from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

@method_decorator(ensure_csrf_cookie, name='dispatch')
class RagAssistantView(TemplateView):
    """View for rendering the RAG assistant interface"""
    template_name = 'legal_rag/index.html'

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ImagePdfAssistantView(TemplateView):
    """View for rendering the Image PDF assistant interface"""
    template_name = 'legal_rag/image_pdf.html'
