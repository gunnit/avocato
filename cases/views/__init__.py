from .case_views import (
    lista_casi,
    nuovo_caso,
    dettaglio_caso,
    rigenera_analisi,
    edit_caso,
    delete_caso
)

from .documentary_evidence_views import (
    documentary_evidence_list,
    documentary_evidence_add,
    documentary_evidence_edit,
    documentary_evidence_detail
)

from .legal_memory_views import (
    memoria_difensiva,
    memoria_difensiva_detail
)

from .chat_views import (
    chat_caso
)

from .ai_utils import (
    analizza_caso
)

__all__ = [
    # Case views
    'lista_casi',
    'nuovo_caso',
    'dettaglio_caso',
    'rigenera_analisi',
    'edit_caso',
    'delete_caso',
    
    # Documentary evidence views
    'documentary_evidence_list',
    'documentary_evidence_add',
    'documentary_evidence_edit',
    'documentary_evidence_detail',
    
    # Legal memory views
    'memoria_difensiva',
    'memoria_difensiva_detail',
    
    # Chat views
    'chat_caso',
    
    # AI utilities
    'analizza_caso'
]
