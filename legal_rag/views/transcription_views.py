from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from openai import OpenAI
import logging
import traceback

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class TranscriptionView(TemplateView):
    """View for rendering the transcription interface"""
    template_name = 'legal_rag/transcription/index.html'

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def transcribe_media(request):
    """
    Handle audio/video file upload and transcription using OpenAI's Whisper API.
    Accepts: POST request with file in request.FILES['file']
    Returns: JSON response with transcription or error message
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'error': 'No file provided'
            }, status=400)

        media_file = request.FILES['file']
        
        # Check file extension
        allowed_extensions = ['flac', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'ogg', 'wav', 'webm']
        file_extension = media_file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': f'Invalid file format. Allowed formats: {", ".join(allowed_extensions)}'
            }, status=400)

        # Log API key presence (not the actual key)
        logger.info(f"OpenAI API Key present: {bool(settings.OPENAI_API_KEY)}")

        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Create transcription
        try:
            # Log file details
            logger.info(f"Processing file: {media_file.name}, size: {media_file.size} bytes")
            
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=media_file,
                response_format="json"
            )
            
            return JsonResponse({
                'success': True,
                'text': response.text
            })

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'error': 'Error during transcription',
                'details': str(e)
            }, status=500)

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'error': 'Server error',
            'details': str(e)
        }, status=500)
