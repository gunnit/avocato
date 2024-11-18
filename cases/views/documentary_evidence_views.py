from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max
from ..models import Caso, DocumentaryEvidence

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
