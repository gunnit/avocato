import anthropic
from ..models import Caso, DocumentaryEvidence
from dotenv import load_dotenv
import os
import json
import base64
from django.conf import settings
from django.core.files.storage import default_storage

load_dotenv()

def extract_text_from_pdf(document: DocumentaryEvidence) -> str:
    """
    Extracts text from a PDF document using Claude's PDF processing capabilities.
    
    Args:
        document: DocumentaryEvidence instance containing the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        print("[DEBUG] Starting text extraction for document:", document.title)
        
        # Get the file path and read the PDF content
        file_path = document.document_file.path
        print("[DEBUG] File path:", file_path)
        
        with open(file_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        print("[DEBUG] Successfully read PDF file")
        
        # Encode PDF content to base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        print("[DEBUG] Successfully encoded PDF to base64")
        
        # Initialize Anthropic client
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not found in settings")
        client = anthropic.Anthropic(api_key=api_key)
        print("[DEBUG] Successfully initialized Anthropic client")
        
        # Call Claude API with PDF content
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this document and return it as a single string. Include all content, including headers, footers, and any text in tables or figures."
                    }
                ]
            }]
        )
        print("[DEBUG] Successfully received response from Anthropic API")
        
        # Get the extracted text from response
        extracted_text = response.content[0].text
        print("[DEBUG] Successfully extracted text, length:", len(extracted_text))
        return extracted_text
                
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {str(e)}")
        raise Exception(f"PDF file not found: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Error extracting text: {str(e)}")
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def analyze_document(document: DocumentaryEvidence) -> dict:
    """
    Analyzes a legal document using Claude AI and returns structured analysis.
    
    Args:
        document: DocumentaryEvidence instance to analyze
        
    Returns:
        dict: Structured analysis of the document
    """
    # Prepare the prompt for Claude analysis
    prompt = f"""Analizza la seguente prova legale dal punto di vista dell'avvocato del imputtato, considerando il contesto del sistema giuridico italiano. Esamina l'affidabilità, le implicazioni legali e il valore strategico:

Titolo: {document.title}
Tipo Documento: {document.get_document_type_display()}
Descrizione: {document.description}
Extracted Text From Document: {document.extracted_text}
Stato di Autenticazione: {document.authentication_status}
Note di Autenticazione: {document.authentication_notes}

Fornisci un'analisi dettagliata in formato JSON con la seguente struttura:
{{
    "informazioni_chiave": {{
        "tipo_documento": "",
        "riferimenti_temporali": [],
        "parti_coinvolte": [],
        "fatti_principali": [],
        "rilevanza_processuale": ""
    }},
    "analisi_legale": {{
        "valutazione_affidabilita": "",
        "potenziali_eccezioni": [],
        "questioni_autenticazione": "",
        "valore_probatorio": "",
        "compatibilita_costituzionale": "",
        "conformita_procedura_penale": ""
    }},
    "considerazioni_strategiche": {{
        "punti_forza": [],
        "punti_deboli": [],
        "azioni_raccomandate": [],
        "controargomentazioni": [],
        "strategie_dibattimentali": []
    }},
    "valutazione_rischi": {{
        "rischi_credibilita": [],
        "rischi_legali": [],
        "rischi_strategici": [],
        "impatto_sulla_posizione_processuale": []
    }},
    "raccomandazioni": {{
        "azioni_immediate": [],
        "strategia_lungo_termine": "",
        "prove_supplementari_necessarie": [],
        "consultazioni_specialistiche": [],
        "opzioni_negoziali": []
    }},
    "considerazioni_processuali": {{
        "fase_processuale_ottimale": "",
        "tempistica_presentazione": "",
        "modalita_acquisizione": "",
        "potenziali_nullita": []
    }}
}}

Restituisci SOLO l'oggetto JSON, senza testo o spiegazioni aggiuntive."""

    try:
        # Initialize Anthropic client
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not found in settings")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        # Get the response content
        content = response.content[0].text
        
        # Try to parse the JSON response
        try:
            analysis = json.loads(content)
            return analysis
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                analysis = json.loads(json_str)
                return analysis
            else:
                raise Exception("Could not extract valid JSON from response")
                
    except Exception as e:
        raise Exception(f"Error analyzing document: {str(e)}")

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
