import asyncio
import aiohttp
import ssl
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from asgiref.sync import async_to_sync
from django.utils.decorators import decorator_from_middleware
import json
import logging

logger = logging.getLogger(__name__)

def async_view(view):
    """Decorator to make async views work with Django"""
    @async_to_sync
    async def _wrapped_view(request, *args, **kwargs):
        return await view(request, *args, **kwargs)
    return _wrapped_view

# Source configurations
SOURCES = {
    'eurlex': {
        'name': 'EUR-Lex',
        'base_url': 'https://eur-lex.europa.eu/search.html',
        'search_params': {
            'scope': 'EURLEX',
            'type': 'quick',
            'lang': 'en',
        }
    },
    'giurisprudenza': {
        'name': 'Giurisprudenza Penale',
        'base_url': 'https://www.giurisprudenzapenale.com/',
        'search_params': {}
    }
}

async def search_source(session, source_id, query):
    """
    Perform search on a specific source
    """
    source_config = SOURCES[source_id]
    try:
        params = source_config['search_params'].copy()
        
        # Add query parameter based on source
        if source_id == 'eurlex':
            params.update({
                'text': query,
                'textScope0': 'ti-te',
                'andText0': query
            })
        elif source_id == 'giurisprudenza':
            params['s'] = query
        
        # Construct URL with parameters
        url = source_config['base_url']
        if params:
            url += '?' + urlencode(params)

        # Common headers for all requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
        }

        async with session.get(url, headers=headers, allow_redirects=True) as response:
            if response.status != 200:
                logger.error(f"Error searching {source_id}: {response.status}")
                return []
                
            html = await response.text()
            return parse_results(source_id, html)
            
    except Exception as e:
        logger.error(f"Error searching {source_id}: {str(e)}")
        return []

def parse_results(source_id, html):
    """
    Parse HTML response based on source format
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    try:
        if source_id == 'eurlex':
            for item in soup.select('.SearchResult'):
                title = item.select_one('.title')
                link = item.select_one('a')
                snippet = item.select_one('.SearchResult__content')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': 'https://eur-lex.europa.eu' + link['href'],
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
                    
        elif source_id == 'giurisprudenza':
            for item in soup.select('article'):
                title = item.select_one('h2')
                link = item.select_one('a')
                snippet = item.select_one('.entry-content')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': link['href'],
                        'snippet': snippet.get_text(strip=True)[:200] + '...' if snippet else ''
                    })
    
    except Exception as e:
        logger.error(f"Error parsing results for {source_id}: {str(e)}")
        
    return results[:10]  # Limit to top 10 results per source

@require_http_methods(["POST"])
@async_view
async def federated_search(request):
    """
    Handle federated search requests
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        selected_sources = data.get('sources', [])
        
        if not query:
            return JsonResponse({'error': 'Query is required'})
            
        if not selected_sources:
            return JsonResponse({'error': 'At least one source must be selected'})
            
        # Validate sources
        selected_sources = [s for s in selected_sources if s in SOURCES]
        if not selected_sources:
            return JsonResponse({'error': 'No valid sources selected'})
            
        # Configure client session with TCP connector settings
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            limit=10,  # Limit concurrent connections
            enable_cleanup_closed=True,  # Clean up closed connections
            force_close=True,  # Force close connections after use
            ssl=ssl_context  # Use custom SSL context
        )
        
        timeout = aiohttp.ClientTimeout(
            total=60,  # Total timeout for the entire operation
            connect=30,  # Timeout for connecting
            sock_read=30  # Timeout for reading from socket
        )
        
        # Create session with configured settings
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True  # Trust environment for proxy settings
        ) as session:
            try:
                tasks = [
                    search_source(session, source_id, query)
                    for source_id in selected_sources
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and handle any exceptions
                processed_results = []
                for source_id, result in zip(selected_sources, results):
                    if isinstance(result, Exception):
                        logger.error(f"Error searching {source_id}: {str(result)}")
                        processed_results.append([])  # Empty results for failed source
                    else:
                        processed_results.append(result)
                results = processed_results
                
            except Exception as e:
                logger.error(f"Error during concurrent searches: {str(e)}")
                return JsonResponse({'error': 'Search operation failed'}, status=500)
            
        # Combine results
        combined_results = {
            SOURCES[source_id]['name']: source_results
            for source_id, source_results in zip(selected_sources, results)
            if source_results  # Only include sources with results
        }
        
        return JsonResponse({
            'results': combined_results
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in federated search: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
