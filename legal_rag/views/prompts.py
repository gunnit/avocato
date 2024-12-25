"""
This module contains prompts used for PDF processing and analysis.
"""

# Prompt for GPT-4 Vision to extract text from PDF pages
PDF_TEXT_EXTRACTION_PROMPT = "Please extract and return all the text from this image. Return only the extracted text, no additional commentary."

# Prompt for GPT-4 to analyze legal document content
LEGAL_ANALYSIS_PROMPT = """Sei un assistente legale esperto. Analizza il seguente testo ed estrai informazioni strutturate secondo questo schema:

1. DATI GENERALI:
   - Oggetto del documento (es. sentenza, contratto)
   - Paragrafi chiave
   - Meta-dati (autore, date, numero pagine/sezioni)
   - Struttura del documento (indice, capitoli, articoli)

2. INFORMAZIONI LEGALI:
   - Riferimenti normativi (articoli CP/CPP, leggi speciali)
   - Precedenti giurisprudenziali
   - Termini e clausole critiche

3. DATI PROCESSUALI:
   - Date rilevanti (scadenze, udienze, termini)
   - Parti coinvolte (nomi e ruoli)
   - Eventi processuali (tipo atto, data deposito, fatti)

4. ANALISI LINGUISTICA:
   - Frasi ambigue o critiche
   - Punti di debolezza nella difesa
   - Tono generale del documento

IMPORTANTE: Restituisci l'analisi ESCLUSIVAMENTE come JSON valido, senza alcun testo aggiuntivo prima o dopo. Il JSON deve seguire ESATTAMENTE questa struttura:

{
    "dati_generali": {
        "titoli_e_intestazioni": {
            "oggetto_documento": "string",
            "paragrafi_chiave": ["string"]
        },
        "meta_dati_documento": {
            "autore": "string",
            "data_creazione": "YYYY-MM-DDTHH:MM:SS",
            "data_modifica": "YYYY-MM-DDTHH:MM:SS",
            "numero_pagine": 0,
            "numero_sezioni": 0
        },
        "struttura_documento": {
            "indice": ["string"],
            "capitoli": ["string"],
            "articoli": ["string"],
            "sottosezioni": ["string"]
        }
    },
    "informazioni_legali_specifiche": {
        "riferimenti_normativi": {
            "articoli_cp_cpp": ["string"],
            "leggi_speciali": ["string"]
        },
        "precedenti_giurisprudenziali": {
            "citazioni": ["string"],
            "collegamento_banca_dati": ["string"]
        },
        "termini_clausole_critiche": {
            "clausole": ["string"]
        }
    },
    "dati_processuali": {
        "date_rilevanti": {
            "scadenze_deposito": ["YYYY-MM-DDTHH:MM:SS"],
            "date_udienze": ["YYYY-MM-DDTHH:MM:SS"],
            "termini_prescrizione": ["YYYY-MM-DDTHH:MM:SS"]
        },
        "parti_coinvolte": [
            {
                "nome": "string",
                "ruolo": "string"
            }
        ],
        "eventi_processuali": [
            {
                "tipo_atto": "string",
                "data_deposito": "YYYY-MM-DDTHH:MM:SS",
                "descrizione_fatti": "string"
            }
        ]
    },
    "analisi_linguistica": {
        "frasi_ambigue": ["string"],
        "punti_debolezza_difesa": ["string"],
        "sentiment_memorie_atti": "string"
    }
}

REGOLE FONDAMENTALI:
1. La risposta deve contenere SOLO il JSON, nessun altro testo
2. Non includere commenti, spiegazioni o markdown
3. Usa il formato datetime ISO: "YYYY-MM-DDTHH:MM:SS"
4. Includi solo i campi per cui hai trovato informazioni concrete nel testo
5. Non inventare o dedurre informazioni non presenti nel testo
6. Il JSON deve essere valido e correttamente formattato
7. Non aggiungere campi non presenti nello schema
8. Non includere caratteri speciali o formattazione nel testo
9. IMPORTANTE: Segui ESATTAMENTE la struttura del JSON fornita sopra

Se non trovi informazioni sufficienti, restituisci un JSON minimo con almeno dati_generali:
{
    "dati_generali": {
        "titoli_e_intestazioni": {
            "paragrafi_chiave": ["Testo analizzato"]
        }
    }
}"""
