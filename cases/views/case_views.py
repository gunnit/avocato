from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Caso
from .ai_utils import analizza_caso
import json

@login_required
def lista_casi(request):
    casi = Caso.objects.all().order_by('-data_creazione')
    return render(request, 'cases/lista_casi.html', {'casi': casi})

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
