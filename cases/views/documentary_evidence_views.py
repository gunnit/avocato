from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import json
import anthropic
from django.conf import settings
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

@require_http_methods(["POST"])
@csrf_protect
def analyze_evidence(request, caso_id, doc_id):
    caso = get_object_or_404(Caso, id=caso_id)
    document = get_object_or_404(DocumentaryEvidence, id=doc_id, caso=caso)
    
    # Prepare the prompt for Claude analysis
    prompt = f"""Analyze the following legal evidence as a lawyer. Consider reliability, legal implications, and strategic value:

Title: {document.title}
Description: {document.description}
Authentication Status: {document.authentication_status}
Authentication Notes: {document.authentication_notes}

Provide a detailed analysis in JSON format with the following structure:
{{
    "key_information": {{
        "document_type": "",
        "date_references": [],
        "key_parties": [],
        "main_facts": []
    }},
    "legal_analysis": {{
        "reliability_assessment": "",
        "potential_challenges": [],
        "authentication_concerns": "",
        "evidentiary_value": ""
    }},
    "strategic_considerations": {{
        "strengths": [],
        "weaknesses": [],
        "recommended_actions": [],
        "potential_counterarguments": []
    }},
    "risk_assessment": {{
        "credibility_risks": [],
        "legal_risks": [],
        "strategic_risks": []
    }},
    "recommendations": {{
        "immediate_actions": [],
        "long_term_strategy": "",
        "additional_evidence_needed": []
    }}
}}

Return ONLY the JSON object, without any additional text or explanation."""

    try:
        # Initialize Anthropic client
        client = anthropic.Client(api_key=settings.ANTHROPIC_API_KEY)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.7,
            system="You are an experienced legal analyst. Analyze the evidence and return ONLY a JSON object without any additional text.",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Get the response content
        content = response.content[0].text
        
        # Try to parse the JSON response
        try:
            analysis = json.loads(content)
            return JsonResponse(analysis)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            # Look for the first { and last } to extract just the JSON part
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                analysis = json.loads(json_str)
                return JsonResponse(analysis)
            else:
                raise Exception("Could not extract valid JSON from response")
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to analyze document",
            "details": str(e)
        }, status=500)
