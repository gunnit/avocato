from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import json
import anthropic
from .ai_utils import analyze_document, extract_text_from_pdf
from django.conf import settings
from ..models import Caso, DocumentaryEvidence

@login_required
def documentary_evidence_list(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    documents = caso.documentary_evidences.all().order_by('exhibit_number')
    return render(request, 'cases/documentary_evidence_list.html', {
        'caso': caso,
        'documents': documents
    })

@login_required
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
            document_type=request.POST.get('document_type', 'altro'),
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

@login_required
def documentary_evidence_edit(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    if request.method == 'POST':
        document.title = request.POST.get('title')
        document.description = request.POST.get('description')
        document.document_type = request.POST.get('document_type', 'altro')
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

@login_required
def documentary_evidence_detail(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    # Pass the existing analysis to the template if available
    initial_analysis = document.ai_analysis_json if document.ai_analysis_json else None
    
    return render(request, 'cases/documentary_evidence_detail.html', {
        'caso': caso,
        'document': document,
        'initial_analysis': json.dumps(initial_analysis) if initial_analysis else 'null'
    })

@login_required
@require_http_methods(["POST"])
@csrf_protect
def analyze_evidence(request, caso_id, doc_id):
    from .ai_utils import analyze_document
    
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    # Check if analysis already exists
    if document.ai_analysis_json is not None:
        return JsonResponse(document.ai_analysis_json)
    
    try:
        # Get analysis from AI utils
        analysis = analyze_document(document)
        
        # Save both JSON and text versions
        document.ai_analysis_json = analysis
        document.ai_analysis_text = json.dumps(analysis)
        document.save()
        
        return JsonResponse(analysis)
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to analyze document",
            "details": str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_protect
def extract_text(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    try:
        # Extract text using AI utils
        extracted_text = extract_text_from_pdf(document)
        
        # Save the extracted text
        document.extracted_text = extracted_text
        document.save()
        
        return JsonResponse({
            "success": True,
            "message": "Text extracted successfully",
            "text": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text  # Preview only
        })
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to extract text from document",
            "details": str(e)
        }, status=500)
