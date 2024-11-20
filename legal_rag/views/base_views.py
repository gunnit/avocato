from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import requests
import os

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class RagAssistantView(TemplateView):
    """View for rendering the RAG assistant interface"""
    template_name = 'legal_rag/index.html'

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ImagePdfAssistantView(TemplateView):
    """View for rendering the Image PDF assistant interface"""
    template_name = 'legal_rag/image_pdf.html'

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CassazioneSearchView(TemplateView):
    """View for rendering the Cassazione search interface"""
    template_name = 'legal_rag/cassazione_search.html'

@login_required
@require_http_methods(["POST"])
def cassazione_search_api(request):
    """API endpoint for searching Corte di Cassazione using Serper"""
    try:
        data = json.loads(request.body)
        query = data.get('query')
        
        if not query:
            return JsonResponse({'error': 'Query parameter is required'}, status=400)

        # Construct the search URL for Corte di Cassazione
        site_query = f"site:cortedicassazione.it {query}"

        # Make request to Serper API
        headers = {
            'X-API-KEY': os.environ.get('SERPER_API_KEY'),
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': site_query,
            'gl': 'it',  # Set region to Italy
            'hl': 'it'   # Set language to Italian
        }

        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch search results'}, status=500)

        search_results = response.json()
        
        # Process and format the results
        formatted_results = []
        if 'organic' in search_results:
            for result in search_results['organic']:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })

        return JsonResponse({'results': formatted_results})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
