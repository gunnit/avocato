import anthropic
from ..models import Caso
from dotenv import load_dotenv
import os

load_dotenv()

def analizza_caso(caso_id):
    caso = Caso.objects.get(id=caso_id)
    
    client = anthropic.Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
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
