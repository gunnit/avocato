import time
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class TitoliEIntestazioni(BaseModel):
    oggetto_documento: Optional[str] = Field(None, description="Tipologia o oggetto del documento")
    paragrafi_chiave: Optional[List[str]] = Field(None, description="Lista di paragrafi chiave")

class MetaDatiDocumento(BaseModel):
    autore: Optional[str] = Field(None, description="Autore del documento")
    data_creazione: Optional[datetime] = Field(None, description="Data di creazione")
    data_modifica: Optional[datetime] = Field(None, description="Data di ultima modifica")
    numero_pagine: Optional[int] = Field(None, description="Numero di pagine")
    numero_sezioni: Optional[int] = Field(None, description="Numero di sezioni")

class StrutturaDocumento(BaseModel):
    indice: Optional[List[str]] = Field(None, description="Contenuto dell'indice")
    capitoli: Optional[List[str]] = Field(None, description="Lista di capitoli")
    articoli: Optional[List[str]] = Field(None, description="Articoli o paragrafi rilevanti")
    sottosezioni: Optional[List[str]] = Field(None, description="Sottosezioni o paragrafi")

class DatiGenerali(BaseModel):
    titoli_e_intestazioni: Optional[TitoliEIntestazioni] = None
    meta_dati_documento: Optional[MetaDatiDocumento] = None
    struttura_documento: Optional[StrutturaDocumento] = None

class RiferimentiNormativi(BaseModel):
    articoli_cp_cpp: Optional[List[str]] = Field(None, description="Articoli CP/CPP")
    leggi_speciali: Optional[List[str]] = Field(None, description="Leggi speciali")

class PrecedentiGiurisprudenziali(BaseModel):
    citazioni: Optional[List[str]] = Field(None, description="Citazioni di sentenze")
    collegamento_banca_dati: Optional[List[str]] = Field(None, description="Link banca dati")

class TerminiClausoleCritiche(BaseModel):
    clausole: Optional[List[str]] = Field(None, description="Clausole critiche")

class InformazioniLegaliSpecifiche(BaseModel):
    riferimenti_normativi: Optional[RiferimentiNormativi] = None
    precedenti_giurisprudenziali: Optional[PrecedentiGiurisprudenziali] = None
    termini_clausole_critiche: Optional[TerminiClausoleCritiche] = None

class DateRilevanti(BaseModel):
    scadenze_deposito: Optional[List[datetime]] = Field(None, description="Scadenze deposito")
    date_udienze: Optional[List[datetime]] = Field(None, description="Date udienze")
    termini_prescrizione: Optional[List[datetime]] = Field(None, description="Termini prescrizione")

class ParteCoinvolta(BaseModel):
    nome: Optional[str] = Field(None, description="Nome della parte")
    ruolo: Optional[str] = Field(None, description="Ruolo nel procedimento")

class EventoProcessuale(BaseModel):
    tipo_atto: Optional[str] = Field(None, description="Tipo di atto processuale")
    data_deposito: Optional[datetime] = Field(None, description="Data di deposito")
    descrizione_fatti: Optional[str] = Field(None, description="Descrizione fatti")

class DatiProcessuali(BaseModel):
    date_rilevanti: Optional[DateRilevanti] = None
    parti_coinvolte: Optional[List[ParteCoinvolta]] = None
    eventi_processuali: Optional[List[EventoProcessuale]] = None

class AnalisiLinguistica(BaseModel):
    frasi_ambigue: Optional[List[str]] = Field(None, description="Frasi ambigue")
    punti_debolezza_difesa: Optional[List[str]] = Field(None, description="Punti deboli difesa")
    sentiment_memorie_atti: Optional[str] = Field(None, description="Tono generale")

class DocumentSchema(BaseModel):
    dati_generali: Optional[DatiGenerali] = None
    informazioni_legali_specifiche: Optional[InformazioniLegaliSpecifiche] = None
    dati_processuali: Optional[DatiProcessuali] = None
    analisi_linguistica: Optional[AnalisiLinguistica] = None

class PDFPage(BaseModel):
    """Model for storing page content and metadata"""
    page_num: int
    text: str
    metadata: Dict = Field(default_factory=dict)
    confidence: float = 1.0
    source: str = "text"  # 'text' or 'vision'

class PDFProcessingResult(BaseModel):
    """Model for storing PDF processing results"""
    text: str
    structured_content: List[Dict]
    chunks: List[Dict]
    processing_type: str
    trace_id: str = Field(default_factory=lambda: f"trace_{time.time()}")

class PageAnalysis(BaseModel):
    """Model for storing page analysis results"""
    page_num: int
    analysis: DocumentSchema
    metadata: Dict = Field(default_factory=dict)
