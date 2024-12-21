from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.core.exceptions import PermissionDenied
from ..models import Caso
from .ai_utils import analizza_caso
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
