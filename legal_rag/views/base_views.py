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
from ..models import PenalCodeBook, PenalCodeTitle, PenalCodeArticle, SavedSearchResult
from cases.models import Caso

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

@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class FederatedSearchView(TemplateView):
    """View for rendering the Federated Search interface"""
    template_name = 'legal_rag/federated_search.html'

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
        book_id = request.GET.get('book')
        search = request.GET.get('search')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # Start with all articles
        articles = PenalCodeArticle.objects.select_related('title__book').all()

        # Apply filters
        if book_id:
            articles = articles.filter(title__book_id=book_id)
        if search:
            articles = articles.filter(number__icontains=search)

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
def save_search_result(request):
    """API endpoint for saving search results to a specific case"""
    try:
        data = json.loads(request.body)
        caso_id = data.get('caso_id')
        search_title = data.get('search_title')
        search_link = data.get('search_link')
        search_snippet = data.get('search_snippet')

        if not all([caso_id, search_title, search_link, search_snippet]):
            return JsonResponse({'error': 'All fields are required'}, status=400)

        caso = Caso.objects.get(id=caso_id)
        SavedSearchResult.objects.create(
            caso=caso,
            search_title=search_title,
            search_link=search_link,
            search_snippet=search_snippet
        )

        return JsonResponse({'success': 'Search result saved successfully'})

    except Caso.DoesNotExist:
        return JsonResponse({'error': 'Case not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
