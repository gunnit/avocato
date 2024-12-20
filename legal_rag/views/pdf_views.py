import os
import json
import base64
import fitz  # PyMuPDF
import tempfile
import io
import requests
from requests.exceptions import Timeout, RequestException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import openparse

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
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        extracted_text = ""
        structured_content = []
        chunks = []
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
            
            if not is_image_pdf:
                # Process as text PDF using openparse
                try:
                    parser = openparse.DocumentParser()
                    parsed_content = parser.parse(temp_file_path)
                    current_section = None
                    
                    # Extract structured content and text with chunking information
                    for node in parsed_content.nodes:
                        node_dict = node.dict()
                        node_metadata = {
                            'type': node_dict.get('type'),
                            'bbox': node_dict.get('bbox', {}),  # Bounding box information
                            'page_num': node_dict.get('page_num', 1),
                            'confidence': node_dict.get('confidence', 1.0)
                        }
                        
                        # Handle different node types
                        if node_dict.get('type') == 'heading':
                            current_section = {
                                'type': 'section',
                                'heading': node_dict.get('text'),
                                'content': [],
                                'metadata': node_metadata
                            }
                            structured_content.append(current_section)
                            extracted_text += f"\n## {node_dict.get('text')}\n"
                            
                            # Add as a chunk
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
                            
                            # Add as a chunk
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
                                
                                # Add as a chunk
                                chunks.append({
                                    'text': text,
                                    'type': 'text',
                                    'metadata': node_metadata
                                })
                
                except Exception as e:
                    print(f"Openparse processing failed: {str(e)}")
                    # If openparse fails, fall back to image processing
                    is_image_pdf = True
            
            if is_image_pdf:
                # Process as image PDF using GPT-4 Vision
                pdf_document = fitz.open(temp_file_path)
                
                for page_num in range(pdf_document.page_count):
                    page = pdf_document[page_num]
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
                                        "text": "Please extract and return all the text from this image. Return only the extracted text, no additional commentary."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 1000
                    }
                    
                    try:
                        # Add timeout parameter and retry mechanism
                        for attempt in range(3):  # Try up to 3 times
                            try:
                                response = requests.post(
                                    "https://api.openai.com/v1/chat/completions",
                                    headers=headers,
                                    json=payload,
                                    timeout=60  # 60 second timeout
                                )
                                response.raise_for_status()
                                break  # If successful, break the retry loop
                            except (Timeout, RequestException) as e:
                                if attempt == 2:  # Last attempt
                                    raise  # Re-raise the exception if all attempts failed
                                print(f"Attempt {attempt + 1} failed: {str(e)}")
                                continue
                        
                        page_text = response.json()['choices'][0]['message']['content']
                        extracted_text += f"[Page {page_num + 1}]\n{page_text}\n\n"
                        
                        # Add as a text node to structured content with page information
                        text_content = {
                            'type': 'text',
                            'text': page_text,
                            'metadata': {
                                'type': 'text',
                                'page_num': page_num + 1,
                                'source': 'gpt4-vision'
                            }
                        }
                        structured_content.append(text_content)
                        
                        # Add as a chunk
                        chunks.append({
                            'text': page_text,
                            'type': 'text',
                            'metadata': {
                                'page_num': page_num + 1,
                                'source': 'gpt4-vision'
                            }
                        })
                    
                    except (Timeout, RequestException) as e:
                        print(f"Error processing page {page_num + 1}: {str(e)}")
                        return JsonResponse({
                            'error': f'Timeout durante l\'elaborazione della pagina {page_num + 1}. Riprova con un file più piccolo o contatta il supporto.'
                        }, status=504)
                
                pdf_document.close()

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

        return JsonResponse({
            'text': extracted_text,
            'structured_content': structured_content,
            'chunks': chunks,
            'processing_type': 'image' if is_image_pdf else 'text'
        })

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'elaborazione del PDF'
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
def analyze_extracted_text(request):
    """Analyze extracted text using OpenAI"""
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

        # Sort pages by number
        page_numbers = sorted(pages_content.keys())
        
        # Prepare the combined analysis string
        combined_analysis = []
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }

        # Analyze each page
        for page_num in page_numbers:
            page_chunks = pages_content[page_num]
            # Prepare page content
            page_text = ""
            for chunk in page_chunks:
                if chunk.get('type') == 'heading':
                    page_text += f"\n## {chunk.get('text')}\n"
                elif chunk.get('type') == 'table':
                    page_text += f"\n{chunk.get('text')}\n"
                else:
                    page_text += f"{chunk.get('text', '')}\n"

            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": """Sei un assistente legale esperto. Analizza il seguente testo e fornisci:
1. Un riassunto conciso dei punti principali
2. Evidenziazione delle parti importanti con spiegazione del loro significato
3. Identificazione di:
   - Questioni legali chiave
   - Date e scadenze rilevanti
   - Parti coinvolte
   - Richieste o decisioni specifiche
4. Eventuali raccomandazioni o punti di attenzione

Formatta la risposta in modo strutturato usando markdown, con sezioni chiare per ogni categoria."""
                    },
                    {
                        "role": "user",
                        "content": f"[PAGINA {page_num}]\n\n{page_text}"
                    }
                ],
                "max_tokens": 2000
            }
            
            try:
                # Add timeout parameter and retry mechanism
                for attempt in range(3):  # Try up to 3 times
                    try:
                        response = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=60  # 60 second timeout
                        )
                        response.raise_for_status()
                        break  # If successful, break the retry loop
                    except (Timeout, RequestException) as e:
                        if attempt == 2:  # Last attempt
                            raise  # Re-raise the exception if all attempts failed
                        print(f"Attempt {attempt + 1} failed: {str(e)}")
                        continue
                
                page_analysis = response.json()['choices'][0]['message']['content']
                combined_analysis.append(f"\n# Analisi Pagina {page_num}\n\n{page_analysis}\n")
                
            except (Timeout, RequestException) as e:
                print(f"Error analyzing page {page_num}: {str(e)}")
                return JsonResponse({
                    'error': f'Timeout durante l\'analisi della pagina {page_num}. Riprova più tardi o contatta il supporto.'
                }, status=504)

        # Join all analyses into a single string
        final_analysis = "\n".join(combined_analysis)
            
        return JsonResponse({
            'analysis': final_analysis
        })
            
    except Exception as e:
        print(f"Error analyzing text: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'analisi del testo'
        }, status=500)
