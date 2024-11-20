from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Caso
from .ai_utils import analizza_caso
import json
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
    caso = get_object_or_404(Caso, id=caso_id)
    try:
        analisi = analizza_caso(caso.id)
        caso.analisi_ai = analisi
        caso.save()
        messages.success(request, 'Analisi rigenerata con successo.')
    except Exception as e:
        messages.error(request, f'Errore durante la rigenerazione dell\'analisi: {str(e)}')
    
    return redirect('dettaglio_caso', caso_id=caso.id)
