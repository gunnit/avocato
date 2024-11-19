from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    """
    View for displaying and updating user profile
    """
    return render(request, 'cases/profile.html')
