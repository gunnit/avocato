from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from ..models import Caso, DocumentaryEvidence
import anthropic
import json
import os

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

@require_http_methods(["POST"])
def generate_content(request, caso_id):
    """Generate AI content for a specific field in the defense memory."""
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    caso = get_object_or_404(Caso, id=caso_id)
    data = json.loads(request.body)
    field = data.get('field')
    
    # Get case data and documents
    case_data = {
        'titolo': caso.titolo,
        'descrizione': caso.descrizione,
        'stato': caso.stato,
        'data_creazione': caso.data_creazione.strftime('%Y-%m-%d'),
        'documenti': [doc.title for doc in caso.documentary_evidences.all()]  # Using correct related_name
    }
    
    # Define prompts for each field
    prompts = {
        'fatti': f"""Sei un avvocato esperto. Genera una esposizione dei fatti per una memoria difensiva basata sul seguente caso:
Titolo: {case_data['titolo']}
Descrizione: {case_data['descrizione']}
Documenti disponibili: {', '.join(case_data['documenti'])}

L'esposizione deve:
1. Seguire un ordine cronologico
2. Essere oggettiva e professionale
3. Citare i documenti pertinenti
4. Evidenziare gli elementi rilevanti per la difesa""",

        'argomentazioni': f"""Sei un avvocato esperto. Genera le argomentazioni legali per una memoria difensiva basata sul seguente caso:
Titolo: {case_data['titolo']}
Descrizione: {case_data['descrizione']}
Documenti disponibili: {', '.join(case_data['documenti'])}

Le argomentazioni devono:
1. Citare articoli di legge pertinenti
2. Riferire precedenti giurisprudenziali rilevanti
3. Collegare le norme ai fatti specifici
4. Strutturare gli argomenti in modo logico e convincente""",

        'prove': f"""Sei un avvocato esperto. Genera una sezione sugli elementi probatori per una memoria difensiva basata sul seguente caso:
Titolo: {case_data['titolo']}
Descrizione: {case_data['descrizione']}
Documenti disponibili: {', '.join(case_data['documenti'])}

L'analisi delle prove deve:
1. Elencare e catalogare tutte le prove disponibili
2. Specificare la rilevanza di ogni prova
3. Indicare fonte e data di ogni documento
4. Organizzare le prove per tipologia""",

        'strategia': f"""Sei un avvocato esperto. Genera una strategia difensiva per una memoria basata sul seguente caso:
Titolo: {case_data['titolo']}
Descrizione: {case_data['descrizione']}
Documenti disponibili: {', '.join(case_data['documenti'])}

La strategia deve:
1. Delineare gli argomenti principali della difesa
2. Anticipare e confutare possibili obiezioni
3. Evidenziare i punti di forza del caso
4. Proporre soluzioni concrete""",

        'conclusioni': f"""Sei un avvocato esperto. Genera le conclusioni per una memoria difensiva basata sul seguente caso:
Titolo: {case_data['titolo']}
Descrizione: {case_data['descrizione']}
Documenti disponibili: {', '.join(case_data['documenti'])}

Le conclusioni devono:
1. Riassumere i punti principali della memoria
2. Formulare richieste specifiche e precise
3. Indicare il petitum in modo chiaro
4. Mantenere coerenza con le argomentazioni precedenti"""
    }
    
    if field not in prompts:
        return JsonResponse({'error': 'Campo non valido'}, status=400)
    
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            system="Sei un avvocato esperto italiano specializzato nella redazione di memorie difensive. Rispondi sempre in italiano.",
            messages=[
                {
                    "role": "user",
                    "content": prompts[field]
                }
            ]
        )
        
        return JsonResponse({'content': message.content[0].text})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
