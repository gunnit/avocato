from .models import StudioLegale

def studio_settings(request):
    """
    Add studio settings to template context globally
    """
    studio = StudioLegale.objects.first()
    return {'studio': studio}
