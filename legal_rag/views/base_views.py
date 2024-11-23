from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import requests
import os
from serpapi import GoogleSearch

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

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class PenalCodeSearchView(TemplateView):
    """View for rendering the Penal Code search interface"""
    template_name = 'legal_rag/penal_code_search.html'

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

@login_required
@require_http_methods(["POST"])
def penal_code_search_api(request):
    """API endpoint for searching Penal Code articles using SerpAPI"""
    try:
        data = json.loads(request.body)
        article_number = data.get('article_number')
        
        if not article_number:
            return JsonResponse({'error': 'Article number is required'}, status=400)

        # Search using SerpAPI
        params = {
            "engine": "google",
            "q": f"site:testolegge.com/codice-penale/articolo-{article_number}",
            "api_key": os.environ.get('SERPAPI_KEY'),
            "gl": "it",  # Set region to Italy
            "hl": "it",  # Set language to Italian
            "num": 1,    # We only need the first result
            "start": 0
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if 'error' in results:
            return JsonResponse({'error': results['error']}, status=500)

        if 'organic_results' not in results or not results['organic_results']:
            return JsonResponse({'error': 'Article not found'}, status=404)

        # Get the article URL
        article_url = results['organic_results'][0].get('link', '')
        article_title = results['organic_results'][0].get('title', '')

        # Now search for the full text
        params = {
            "engine": "google",
            "q": f"\"{article_number}\" \"Articolo {article_number}\" \"Chiunque\" site:testolegge.com/codice-penale",
            "api_key": os.environ.get('SERPAPI_KEY'),
            "gl": "it",
            "hl": "it",
            "num": 10
        }

        search = GoogleSearch(params)
        full_text_results = search.get_dict()

        # Get the full text from the search results
        full_text = ""
        if 'organic_results' in full_text_results:
            # Combine snippets from all results
            snippets = []
            for result in full_text_results['organic_results']:
                snippet = result.get('snippet', '').strip()
                if snippet and 'Articolo' in snippet and str(article_number) in snippet:
                    snippets.append(snippet)

            # Use the longest snippet as it's likely to be the most complete
            full_text = max(snippets, key=len) if snippets else results['organic_results'][0].get('snippet', '')

        formatted_results = [{
            'title': article_title,
            'link': article_url,
            'snippet': full_text
        }]

        return JsonResponse({'results': formatted_results})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
