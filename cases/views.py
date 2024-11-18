from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Caso, ChatMessage
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
        
        # Analisi immediata del caso
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
