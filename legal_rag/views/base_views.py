from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json
import requests
import os
from serpapi import GoogleSearch
from ..models import PenalCodeBook, PenalCodeTitle, PenalCodeArticle

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
@require_http_methods(["GET"])
def penal_code_books(request):
    """API endpoint for getting all penal code books"""
    try:
        books = PenalCodeBook.objects.all()
        books_data = [{
            'id': book.id,
            'number': book.number,
            'name': book.name,
            'description': book.description
        } for book in books]
        return JsonResponse(books_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def penal_code_titles(request):
    """API endpoint for getting titles, optionally filtered by book"""
    try:
        book_id = request.GET.get('book_id')
        titles = PenalCodeTitle.objects.all()
        
        if book_id:
            titles = titles.filter(book_id=book_id)
        
        titles_data = [{
            'id': title.id,
            'number': title.number,
            'name': title.name,
            'description': title.description,
            'book_id': title.book_id,
            'articles_range': title.articles_range
        } for title in titles]
        return JsonResponse(titles_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def penal_code_articles(request):
    """API endpoint for getting paginated articles with optional filters"""
    try:
        # Get filter parameters
        book_id = request.GET.get('book_id')
        title_id = request.GET.get('title_id')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # Start with all articles
        articles = PenalCodeArticle.objects.select_related('title__book').all()

        # Apply filters
        if book_id:
            articles = articles.filter(title__book_id=book_id)
        if title_id:
            articles = articles.filter(title_id=title_id)

        # Paginate results
        paginator = Paginator(articles, page_size)
        page_obj = paginator.get_page(page)

        # Format response
        articles_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'results': [{
                'id': article.id,
                'number': article.number,
                'heading': article.heading,
                'book_name': f"Libro {article.title.book.number} - {article.title.book.name}",
                'title_name': f"Titolo {article.title.number} - {article.title.name}",
                'section_name': f"Sezione {article.section.number} - {article.section.name}" if article.section else None
            } for article in page_obj]
        }
        return JsonResponse(articles_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def penal_code_article_detail(request, article_id):
    """API endpoint for getting article details"""
    try:
        article = PenalCodeArticle.objects.select_related(
            'title__book',
            'section'
        ).get(id=article_id)

        article_data = {
            'id': article.id,
            'number': article.number,
            'heading': article.heading,
            'content': article.content,
            'book_name': f"Libro {article.title.book.number} - {article.title.book.name}",
            'title_name': f"Titolo {article.title.number} - {article.title.name}",
            'section_name': f"Sezione {article.section.number} - {article.section.name}" if article.section else None,
            'last_updated': article.last_updated.isoformat()
        }
        return JsonResponse(article_data)
    except PenalCodeArticle.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

        # First search: Get the exact article URL
        params = {
            "engine": "google",
            "q": f"site:testolegge.com/codice-penale/articolo-{article_number}",
            "api_key": os.environ.get('SERPAPI_KEY'),
            "gl": "it",
            "hl": "it",
            "num": 1,
            "start": 0,
            "filter": 0,  # Disable duplicate content filter
            "no_cache": True  # Disable caching to get fresh results
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if 'error' in results:
            return JsonResponse({'error': results['error']}, status=500)

        if 'organic_results' not in results or not results['organic_results']:
            return JsonResponse({'error': 'Article not found'}, status=404)

        # Get the article URL and title
        article_url = results['organic_results'][0].get('link', '')
        article_title = results['organic_results'][0].get('title', '')

        # Second search: Get the full text using multiple specific queries
        full_text_queries = [
            f"\"Articolo {article_number}\" \"Chiunque\" site:testolegge.com/codice-penale/articolo-{article_number}",
            f"\"Art. {article_number}\" intext:\"Chiunque\" site:testolegge.com/codice-penale",
            f"\"Articolo {article_number}\" intext:\"pena\" site:testolegge.com/codice-penale"
        ]

        all_snippets = []
        for query in full_text_queries:
            params = {
                "engine": "google",
                "q": query,
                "api_key": os.environ.get('SERPAPI_KEY'),
                "gl": "it",
                "hl": "it",
                "num": 10,
                "filter": 0,
                "no_cache": True
            }

            search = GoogleSearch(params)
            full_text_results = search.get_dict()

            if 'organic_results' in full_text_results:
                for result in full_text_results['organic_results']:
                    snippet = result.get('snippet', '').strip()
                    if snippet and 'Articolo' in snippet and str(article_number) in snippet:
                        # Clean up the snippet
                        snippet = snippet.replace('...', ' ').strip()
                        all_snippets.append(snippet)

        # Combine all unique snippets
        if all_snippets:
            # Sort snippets by length (longest first) and combine them
            all_snippets.sort(key=len, reverse=True)
            full_text = all_snippets[0]  # Use the longest snippet
        else:
            full_text = results['organic_results'][0].get('snippet', '')

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
