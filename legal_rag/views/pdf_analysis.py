import json
import logging
import requests
import time
import traceback
from datetime import datetime
from typing import List, Dict, Optional
from requests.exceptions import Timeout, RequestException
from django.conf import settings
from .prompts import LEGAL_ANALYSIS_PROMPT
from ..schemas import DocumentSchema, PageAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_page_content(page_data: tuple) -> Optional[PageAnalysis]:
    """Analyze a single page's content using GPT-4"""
    page_num, page_text = page_data
    try:
        logger.info(f"\n{'='*80}\nAnalyzing page {page_num}\n{'='*80}")
        logger.info(f"Input text length: {len(page_text)} characters")
        logger.info(f"Text preview: {page_text[:200]}...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        # Log the prompts being sent
        logger.info("\nSystem Prompt:")
        logger.info("-" * 40)
        logger.info(LEGAL_ANALYSIS_PROMPT)
        
        logger.info("\nUser Prompt:")
        logger.info("-" * 40)
        logger.info(f"[PAGINA {page_num}]\n\n{page_text[:200]}...")
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": LEGAL_ANALYSIS_PROMPT
                },
                {
                    "role": "user",
                    "content": f"[PAGINA {page_num}]\n\n{page_text}"
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
            "response_format": { "type": "json_object" }
        }
        
        # Process with retry mechanism
        for attempt in range(3):
            try:
                logger.info(f"Attempt {attempt + 1} to analyze page {page_num}")
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'error' in response_data:
                    logger.error(f"OpenAI API error for page {page_num}: {response_data['error']}")
                    raise RequestException(f"OpenAI API error: {response_data['error']}")
                    
                analysis_text = response_data['choices'][0]['message']['content']
                if not analysis_text.strip():
                    logger.warning(f"Empty analysis for page {page_num}")
                    return None
                
                logger.info("\nRaw GPT Response:")
                logger.info("-" * 40)
                logger.info(analysis_text)
                
                def transform_to_schema(data: dict) -> dict:
                    """Transform the GPT response to match our schema structure"""
                    def serialize_datetime(obj):
                        """Convert datetime objects to ISO format strings"""
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        elif isinstance(obj, dict):
                            return {k: serialize_datetime(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [serialize_datetime(item) for item in obj]
                        return obj

                    transformed = {}
                    
                    # Transform dati_generali
                    if 'dati_generali' in data:
                        transformed['dati_generali'] = data['dati_generali']
                    
                    # Transform informazioni_legali_specifiche
                    if 'informazioni_legali_specifiche' in data:
                        ils = data['informazioni_legali_specifiche']
                        transformed['informazioni_legali_specifiche'] = {}
                        
                        # Handle riferimenti_normativi
                        if 'riferimenti_normativi' in ils:
                            transformed['informazioni_legali_specifiche']['riferimenti_normativi'] = ils['riferimenti_normativi']
                        
                        # Handle precedenti_giurisprudenziali
                        if 'precedenti_giurisprudenziali' in ils:
                            transformed['informazioni_legali_specifiche']['precedenti_giurisprudenziali'] = ils['precedenti_giurisprudenziali']
                        
                        # Transform termini_clausole_critiche from array to object
                        if 'termini_clausole_critiche' in ils:
                            if isinstance(ils['termini_clausole_critiche'], list):
                                transformed['informazioni_legali_specifiche']['termini_clausole_critiche'] = {
                                    'clausole': ils['termini_clausole_critiche']
                                }
                            else:
                                transformed['informazioni_legali_specifiche']['termini_clausole_critiche'] = ils['termini_clausole_critiche']
                    
                    # Transform dati_processuali
                    if 'dati_processuali' in data:
                        dp = data['dati_processuali']
                        transformed['dati_processuali'] = {}
                        
                        # Transform date_rilevanti from array to object
                        if 'date_rilevanti' in dp:
                            if isinstance(dp['date_rilevanti'], list):
                                dates = dp['date_rilevanti']
                                transformed['dati_processuali']['date_rilevanti'] = {
                                    'scadenze_deposito': [d['data'] for d in dates if 'scadenza' in d.get('descrizione', '').lower()],
                                    'date_udienze': [d['data'] for d in dates if 'udienza' in d.get('descrizione', '').lower()],
                                    'termini_prescrizione': [d['data'] for d in dates if 'prescrizione' in d.get('descrizione', '').lower()]
                                }
                            else:
                                transformed['dati_processuali']['date_rilevanti'] = dp['date_rilevanti']
                        
                        # Copy other dati_processuali fields
                        if 'parti_coinvolte' in dp:
                            transformed['dati_processuali']['parti_coinvolte'] = dp['parti_coinvolte']
                        if 'eventi_processuali' in dp:
                            transformed['dati_processuali']['eventi_processuali'] = dp['eventi_processuali']
                    
                    # Transform analisi_linguistica
                    if 'analisi_linguistica' in data:
                        al = data['analisi_linguistica']
                        transformed['analisi_linguistica'] = {
                            'frasi_ambigue': al.get('frasi_ambigue_o_critiche', al.get('frasi_ambigue', [])),
                            'punti_debolezza_difesa': al.get('punti_debolezza_nella_difesa', al.get('punti_debolezza_difesa', [])),
                            'sentiment_memorie_atti': al.get('tono_generale_documento', al.get('sentiment_memorie_atti', ''))
                        }
                    
                    # Serialize any datetime objects in the transformed data
                    return serialize_datetime(transformed)

                # First try to parse as pure JSON
                try:
                    raw_data = json.loads(analysis_text)
                    logger.info("Successfully parsed response as JSON")
                    analysis_data = transform_to_schema(raw_data)
                    logger.info("Successfully transformed data to match schema")
                except json.JSONDecodeError:
                    logger.warning("Failed to parse response as pure JSON, attempting to extract JSON")
                    # If not pure JSON, try to extract JSON from the text
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', analysis_text)
                    if json_match:
                        try:
                            raw_data = json.loads(json_match.group(0))
                            analysis_data = transform_to_schema(raw_data)
                            logger.info("Successfully extracted and transformed JSON")
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse extracted JSON for page {page_num}")
                            # Create basic schema from text
                            analysis_data = {
                                "dati_generali": {
                                    "titoli_e_intestazioni": {
                                        "paragrafi_chiave": [analysis_text.strip()]
                                    }
                                }
                            }
                    else:
                        # If no JSON found, create basic schema from text
                        logger.warning(f"No JSON found in response for page {page_num}, creating basic schema")
                        analysis_data = {
                            "dati_generali": {
                                "titoli_e_intestazioni": {
                                    "paragrafi_chiave": [analysis_text.strip()]
                                }
                            }
                        }
                
                # Validate datetime fields
                def convert_dates(obj):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if isinstance(value, str) and any(date_field in key for date_field in ['data', 'date']):
                                try:
                                    # Try to parse and format the date
                                    parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    obj[key] = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")
                                except (ValueError, TypeError):
                                    logger.warning(f"Failed to parse date value: {value}")
                                    # If date parsing fails, remove the field
                                    obj[key] = None
                            elif isinstance(value, (dict, list)):
                                convert_dates(value)
                    elif isinstance(obj, list):
                        for item in obj:
                            convert_dates(item)
                    return obj
                
                # Clean and validate the data
                logger.info("Converting and validating date fields")
                analysis_data = convert_dates(analysis_data)
                
                try:
                    logger.info("Creating DocumentSchema from analysis data")
                    document_schema = DocumentSchema(**analysis_data)
                    result = PageAnalysis(
                        page_num=page_num,
                        analysis=document_schema,
                        metadata={'page_num': page_num}
                    )
                    
                    logger.info("\nProcessed Analysis Result:")
                    logger.info("-" * 40)
                    logger.info(json.dumps(result.dict(), indent=2, ensure_ascii=False, default=str))
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed to create DocumentSchema for page {page_num}: {str(e)}")
                    logger.error(f"Schema validation error details: {traceback.format_exc()}")
                    # Create minimal valid schema
                    minimal_data = {
                        "dati_generali": {
                            "titoli_e_intestazioni": {
                                "paragrafi_chiave": [f"Error parsing page {page_num}: {str(e)}"]
                            }
                        }
                    }
                    document_schema = DocumentSchema(**minimal_data)
                    return PageAnalysis(
                        page_num=page_num,
                        analysis=document_schema,
                        metadata={'page_num': page_num}
                    )
                
            except (Timeout, RequestException) as e:
                if attempt == 2:
                    logger.error(f"Failed to analyze page {page_num} after 3 attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed for page {page_num}: {str(e)}")
                time.sleep(1)  # Wait before retry
                
    except Exception as e:
        logger.error(f"Error analyzing page {page_num}:")
        logger.error(traceback.format_exc())
        return None

def merge_lists(existing: Optional[List], new: Optional[List]) -> Optional[List]:
    """Helper function to merge lists without duplicates"""
    if not existing and not new:
        return None
    if not existing:
        return new
    if not new:
        return existing
    # Convert to sets to remove duplicates, then back to list
    return list(set(existing + new))

def merge_page_analyses(pages: List[PageAnalysis]) -> DocumentSchema:
    """Merge multiple page analyses into a single DocumentSchema"""
    logger.info(f"\n{'='*80}\nMerging {len(pages)} page analyses\n{'='*80}")
    
    combined_schema = DocumentSchema()
    
    for page in pages:
        logger.info(f"\nProcessing analysis from page {page.page_num}")
        page_schema = page.analysis
        
        # Merge DatiGenerali
        if page_schema.dati_generali:
            if not combined_schema.dati_generali:
                combined_schema.dati_generali = page_schema.dati_generali
                logger.info("Initialized DatiGenerali from first page")
            else:
                dg = combined_schema.dati_generali
                pg_dg = page_schema.dati_generali
                
                if pg_dg.titoli_e_intestazioni:
                    if not dg.titoli_e_intestazioni:
                        dg.titoli_e_intestazioni = pg_dg.titoli_e_intestazioni
                    else:
                        dg.titoli_e_intestazioni.paragrafi_chiave = merge_lists(
                            dg.titoli_e_intestazioni.paragrafi_chiave,
                            pg_dg.titoli_e_intestazioni.paragrafi_chiave
                        )
                
                if pg_dg.struttura_documento:
                    if not dg.struttura_documento:
                        dg.struttura_documento = pg_dg.struttura_documento
                    else:
                        sd = dg.struttura_documento
                        pg_sd = pg_dg.struttura_documento
                        sd.indice = merge_lists(sd.indice, pg_sd.indice)
                        sd.capitoli = merge_lists(sd.capitoli, pg_sd.capitoli)
                        sd.articoli = merge_lists(sd.articoli, pg_sd.articoli)
                        sd.sottosezioni = merge_lists(sd.sottosezioni, pg_sd.sottosezioni)
        
        # Merge InformazioniLegaliSpecifiche
        if page_schema.informazioni_legali_specifiche:
            if not combined_schema.informazioni_legali_specifiche:
                combined_schema.informazioni_legali_specifiche = page_schema.informazioni_legali_specifiche
                logger.info("Initialized InformazioniLegaliSpecifiche from first page")
            else:
                ils = combined_schema.informazioni_legali_specifiche
                pg_ils = page_schema.informazioni_legali_specifiche
                
                if pg_ils.riferimenti_normativi:
                    if not ils.riferimenti_normativi:
                        ils.riferimenti_normativi = pg_ils.riferimenti_normativi
                    else:
                        ils.riferimenti_normativi.articoli_cp_cpp = merge_lists(
                            ils.riferimenti_normativi.articoli_cp_cpp,
                            pg_ils.riferimenti_normativi.articoli_cp_cpp
                        )
                        ils.riferimenti_normativi.leggi_speciali = merge_lists(
                            ils.riferimenti_normativi.leggi_speciali,
                            pg_ils.riferimenti_normativi.leggi_speciali
                        )
        
        # Merge DatiProcessuali
        if page_schema.dati_processuali:
            if not combined_schema.dati_processuali:
                combined_schema.dati_processuali = page_schema.dati_processuali
                logger.info("Initialized DatiProcessuali from first page")
            else:
                dp = combined_schema.dati_processuali
                pg_dp = page_schema.dati_processuali
                
                if pg_dp.parti_coinvolte:
                    if not dp.parti_coinvolte:
                        dp.parti_coinvolte = pg_dp.parti_coinvolte
                    else:
                        dp.parti_coinvolte.extend(pg_dp.parti_coinvolte)
                
                if pg_dp.eventi_processuali:
                    if not dp.eventi_processuali:
                        dp.eventi_processuali = pg_dp.eventi_processuali
                    else:
                        dp.eventi_processuali.extend(pg_dp.eventi_processuali)
        
        # Merge AnalisiLinguistica
        if page_schema.analisi_linguistica:
            if not combined_schema.analisi_linguistica:
                combined_schema.analisi_linguistica = page_schema.analisi_linguistica
                logger.info("Initialized AnalisiLinguistica from first page")
            else:
                al = combined_schema.analisi_linguistica
                pg_al = page_schema.analisi_linguistica
                al.frasi_ambigue = merge_lists(al.frasi_ambigue, pg_al.frasi_ambigue)
                al.punti_debolezza_difesa = merge_lists(
                    al.punti_debolezza_difesa,
                    pg_al.punti_debolezza_difesa
                )
    
    logger.info("\nFinished merging page analyses")
    logger.info("Final schema preview:")
    logger.info("-" * 40)
    logger.info(json.dumps(combined_schema.dict(exclude_none=True), indent=2, ensure_ascii=False, default=str)[:500] + "...")
    
    return combined_schema
