from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.core.exceptions import PermissionDenied
from ..models import Caso, DocumentaryEvidence
from legal_rag.models import SavedSearchResult
from legal_rag.models.legal_search import LegalSearchResult
from .ai_utils import analizza_caso
from legal_rag.crews.legal_search_crew import LegalSearchCrew
import json
import anthropic
import os
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, F, ExpressionWrapper, fields
from django.db.models.functions import Now

@login_required
def lista_casi(request):
    casi = Caso.objects.all().order_by('-data_creazione')
    
    # Get current date and first day of current month
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate statistics
    casi_totali = casi.count()
    casi_completati = casi.filter(stato='Completato').count()
    casi_in_corso = casi.filter(stato='In corso').count()
    casi_questo_mese = casi.filter(data_creazione__gte=first_day_of_month).count()
    
    # Calculate percentage of cases in progress
    casi_in_corso_percentage = (casi_in_corso / casi_totali * 100) if casi_totali > 0 else 0
    
    # Calculate average resolution time for completed cases
    completed_cases = casi.filter(stato='Completato')
    if completed_cases.exists():
        # Create a duration expression
        duration_expr = ExpressionWrapper(
            Now() - F('data_creazione'),
            output_field=fields.DurationField()
        )
        avg_duration = completed_cases.annotate(
            duration=duration_expr
        ).aggregate(avg_duration=Avg('duration'))['avg_duration']
        
        # Convert to days
        tempo_medio_risoluzione = avg_duration.days if avg_duration else 0
    else:
        tempo_medio_risoluzione = 0

    context = {
        'casi': casi,
        'casi_completati': casi_completati,
        'casi_questo_mese': casi_questo_mese,
        'tempo_medio_risoluzione': tempo_medio_risoluzione,
        'casi_in_corso': round(casi_in_corso_percentage)  # Rounded percentage for progress bar
    }
    
    return render(request, 'cases/lista_casi.html', context)

@login_required
def nuovo_caso(request):
    if request.method == 'POST':
        titolo = request.POST.get('titolo')
        descrizione = request.POST.get('descrizione')
        
        caso = Caso.objects.create(
            titolo=titolo,
            descrizione=descrizione,
            stato='Nuovo'
        )
        
        try:
            analisi = analizza_caso(caso.id)
            caso.analisi_ai = analisi
            caso.save()
            messages.success(request, 'Caso creato e analizzato con successo.')
        except Exception as e:
            messages.error(request, f'Caso creato ma si è verificato un errore durante l\'analisi: {str(e)}')
        
        return redirect('dettaglio_caso', caso_id=caso.id)
    
    return render(request, 'cases/nuovo_caso.html')

@login_required
def edit_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    
    if request.method == 'POST':
        titolo = request.POST.get('titolo')
        descrizione = request.POST.get('descrizione')
        stato = request.POST.get('stato')
        
        caso.titolo = titolo
        caso.descrizione = descrizione
        caso.stato = stato
        caso.save()
        
        messages.success(request, 'Caso aggiornato con successo.')
        return redirect('dettaglio_caso', caso_id=caso.id)
    
    return render(request, 'cases/edit_caso.html', {'caso': caso})

@login_required
@require_GET
def get_cases_api(request):
    """API endpoint to get a list of cases for dropdowns"""
    cases = Caso.objects.all().order_by('-data_creazione').values('id', 'titolo')
    return JsonResponse(list(cases), safe=False)

@login_required
def delete_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    if request.method == 'POST':
        caso.delete()
        messages.success(request, 'Caso eliminato con successo.')
        return redirect('lista_casi')
    return redirect('dettaglio_caso', caso_id=caso_id)

@login_required
def dettaglio_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    try:
        analisi_json = json.loads(caso.analisi_ai) if caso.analisi_ai else None
    except json.JSONDecodeError:
        analisi_json = None
    return render(request, 'cases/dettaglio_caso.html', {'caso': caso, 'analisi_json': analisi_json})

@login_required
def rigenera_analisi(request, caso_id):
    print(f"[DEBUG] Starting rigenera_analisi for caso_id: {caso_id}")
    caso = get_object_or_404(Caso, id=caso_id)
    print(f"[DEBUG] Found case: {caso.titolo}")
    
    try:
        print("[DEBUG] Calling analizza_caso...")
        analisi = analizza_caso(caso.id)
        print(f"[DEBUG] Got analysis result length: {len(str(analisi))}")
        
        print("[DEBUG] Saving analysis to case...")
        caso.analisi_ai = analisi
        caso.save()
        print("[DEBUG] Analysis saved successfully")
        
        messages.success(request, 'Analisi rigenerata con successo.')
    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        messages.error(request, f'Errore durante la rigenerazione dell\'analisi: {str(e)}')
    
    print("[DEBUG] Redirecting to dettaglio_caso")
    return redirect('dettaglio_caso', caso_id=caso.id)

@require_http_methods(["POST"])
def generate_description(request, caso_id):
    """Generate AI description for a case using all available data."""
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    caso = get_object_or_404(Caso, id=caso_id)
    
    # Get case data and documents
    case_data = {
        'titolo': caso.titolo,
        'stato': caso.stato,
        'data_creazione': caso.data_creazione.strftime('%Y-%m-%d'),
        'documenti': [doc.title for doc in caso.documentary_evidences.all()],
        'analisi': json.loads(caso.analisi_ai) if caso.analisi_ai else None
    }
    
    # Create prompt for case description
    prompt = f"""Sei un avvocato esperto. Genera una descrizione dettagliata e professionale per il seguente caso legale:

Titolo del Caso: {case_data['titolo']}
Data di Apertura: {case_data['data_creazione']}
Stato: {case_data['stato']}
Documenti Disponibili: {', '.join(case_data['documenti'])}

La descrizione deve:
1. Fornire un quadro completo e chiaro del caso
2. Includere una cronologia degli eventi rilevanti
3. Menzionare le parti coinvolte e i loro ruoli
4. Evidenziare gli aspetti legali chiave
5. Citare i documenti pertinenti
6. Mantenere un tono professionale e oggettivo
7. Essere strutturata in modo logico e coerente

Se disponibile, considera anche la seguente analisi del caso:
{json.dumps(case_data['analisi'], indent=2) if case_data['analisi'] else 'Analisi non disponibile'}"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.7,
            system="Sei un avvocato esperto italiano specializzato nella redazione di documenti legali. Rispondi sempre in italiano.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return JsonResponse({'content': message.content[0].text})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def perform_legal_search(request, caso_id):
    """Perform comprehensive legal search based on case details"""
    try:
        caso = get_object_or_404(Caso, id=caso_id)
        
        # Gather all case information
        try:
            ai_analysis = json.loads(caso.analisi_ai) if caso.analisi_ai else {}
        except json.JSONDecodeError:
            ai_analysis = {}
            messages.warning(request, 'Errore nel parsing dell\'analisi AI. Procedendo con analisi vuota.')
        
        case_details = {
            "title": caso.titolo,
            "description": caso.descrizione,
            "ai_analysis": ai_analysis,
            "legal_references": caso.riferimenti_legali,
            "documents": []
        }
        
        # Add extracted text from documents
        for doc in caso.documentary_evidences.all():
            if doc.extracted_text:
                case_details["documents"].append({
                    "title": doc.title,
                    "type": doc.document_type,
                    "content": doc.extracted_text
                })
        
        # Initialize and run the legal search crew
        crew = LegalSearchCrew()
        result = crew.kickoff(case_details)
        
        # Convert result to dictionary
        if hasattr(result, 'json_dict'):
            raw_results = result.json_dict
        elif hasattr(result, 'raw'):
            try:
                raw_results = json.loads(result.raw)
            except json.JSONDecodeError:
                raw_results = {"error": "Failed to parse JSON", "raw_output": result.raw}
        else:
            raw_results = {"error": "Unexpected result format"}

        print(f"Raw results from crew: {json.dumps(raw_results, indent=2)}")

        # Transform results into expected format
        if isinstance(raw_results, dict) and 'results' in raw_results and isinstance(raw_results['results'], list):
            results = raw_results['results']
            valid_results = [
                {
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result['snippet']
                }
                for result in results
                if isinstance(result, dict) and all(result.get(k) for k in ['title', 'url', 'snippet'])
            ]
            
            results_dict = {
                'results_by_source': {
                    'Giurisprudenza Penale': valid_results
                } if valid_results else {}
            }
            print(f"Found {len(valid_results)} valid results")
        else:
            results_dict = {'results_by_source': {}}
            print("No valid results structure found")

        print(f"Transformed results: {json.dumps(results_dict, indent=2)}")

        # Create search strategy from query
        query = raw_results.get('query', '')
        search_strategy = {
            "terms": [term.strip() for term in query.split() if term.strip() and not term.startswith('site:')],
            "filters": {
                "source": raw_results.get('source', 'giurisprudenzapenale.com')
            },
            "rationale": "Automated legal search based on case details"
        }
        print(f"Search strategy: {json.dumps(search_strategy, indent=2)}")
        
        # Save the search results
        legal_search = LegalSearchResult.objects.create(
            caso=caso,
            search_query=case_details,
            search_results=results_dict,
            search_strategy=search_strategy
        )
        
        # Debug logging after saving
        print(f"Saved search results ID: {legal_search.id}")
        print(f"Saved results from database: {json.dumps(json.loads(legal_search.search_results) if isinstance(legal_search.search_results, str) else legal_search.search_results, indent=2)}")
        
        messages.success(request, 'Ricerca legale completata con successo.')
        return JsonResponse({
            'status': 'success',
            'results': results_dict,
            'search_id': legal_search.id
        })
        
    except Caso.DoesNotExist:
        messages.error(request, 'Caso non trovato.')
        return JsonResponse({
            'status': 'error',
            'message': 'Caso non trovato'
        }, status=404)
    except json.JSONDecodeError as e:
        messages.error(request, 'Errore nel parsing dei dati JSON.')
        return JsonResponse({
            'status': 'error',
            'message': f'Errore nel parsing JSON: {str(e)}'
        }, status=400)
    except ValueError as e:
        if "SERPER_API_KEY" in str(e):
            messages.error(request, 'Chiave API Serper non configurata. Contattare l\'amministratore.')
            return JsonResponse({
                'status': 'error',
                'message': 'Configurazione API mancante',
                'details': str(e)
            }, status=500)
        else:
            messages.error(request, f'Errore di validazione: {str(e)}')
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[DEBUG] Error traceback:\n{error_traceback}")
        messages.error(request, f'Errore durante la ricerca: {str(e)}')
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__,
            'traceback': error_traceback
        }, status=500)

@login_required
def saved_searches(request, caso_id):
    """Display saved Cassazione searches for a case."""
    caso = get_object_or_404(Caso, id=caso_id)
    saved_searches = SavedSearchResult.objects.filter(caso=caso).order_by('-date_saved')
    return render(request, 'cases/saved_searches.html', {
        'caso': caso,
        'saved_searches': saved_searches
    })
