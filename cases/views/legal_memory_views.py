from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Caso
import json

def memoria_difensiva(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    
    if request.method == 'POST':
        # Extract form data
        fatti = request.POST.get('fatti', '')
        argomentazioni = request.POST.get('argomentazioni', '')
        prove = request.POST.get('prove', '')
        strategia = request.POST.get('strategia', '')
        conclusioni = request.POST.get('conclusioni', '')
        action = request.POST.get('action', 'draft')
        
        # Create a structured format for the defense memory
        memoria = {
            'fatti': fatti,
            'argomentazioni_legali': argomentazioni,
            'elementi_probatori': prove,
            'strategia_difensiva': strategia,
            'conclusioni': conclusioni,
            'stato': 'finale' if action == 'final' else 'bozza'
        }
        
        # Save to the case
        caso.riferimenti_legali = json.dumps(memoria)
        caso.stato = 'Memoria Completata' if action == 'final' else 'Memoria in Bozza'
        caso.save()
        
        messages.success(request, 'Memoria difensiva salvata come ' + ('versione finale' if action == 'final' else 'bozza'))
        
        if action == 'final':
            return redirect('memoria_difensiva_detail', caso_id=caso.id)
    
    # Try to load existing memoria if it exists
    try:
        memoria_esistente = json.loads(caso.riferimenti_legali) if caso.riferimenti_legali else None
    except json.JSONDecodeError:
        memoria_esistente = None
    
    return render(request, 'cases/memoria_difensiva.html', {
        'caso': caso,
        'memoria': memoria_esistente
    })

def memoria_difensiva_detail(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    try:
        memoria = json.loads(caso.riferimenti_legali) if caso.riferimenti_legali else None
    except json.JSONDecodeError:
        memoria = None
    
    if not memoria or memoria.get('stato') != 'finale':
        messages.error(request, 'La memoria difensiva non è ancora stata finalizzata.')
        return redirect('dettaglio_caso', caso_id=caso.id)
    
    return render(request, 'cases/memoria_difensiva_detail.html', {
        'caso': caso,
        'memoria': memoria
    })
