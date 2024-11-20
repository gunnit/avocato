import os
import json
import base64
import fitz  # PyMuPDF
import tempfile
import io
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings

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
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(temp_file_path)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Try to extract text normally first
                page_text = page.get_text()
                
                # If no text is extracted or text is very short, treat as image-based page
                if not page_text or len(page_text.strip()) < 50:
                    # Convert page to image
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Encode image to base64
                    base64_image = base64.b64encode(img_data).decode('utf-8')
                    
                    # Use OpenAI Vision API to extract text from image
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
                    
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    page_text = response.json()['choices'][0]['message']['content']
                
                extracted_text += page_text + "\n\n"
            
            pdf_document.close()

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

        return JsonResponse({
            'text': extracted_text
        })

    except Exception as e:
        print(f"Error processing image PDF: {str(e)}")
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
        
        if not text:
            return JsonResponse({
                'error': 'Nessun testo fornito per l\'analisi'
            }, status=400)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sei un assistente legale esperto. Analizza il seguente testo e fornisci un riassunto dettagliato evidenziando i punti chiave, le questioni legali principali e eventuali raccomandazioni."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "max_tokens": 2000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        analysis = response.json()['choices'][0]['message']['content']
        
        return JsonResponse({
            'analysis': analysis
        })

    except Exception as e:
        print(f"Error analyzing text: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'analisi del testo'
        }, status=500)
