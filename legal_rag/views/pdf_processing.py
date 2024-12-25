import base64
import fitz  # PyMuPDF
import logging
import requests
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from requests.exceptions import Timeout, RequestException
from django.conf import settings
import openparse
from .prompts import PDF_TEXT_EXTRACTION_PROMPT
from ..schemas import PDFPage, PDFProcessingResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_page_with_vision(page_data: tuple) -> Optional[PDFPage]:
    """Process a single page with GPT-4 Vision"""
    page, page_num = page_data
    try:
        logger.info(f"\n{'='*80}\nProcessing page {page_num + 1} with Vision API\n{'='*80}")
        
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        base64_image = base64.b64encode(img_data).decode('utf-8')
        logger.info(f"Successfully converted page {page_num + 1} to base64 image")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        # Log the prompt being sent
        logger.info(f"\nPrompt for page {page_num + 1}:")
        logger.info("-" * 40)
        logger.info(PDF_TEXT_EXTRACTION_PROMPT)
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PDF_TEXT_EXTRACTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }

        # Process page with retry mechanism
        for attempt in range(3):
            try:
                logger.info(f"Attempt {attempt + 1} to process page {page_num + 1}")
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'error' in response_data:
                    logger.error(f"OpenAI API error for page {page_num + 1}: {response_data['error']}")
                    raise RequestException(f"OpenAI API error: {response_data['error']}")
                    
                page_text = response_data['choices'][0]['message']['content']
                if not page_text.strip():
                    logger.warning(f"Empty text extracted from page {page_num + 1}")
                    return None
                
                logger.info(f"\nExtracted text from page {page_num + 1}:")
                logger.info("-" * 40)
                logger.info(page_text[:500] + "..." if len(page_text) > 500 else page_text)
                
                return PDFPage(
                    page_num=page_num + 1,
                    text=page_text,
                    source='vision',
                    metadata={'page_num': page_num + 1}
                )
                
            except (Timeout, RequestException) as e:
                if attempt == 2:
                    logger.error(f"Failed to process page {page_num + 1} after 3 attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed for page {page_num + 1}: {str(e)}")
                time.sleep(1)  # Wait before retry
                
    except Exception as e:
        logger.error(f"Error processing page {page_num + 1}:")
        logger.error(traceback.format_exc())
        return None

def process_text_pdf(pdf_path: str) -> Optional[PDFProcessingResult]:
    """Process a text-based PDF using openparse"""
    try:
        logger.info("\nProcessing text-based PDF")
        logger.info("=" * 80)
        
        parser = openparse.DocumentParser()
        parsed_content = parser.parse(pdf_path)
        logger.info("Successfully parsed PDF with openparse")
        
        extracted_text = ""
        structured_content = []
        chunks = []
        current_section = None
        
        for node in parsed_content.nodes:
            node_dict = node.dict()
            node_metadata = {
                'type': node_dict.get('type'),
                'bbox': node_dict.get('bbox', {}),
                'page_num': node_dict.get('page_num', 1),
                'confidence': node_dict.get('confidence', 1.0)
            }
            
            if node_dict.get('type') == 'heading':
                current_section = {
                    'type': 'section',
                    'heading': node_dict.get('text'),
                    'content': [],
                    'metadata': node_metadata
                }
                structured_content.append(current_section)
                extracted_text += f"\n## {node_dict.get('text')}\n"
                chunks.append({
                    'text': node_dict.get('text'),
                    'type': 'heading',
                    'metadata': node_metadata
                })
            elif node_dict.get('type') == 'table':
                table_content = {
                    'type': 'table',
                    'markdown': node_dict.get('markdown'),
                    'cells': node_dict.get('cells', []),
                    'metadata': node_metadata
                }
                if current_section:
                    current_section['content'].append(table_content)
                else:
                    structured_content.append(table_content)
                extracted_text += f"\n{node_dict.get('markdown')}\n"
                chunks.append({
                    'text': node_dict.get('markdown'),
                    'type': 'table',
                    'metadata': node_metadata
                })
            else:
                text = node_dict.get('text', '')
                if text:
                    text_content = {
                        'type': 'text',
                        'text': text,
                        'metadata': node_metadata
                    }
                    if current_section:
                        current_section['content'].append(text_content)
                    else:
                        structured_content.append(text_content)
                    extracted_text += f"{text}\n"
                    chunks.append({
                        'text': text,
                        'type': 'text',
                        'metadata': node_metadata
                    })
        
        logger.info(f"\nExtracted {len(chunks)} chunks from PDF")
        logger.info(f"Preview of extracted text:")
        logger.info("-" * 40)
        logger.info(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
        
        return PDFProcessingResult(
            text=extracted_text,
            structured_content=structured_content,
            chunks=chunks,
            processing_type='text'
        )
        
    except Exception as e:
        logger.error("Error processing text PDF:")
        logger.error(traceback.format_exc())
        return None

def process_image_pdf_with_vision(pdf_path: str) -> Optional[PDFProcessingResult]:
    """Process an image-based PDF using GPT-4 Vision with parallel processing"""
    try:
        logger.info("\nProcessing image-based PDF with Vision API")
        logger.info("=" * 80)
        
        pdf_document = fitz.open(pdf_path)
        pages = [(pdf_document[i], i) for i in range(pdf_document.page_count)]
        logger.info(f"PDF has {len(pages)} pages")
        
        # Process pages in parallel with smaller batch size
        extracted_text = ""
        structured_content = []
        chunks = []
        
        # Process in smaller batches to avoid rate limits
        batch_size = 1  # Process one page at a time to avoid rate limits
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            logger.info(f"\nProcessing batch of pages {i+1} to {min(i+batch_size, len(pages))}")
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                processed_pages = list(executor.map(process_page_with_vision, batch))
                
                # Process successful pages from this batch
                successful_pages = [page for page in processed_pages if page is not None]
                successful_pages.sort(key=lambda x: x.page_num)
                
                logger.info(f"Successfully processed {len(successful_pages)} pages in this batch")
                
                for page in successful_pages:
                    extracted_text += f"[Page {page.page_num}]\n{page.text}\n\n"
                    
                    # Create content and chunk entries
                    content = {
                        'type': 'text',
                        'text': page.text,
                        'metadata': {
                            'type': 'text',
                            'page_num': page.page_num,
                            'source': page.source
                        }
                    }
                    structured_content.append(content)
                    chunks.append({
                        'text': page.text,
                        'type': 'text',
                        'metadata': {
                            'page_num': page.page_num,
                            'source': page.source
                        }
                    })
            
            # Add longer delay between batches to avoid rate limits
            if i + batch_size < len(pages):
                logger.info("Waiting 5 seconds before processing next batch...")
                time.sleep(5)  # 5 second delay between pages
        
        pdf_document.close()
        
        if not chunks:
            logger.warning("No pages were successfully processed")
            return PDFProcessingResult(
                text="",
                structured_content=[],
                chunks=[],
                processing_type='image'
            )
        
        logger.info(f"\nFinished processing PDF")
        logger.info(f"Successfully processed {len(chunks)} chunks")
        logger.info(f"Preview of extracted text:")
        logger.info("-" * 40)
        logger.info(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
            
        return PDFProcessingResult(
            text=extracted_text,
            structured_content=structured_content,
            chunks=chunks,
            processing_type='image'
        )
        
    except Exception as e:
        logger.error("Error processing image PDF:")
        logger.error(traceback.format_exc())
        return None
