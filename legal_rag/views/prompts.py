"""
This module contains prompts used for PDF processing and analysis.
"""

# Prompt for GPT-4 Vision to extract text from PDF pages
PDF_TEXT_EXTRACTION_PROMPT = "Please extract and return all the text from this image. Return only the extracted text, no additional commentary."

# Prompt for GPT-4 to analyze legal document content
LEGAL_ANALYSIS_PROMPT = """Sei un assistente legale esperto. Analizza il seguente testo e fornisci:
1. Un riassunto conciso dei punti principali
2. Evidenziazione delle parti importanti con spiegazione del loro significato
3. Identificazione di:
   - Questioni legali chiave
   - Date e scadenze rilevanti
   - Parti coinvolte
   - Richieste o decisioni specifiche
4. Eventuali raccomandazioni o punti di attenzione

Formatta la risposta in modo strutturato usando markdown, con sezioni chiare per ogni categoria."""
