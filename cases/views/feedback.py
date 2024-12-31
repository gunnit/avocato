from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Feedback

@login_required
def feedback_form(request):
    if request.method == 'POST':
        oggetto = request.POST.get('oggetto')
        messaggio = request.POST.get('messaggio')
        
        Feedback.objects.create(
            utente=request.user,
            oggetto=oggetto,
            messaggio=messaggio
        )
        
        messages.success(request, 'Grazie per il tuo feedback!')
        return redirect('feedback_form')
        
    return render(request, 'cases/feedback_form.html')
