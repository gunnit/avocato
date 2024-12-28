import asyncio
import aiohttp
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
    'normattiva': {
        'name': 'Normattiva',
        'base_url': 'https://www.normattiva.it/ricerca/ricerca-semplice',
        'search_params': {}
    },
    'giurisprudenza': {
        'name': 'Giurisprudenza Penale',
        'base_url': 'https://www.giurisprudenzapenale.com/',
        'search_params': {}
    },
    'penale': {
        'name': 'Penale.it',
        'base_url': 'https://www.penale.it/blog',
        'search_params': {}
    },
    'giustizia': {
        'name': 'Giustizia.it',
        'base_url': 'https://www.giustizia.it/giustizia/it/mg_14_7.page',
        'search_params': {}
    },
    'milano': {
        'name': 'Giustizia Milano',
        'base_url': 'https://www.tribunale.milano.it/it/Content/Index/28',
        'search_params': {}
    },
    'osservatorio': {
        'name': 'Osservatorio Penale',
        'base_url': 'https://www.osservatoriopenale.it',
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
        
        # Special handling for Penale.it
        if source_id == 'penale':
            params = {
                's': query,
                'post_type': 'post'
            }
            search_url = f"{source_config['base_url']}/?{urlencode(params)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            async with session.get(search_url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Error searching {source_id}: {response.status}")
                    return []
                html = await response.text()
                return parse_results(source_id, html)

        # Special handling for Giustizia.it
        elif source_id == 'giustizia':
            # First visit the homepage to get cookies
            homepage_url = 'https://www.giustizia.it/giustizia/it/homepage.page'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Cache-Control': 'max-age=0'
            }
            
            # Visit homepage first
            async with session.get(homepage_url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Error accessing homepage for {source_id}: {response.status}")
                    return []
                    
                # Get cookies from response
                cookies = response.cookies
                
                # Add delay between requests
                await asyncio.sleep(2)
                
                # Update headers for search request
                headers.update({
                    'Referer': homepage_url,
                    'Origin': 'https://www.giustizia.it',
                    'Cookie': '; '.join([f'{k}={v.value}' for k, v in cookies.items()])
                })
                
                # Construct search URL
                params = {
                    'search': query,
                    'pageCode': 'homepage',
                    'contentId': '',
                    'cod_parent': ''
                }
                search_url = f"{source_config['base_url']}?{urlencode(params)}"
            
            async with session.get(search_url, headers=headers, allow_redirects=True) as response:
                if response.status == 503:
                    logger.error(f"Service unavailable for {source_id}, possibly rate limited")
                    return []
                elif response.status != 200:
                    logger.error(f"Error searching {source_id}: {response.status}")
                    return []
                    
                html = await response.text()
                return parse_results(source_id, html)

        # Special handling for Osservatorio Penale
        elif source_id == 'osservatorio':
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cookie': 'cookieConsent=true'
            }
            
            # Construct search URL
            params = {
                's': query,
                'post_type': 'post'
            }
            search_url = f"{source_config['base_url']}/?{urlencode(params)}"
            
            async with session.get(search_url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Error searching {source_id}: {response.status}")
                    return []
                html = await response.text()
                return parse_results(source_id, html)

        # Special handling for Giustizia Milano
        elif source_id == 'milano':
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            data = {
                'q': query,
                'filter': 'all',
                'page': '1'
            }
            async with session.post(source_config['base_url'], headers=headers, data=data, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Error searching {source_id}: {response.status}")
                    return []
                html = await response.text()
                return parse_results(source_id, html)

        # Add query parameter based on source
        if source_id == 'eurlex':
            params.update({
                'text': query,
                'textScope0': 'ti-te',
                'andText0': query
            })
        elif source_id == 'giurisprudenza':
            params['s'] = query
        
        # For all other sources, use GET request
        url = source_config['base_url']
        if params:
            url += '?' + urlencode(params)

        async with session.get(url, allow_redirects=True) as response:
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
                    
        elif source_id == 'normattiva':
            for item in soup.select('.search-results .result-item'):
                title = item.select_one('.result-title')
                link = item.select_one('.result-title a')
                snippet = item.select_one('.result-description')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': 'https://www.normattiva.it' + link['href'] if not link['href'].startswith('http') else link['href'],
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
                    
        elif source_id == 'penale':
            for item in soup.select('article.post'):
                title = item.select_one('h2.entry-title')
                link = item.select_one('h2.entry-title a')
                snippet = item.select_one('.entry-content')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': link['href'],
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
                    
        elif source_id == 'giustizia':
            # First check if we have any results
            results_count = soup.select_one('.risultati-ricerca')
            if not results_count:
                return []
                
            for item in soup.select('.mg-search-results .mg-search-item'):
                title = item.select_one('.mg-search-title')
                link = item.select_one('.mg-search-title a')
                snippet = item.select_one('.mg-search-description')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': 'https://www.giustizia.it' + link['href'] if not link['href'].startswith('http') else link['href'],
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
                    
        elif source_id == 'milano':
            for item in soup.select('.risultati .risultato'):
                title = item.select_one('.titolo')
                link = item.select_one('a')
                snippet = item.select_one('.descrizione')
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'link': 'https://www.tribunale.milano.it' + link['href'] if not link['href'].startswith('http') else link['href'],
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
                    
        elif source_id == 'osservatorio':
            # First check if we have any results
            no_results = soup.select_one('.alert-info')
            if no_results and 'non sei stato felice' in no_results.get_text():
                return []
                
            for item in soup.select('article.post'):
                title = item.select_one('h3.entry-title')
                link = item.select_one('h3.entry-title a')
                snippet = item.select_one('.td-post-content')
                
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
            
        # Perform concurrent searches
        async with aiohttp.ClientSession() as session:
            tasks = [
                search_source(session, source_id, query)
                for source_id in selected_sources
            ]
            results = await asyncio.gather(*tasks)
            
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
