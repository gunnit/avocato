from django.shortcuts import render

def landing_view(request):
    """
    View for the AI-powered legal practice landing page.
    """
    return render(request, 'cases/landing.html')
