import os
import json
import tempfile
import time
import logging
from datetime import datetime
import fitz  # PyMuPDF
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from .pdf_processing import process_text_pdf, process_image_pdf_with_vision
from .pdf_analysis import analyze_page_content, merge_page_analyses
from ..models import PDFAnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # Create PDFAnalysisResult instance first
            analysis_result = PDFAnalysisResult.objects.create(
                filename=pdf_file.name,
                pdf_file=pdf_file,
                caso_id=request.POST.get('caso_id')  # Optional caso_id
            )

            # Process based on PDF type
            if is_image_pdf:
                result = process_image_pdf_with_vision(temp_file_path)
            else:
                result = process_text_pdf(temp_file_path)
                
            if result is None:
                analysis_result.delete()  # Clean up if processing failed
                return JsonResponse({
                    'error': 'Si è verificato un errore durante l\'elaborazione del PDF. Nessuna pagina è stata elaborata con successo.'
                }, status=500)
                
            # Ensure we have some content before returning
            if not result.chunks:
                analysis_result.delete()  # Clean up if no content extracted
                return JsonResponse({
                    'error': 'Nessun contenuto è stato estratto dal PDF.'
                }, status=400)
            
            # Update analysis result with processed data
            analysis_result.extracted_text = result.text
            analysis_result.structured_content = result.structured_content
            analysis_result.content_chunks = result.chunks
            analysis_result.processing_type = result.processing_type
            analysis_result.processing_completed = True
            analysis_result.save()
                
            # Ensure datetime objects are serialized in the response
            response_data = result.dict()
            response_data['analysis_id'] = analysis_result.id
            return JsonResponse(response_data, json_dumps_params={'default': str})

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

@csrf_protect
@require_http_methods(["POST"])
def analyze_extracted_text(request):
    """Analyze extracted text using OpenAI with parallel processing and save results"""
    try:
        data = json.loads(request.body)
        text = data.get('text')
        structured_content = data.get('structured_content', [])
        chunks = data.get('chunks', [])
        analysis_id = data.get('analysis_id')
        
        if not analysis_id:
            return JsonResponse({
                'error': 'analysis_id is required'
            }, status=400)
            
        try:
            analysis_result = PDFAnalysisResult.objects.get(id=analysis_id)
        except PDFAnalysisResult.DoesNotExist:
            return JsonResponse({
                'error': 'Analysis result not found'
            }, status=404)
        
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
        
        # Combine analyses into a single DocumentSchema
        if not successful_pages:
            return JsonResponse({
                'error': 'Nessuna pagina è stata analizzata con successo.',
                'pages_analyzed': 0,
                'total_pages': len(pages_to_analyze)
            })

        # Merge all page analyses
        combined_schema = merge_page_analyses(successful_pages)

        # Convert the combined schema to dict for saving with datetime handling
        analysis_dict = combined_schema.dict(exclude_none=True)
        
        # Helper function to serialize datetime objects
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_dates(item) for item in obj]
            return obj
            
        # Ensure all datetime objects are serialized
        analysis_dict = serialize_dates(analysis_dict)
        
        # Update existing PDFAnalysisResult with analysis data
        analysis_result.dati_generali = analysis_dict.get('dati_generali', {})
        analysis_result.informazioni_legali_specifiche = analysis_dict.get('informazioni_legali_specifiche', {})
        analysis_result.dati_processuali = analysis_dict.get('dati_processuali', {})
        analysis_result.analisi_linguistica = analysis_dict.get('analisi_linguistica', {})
        analysis_result.analysis_completed = True
        analysis_result.save()

        # Format analysis for display
        analysis_text = json.dumps(analysis_dict, indent=2, ensure_ascii=False, default=str)

        return JsonResponse({
            'analysis': analysis_text,
            'pages_analyzed': len(successful_pages),
            'total_pages': len(pages_to_analyze),
            'analysis_id': analysis_result.id
        }, json_dumps_params={'default': str})
            
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'analisi del testo'
        }, status=500)
