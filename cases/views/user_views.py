from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import StudioLegale
import json

@login_required
def profile(request):
    """
    View for displaying and updating user profile
    """
    # Add studio to context for sidebar logo
    studio = StudioLegale.objects.first()
    
    if request.method == 'POST':
        # Handle form submission
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Update profile
        profile = user.profile
        profile.phone = request.POST.get('phone', '')
        profile.save()
        
        messages.success(request, 'Profilo aggiornato con successo.')
        
    return render(request, 'cases/profile.html', {'studio': studio})

@login_required
def configurazione_studio(request):
    """
    View for managing law firm settings and configuration
    """
    # Get or create studio settings
    studio, created = StudioLegale.objects.get_or_create(pk=1)  # Using pk=1 since we only need one instance

    if request.method == 'POST':
        # Handle form submission
        studio.nome = request.POST.get('studio_name', '')
        studio.indirizzo = request.POST.get('address_line1', '')
        studio.citta = request.POST.get('address_line2', '')
        studio.cap = request.POST.get('cap', '')
        studio.provincia = request.POST.get('province', '')
        studio.paese = request.POST.get('country', 'Italia')
        studio.email = request.POST.get('email', '')
        studio.telefono = request.POST.get('phone', '')
        studio.fax = request.POST.get('fax', '')
        
        # Handle specializations (multiple select)
        specializations = request.POST.getlist('specializations', [])
        studio.specializzazioni = json.dumps(specializations)
        
        # Handle AI settings
        studio.ai_suggestions_enabled = bool(request.POST.get('ai_suggestions', False))
        studio.ai_analysis_enabled = bool(request.POST.get('ai_analysis', False))
        studio.ai_templates_enabled = bool(request.POST.get('ai_templates', False))
        
        # Handle logo upload
        if request.FILES.get('logo'):
            studio.logo = request.FILES['logo']
        
        studio.save()
        messages.success(request, 'Le impostazioni sono state salvate con successo.')
    
    # Prepare context for template
    context = {
        'studio': studio,
        'specializations': json.loads(studio.specializzazioni) if studio.specializzazioni else []
    }
    
    return render(request, 'cases/configurazione_studio.html', context)
