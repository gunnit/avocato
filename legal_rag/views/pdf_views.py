import os
import json
import base64
import fitz  # PyMuPDF
import tempfile
import io
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from requests.exceptions import Timeout, RequestException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import openparse
import logging
from .prompts import PDF_TEXT_EXTRACTION_PROMPT, LEGAL_ANALYSIS_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFPage(BaseModel):
    """Model for storing page content and metadata"""
    page_num: int
    text: str
    metadata: Dict = Field(default_factory=dict)
    confidence: float = 1.0
    source: str = "text"  # 'text' or 'vision'

class PDFProcessingResult(BaseModel):
    """Model for storing PDF processing results"""
    text: str
    structured_content: List[Dict]
    chunks: List[Dict]
    processing_type: str
    trace_id: str = Field(default_factory=lambda: f"trace_{time.time()}")

def process_page_with_vision(page_data: tuple) -> Optional[PDFPage]:
    """Process a single page with GPT-4 Vision"""
    page, page_num = page_data
    try:
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        base64_image = base64.b64encode(img_data).decode('utf-8')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
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
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'error' in response_data:
                    logger.error(f"OpenAI API error: {response_data['error']}")
                    raise RequestException(f"OpenAI API error: {response_data['error']}")
                    
                page_text = response_data['choices'][0]['message']['content']
                if not page_text.strip():
                    logger.warning(f"Empty text extracted from page {page_num + 1}")
                    return None
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
        logger.error(f"Error processing page {page_num + 1}: {str(e)}")
        return None

def process_text_pdf(pdf_path: str) -> Optional[PDFProcessingResult]:
    """Process a text-based PDF using openparse"""
    try:
        parser = openparse.DocumentParser()
        parsed_content = parser.parse(pdf_path)
        
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
        
        return PDFProcessingResult(
            text=extracted_text,
            structured_content=structured_content,
            chunks=chunks,
            processing_type='text'
        )
        
    except Exception as e:
        logger.error(f"Error processing text PDF: {str(e)}")
        return None

def process_image_pdf_with_vision(pdf_path: str) -> Optional[PDFProcessingResult]:
    """Process an image-based PDF using GPT-4 Vision with parallel processing"""
    try:
        pdf_document = fitz.open(pdf_path)
        pages = [(pdf_document[i], i) for i in range(pdf_document.page_count)]
        
        # Process pages in parallel with smaller batch size
        extracted_text = ""
        structured_content = []
        chunks = []
        
        # Process in smaller batches to avoid rate limits
        batch_size = 1  # Process one page at a time to avoid rate limits
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                processed_pages = list(executor.map(process_page_with_vision, batch))
                
                # Process successful pages from this batch
                successful_pages = [page for page in processed_pages if page is not None]
                successful_pages.sort(key=lambda x: x.page_num)
                
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
            
        return PDFProcessingResult(
            text=extracted_text,
            structured_content=structured_content,
            chunks=chunks,
            processing_type='image'
        )
        
    except Exception as e:
        logger.error(f"Error processing image PDF: {str(e)}")
        return None

@csrf_protect
@require_http_methods(["POST"])
def process_image_pdf(request):
    """Handle image PDF processing requests"""
    try:
        if 'pdf' not in request.FILES:
            return JsonResponse({
                'error': 'È necessario caricare un file PDF'
            }, status=400)

        pdf_file = request.FILES['pdf']
        logger.info(f"Processing PDF file: {pdf_file.name}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # First try to extract text using PyMuPDF to check if it's an image PDF
            pdf_document = fitz.open(temp_file_path)
            is_image_pdf = True
            
            # Check first few pages for text content
            for page_num in range(min(3, pdf_document.page_count)):
                page = pdf_document[page_num]
                text = page.get_text().strip()
                if len(text) > 50:  # If we find substantial text, it's not an image PDF
                    is_image_pdf = False
                    break
            
            pdf_document.close()
            
            # Process based on PDF type
            if is_image_pdf:
                result = process_image_pdf_with_vision(temp_file_path)
            else:
                result = process_text_pdf(temp_file_path)
                
            if result is None:
                return JsonResponse({
                    'error': 'Si è verificato un errore durante l\'elaborazione del PDF. Nessuna pagina è stata elaborata con successo.'
                }, status=500)
                
            # Ensure we have some content before returning
            if not result.chunks:
                return JsonResponse({
                    'error': 'Nessun contenuto è stato estratto dal PDF.'
                }, status=400)
                
            return JsonResponse(result.dict())

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except PermissionError:
                # If file is still in use, try again after a short delay
                time.sleep(0.1)
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to delete temporary file: {str(e)}")

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'elaborazione del PDF'
        }, status=500)

class PageAnalysis(BaseModel):
    """Model for storing page analysis results"""
    page_num: int
    analysis: str
    metadata: Dict = Field(default_factory=dict)

def analyze_page_content(page_data: tuple) -> Optional[PageAnalysis]:
    """Analyze a single page's content using GPT-4"""
    page_num, page_text = page_data
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": LEGAL_ANALYSIS_PROMPT
                },
                {
                    "role": "user",
                    "content": f"[PAGINA {page_num}]\n\n{page_text}"
                }
            ],
            "max_tokens": 2000
        }
        
        # Process with retry mechanism
        for attempt in range(3):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'error' in response_data:
                    logger.error(f"OpenAI API error: {response_data['error']}")
                    raise RequestException(f"OpenAI API error: {response_data['error']}")
                    
                analysis = response_data['choices'][0]['message']['content']
                if not analysis.strip():
                    logger.warning(f"Empty analysis for page {page_num}")
                    return None
                return PageAnalysis(
                    page_num=page_num,
                    analysis=analysis,
                    metadata={'page_num': page_num}
                )
                
            except (Timeout, RequestException) as e:
                if attempt == 2:
                    logger.error(f"Failed to analyze page {page_num} after 3 attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed for page {page_num}: {str(e)}")
                time.sleep(1)  # Wait before retry
                
    except Exception as e:
        logger.error(f"Error analyzing page {page_num}: {str(e)}")
        return None

@csrf_protect
@require_http_methods(["POST"])
def analyze_extracted_text(request):
    """Analyze extracted text using OpenAI with parallel processing"""
    try:
        data = json.loads(request.body)
        text = data.get('text')
        structured_content = data.get('structured_content', [])
        chunks = data.get('chunks', [])
        
        if not text and not structured_content and not chunks:
            return JsonResponse({
                'error': 'Nessun testo fornito per l\'analisi'
            }, status=400)

        # Organize content by pages
        pages_content = {}
        if chunks:
            for chunk in chunks:
                page_num = chunk.get('metadata', {}).get('page_num', 1)
                if page_num not in pages_content:
                    pages_content[page_num] = []
                pages_content[page_num].append(chunk)
        else:
            # If no chunks, treat all content as page 1
            pages_content[1] = [{'text': text, 'type': 'text'}]

        # Prepare pages for parallel processing
        pages_to_analyze = []
        for page_num in sorted(pages_content.keys()):
            page_chunks = pages_content[page_num]
            page_text = ""
            for chunk in page_chunks:
                if chunk.get('type') == 'heading':
                    page_text += f"\n## {chunk.get('text')}\n"
                elif chunk.get('type') == 'table':
                    page_text += f"\n{chunk.get('text')}\n"
                else:
                    page_text += f"{chunk.get('text', '')}\n"
            pages_to_analyze.append((page_num, page_text))
        
        # Process pages sequentially to avoid rate limits
        analyzed_pages = []
        for page_data in pages_to_analyze:
            result = analyze_page_content(page_data)
            if result:
                analyzed_pages.append(result)
            # Add delay between pages
            if page_data != pages_to_analyze[-1]:  # Don't delay after last page
                time.sleep(3)  # 3 second delay between analyses
        
        # Filter out failed pages and sort by page number
        successful_pages = [page for page in analyzed_pages if page is not None]
        successful_pages.sort(key=lambda x: x.page_num)
        
        # Combine analyses
        combined_analysis = []
        for page in successful_pages:
            combined_analysis.append(f"\n# Analisi Pagina {page.page_num}\n\n{page.analysis}\n")
        
        final_analysis = "\n".join(combined_analysis)
        
        # Return empty analysis if no pages were processed
        if not successful_pages:
            return JsonResponse({
                'analysis': 'Nessuna pagina è stata analizzata con successo.',
                'pages_analyzed': 0,
                'total_pages': len(pages_to_analyze)
            })

        return JsonResponse({
            'analysis': final_analysis,
            'pages_analyzed': len(successful_pages),
            'total_pages': len(pages_to_analyze)
        })
            
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'analisi del testo'
        }, status=500)
