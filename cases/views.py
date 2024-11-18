from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max
from .models import Caso, ChatMessage, DocumentaryEvidence
import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

def lista_casi(request):
    casi = Caso.objects.all().order_by('-data_creazione')
    return render(request, 'cases/lista_casi.html', {'casi': casi})

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

def dettaglio_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    try:
        analisi_json = json.loads(caso.analisi_ai) if caso.analisi_ai else None
    except json.JSONDecodeError:
        analisi_json = None
    return render(request, 'cases/dettaglio_caso.html', {'caso': caso, 'analisi_json': analisi_json})

def documentary_evidence_list(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    documents = caso.documentary_evidences.all().order_by('exhibit_number')
    return render(request, 'cases/documentary_evidence_list.html', {
        'caso': caso,
        'documents': documents
    })

def documentary_evidence_add(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    
    if request.method == 'POST':
        # Get the next available exhibit number
        max_exhibit = caso.documentary_evidences.aggregate(Max('exhibit_number'))['exhibit_number__max']
        next_exhibit = 1 if max_exhibit is None else max_exhibit + 1
        
        document = DocumentaryEvidence(
            caso=caso,
            exhibit_number=next_exhibit,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            document_file=request.FILES.get('document_file'),
            authentication_status=request.POST.get('authentication_status', 'pending'),
            authentication_notes=request.POST.get('authentication_notes', '')
        )
        document.save()
        
        messages.success(request, 'Documento aggiunto con successo.')
        return redirect('documentary_evidence_list', caso_id=caso.id)
    
    return render(request, 'cases/documentary_evidence_form.html', {
        'caso': caso,
        'action': 'add'
    })

def documentary_evidence_edit(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    if request.method == 'POST':
        document.title = request.POST.get('title')
        document.description = request.POST.get('description')
        if 'document_file' in request.FILES:
            document.document_file = request.FILES['document_file']
        document.authentication_status = request.POST.get('authentication_status')
        document.authentication_notes = request.POST.get('authentication_notes')
        document.save()
        
        messages.success(request, 'Documento aggiornato con successo.')
        return redirect('documentary_evidence_list', caso_id=caso.id)
    
    return render(request, 'cases/documentary_evidence_form.html', {
        'caso': caso,
        'document': document,
        'action': 'edit'
    })

def documentary_evidence_detail(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    return render(request, 'cases/documentary_evidence_detail.html', {
        'caso': caso,
        'document': document
    })

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

def chat_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    chat_messages = caso.chat_messages.all()

    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Save user message
            ChatMessage.objects.create(
                caso=caso,
                content=user_message,
                is_ai=False
            )

            try:
                client = anthropic.Anthropic()
                
                # Create context from case details
                context = f"""
                Dettagli del caso:
                Titolo: {caso.titolo}
                Descrizione: {caso.descrizione}
                Analisi AI: {caso.analisi_ai}
                Riferimenti Legali: {caso.riferimenti_legali}
                """

                # Get chat history
                chat_history = "\n".join([
                    f"{'Assistant' if msg.is_ai else 'Human'}: {msg.content}"
                    for msg in chat_messages
                ])

                # Create the prompt with context and history
                prompt = f"""
                {context}

                Cronologia chat:
                {chat_history}

                Human: {user_message}

                Rispondi come un assistente legale esperto, fornendo informazioni accurate e pertinenti basate sul contesto del caso.
                """

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Save AI response
                ChatMessage.objects.create(
                    caso=caso,
                    content=response.content[0].text,
                    is_ai=True
                )

            except Exception as e:
                messages.error(request, f'Errore durante la generazione della risposta: {str(e)}')

    return render(request, 'cases/chat.html', {
        'caso': caso,
        'messages': caso.chat_messages.all()
    })

def analizza_caso(caso_id):
    caso = Caso.objects.get(id=caso_id)
    
    client = anthropic.Anthropic()
    
    prompt = f"""
    Analizza il seguente caso secondo la legge italiana e fornisci una risposta in formato JSON strutturato come segue:
    
    Caso da analizzare:
    Titolo: {caso.titolo}
    Descrizione: {caso.descrizione}
    
    La risposta deve essere un oggetto JSON valido con la seguente struttura:
    {{
        "analisi_legale": {{
            "inquadramento_giuridico": "string",
            "norme_applicabili": ["string"],
            "giurisprudenza_rilevante": ["string"],
            "aggravanti": ["string"],
            "attenuanti": ["string"]
        }},
        "strategie_difensive": {{
            "linee_principali": ["string"],
            "argomentazioni": ["string"],
            "eccezioni_procedurali": ["string"],
            "strategie_alternative": ["string"]
        }},
        "gestione_prove": {{
            "prove_da_raccogliere": ["string"],
            "documenti_necessari": ["string"],
            "testimonianze": ["string"],
            "perizie_tecniche": ["string"],
            "tempistiche": "string"
        }},
        "azioni_immediate": {{
            "passi_urgenti": ["string"],
            "misure_cautelari": ["string"],
            "azioni_preventive": ["string"],
            "comunicazioni": ["string"]
        }},
        "timeline": {{
            "tempistiche_procedurali": "string",
            "date_chiave": ["string"],
            "termini_perentori": ["string"],
            "calendario_azioni": ["string"]
        }},
        "analisi_rischi": {{
            "conseguenze_possibili": ["string"],
            "scenario_migliore": "string",
            "scenario_peggiore": "string",
            "fattori_critici": ["string"],
            "strategie_mitigazione": ["string"]
        }},
        "supporto_risorse": {{
            "professionisti": ["string"],
            "servizi_supporto": ["string"],
            "contatti_utili": ["string"],
            "risorse_disponibili": ["string"]
        }},
        "raccomandazioni": {{
            "comportamenti_da_adottare": ["string"],
            "comportamenti_da_evitare": ["string"],
            "gestione_comunicazione": ["string"],
            "suggerimenti_quotidiani": ["string"]
        }},
        "aspetti_economici": {{
            "stima_costi": "string",
            "sanzioni_possibili": ["string"],
            "supporto_finanziario": ["string"],
            "gestione_spese": ["string"]
        }},
        "prospettive_risoluzione": {{
            "possibili_esiti": ["string"],
            "opzioni_patteggiamento": ["string"],
            "tempistiche_stimate": "string",
            "strategie_negoziazione": ["string"]
        }}
    }}

    Assicurati che la risposta sia un JSON valido e che tutti i campi siano compilati in modo dettagliato e pertinente al caso specifico.
    Non includere commenti o testo aggiuntivo fuori dalla struttura JSON.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"Errore durante l'analisi AI: {str(e)}"
