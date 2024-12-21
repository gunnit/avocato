import anthropic
from ..models import Caso
from dotenv import load_dotenv
import os

load_dotenv()

def analizza_caso(caso_id):
    print(f"[DEBUG] Starting analizza_caso for caso_id: {caso_id}")
    caso = Caso.objects.get(id=caso_id)
    print(f"[DEBUG] Retrieved case: {caso.titolo}")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    print(f"[DEBUG] Got API key (length: {len(api_key) if api_key else 0})")
    
    client = anthropic.Anthropic(api_key=api_key)
    print("[DEBUG] Created Anthropic client")
    
    prompt = f"""
    Analizza il seguente caso secondo la legge italiana e fornisci una risposta in formato JSON strutturato come segue:
    
    Caso da analizzare:
    Titolo: {caso.titolo}
    Descrizione: {caso.descrizione}
    
    La risposta deve essere un oggetto JSON valido con la seguente struttura:
    {{
        "analisi_legale": {{
            "quadro_normativo": [
                {{"titolo": "string", "descrizione": "string"}}
            ],
            "precedenti_rilevanti": [
                {{"riferimento": "string", "esito": "string"}}
            ],
            "giurisprudenza": [
                {{"riferimento": "string", "principio": "string"}}
            ],
            "punti_chiave": ["string"]
        }},
        "strategie_difesa": {{
            "argomenti_principali": ["string"],
            "contro_argomentazioni": [
                {{"argomento": "string", "risposta": "string"}}
            ],
            "punti_forza": ["string"],
            "approccio_difensivo": [
                {{"titolo": "string", "descrizione": "string"}}
            ],
            "criticita": ["string"]
        }},
        "gestione_prove": {{
            "prove_documentali": [
                {{"titolo": "string", "descrizione": "string", "rilevanza": "Alta|Media|Bassa"}}
            ],
            "testimonianze": [
                {{"testimone": "string", "dichiarazione": "string", "affidabilita": "Alta|Media|Bassa"}}
            ],
            "analisi_prove": ["string"],
            "prove_da_acquisire": [
                {{"descrizione": "string", "priorita": "Alta|Media|Bassa"}}
            ],
            "criticita_probatorie": ["string"]
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
            "esito_favorevole": "string",
            "esito_intermedio": "string",
            "esito_sfavorevole": "string",
            "strategie_risoluzione": ["string"],
            "prossimi_passi": ["string"]
        }}
    }}

    Assicurati che la risposta sia un JSON valido e che tutti i campi siano compilati in modo dettagliato e pertinente al caso specifico.
    Non includere commenti o testo aggiuntivo fuori dalla struttura JSON.
    """
    
    try:
        print("[DEBUG] Sending request to Anthropic API...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        print("[DEBUG] Got response from Anthropic API")
        result = response.content[0].text
        print(f"[DEBUG] Response length: {len(result)}")
        return result
    except Exception as e:
        print(f"[DEBUG] Error in analizza_caso: {str(e)}")
        raise Exception(f"Errore durante l'analisi AI: {str(e)}")
