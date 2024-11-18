from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Caso, ChatMessage
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

def chat_caso(request, caso_id):
    caso = get_object_or_404(Caso, id=caso_id)
    chat_messages = caso.chat_messages.all()

    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Save user message
            ChatMessage.objects.create(
                caso=caso,
                content=user_message,
                is_ai=False
            )

            try:
                client = anthropic.Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
                
                # Create context from case details
                context = f"""
                Dettagli del caso:
                Titolo: {caso.titolo}
                Descrizione: {caso.descrizione}
                Analisi AI: {caso.analisi_ai}
                Riferimenti Legali: {caso.riferimenti_legali}
                """

                # Get chat history
                chat_history = "\n".join([
                    f"{'Assistant' if msg.is_ai else 'Human'}: {msg.content}"
                    for msg in chat_messages
                ])

                # Create the prompt with context and history
                prompt = f"""
                {context}

                Cronologia chat:
                {chat_history}

                Human: {user_message}

                Rispondi come un assistente legale esperto, fornendo informazioni accurate e pertinenti basate sul contesto del caso.
                """

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Save AI response
                ChatMessage.objects.create(
                    caso=caso,
                    content=response.content[0].text,
                    is_ai=True
                )

            except Exception as e:
                messages.error(request, f'Errore durante la generazione della risposta: {str(e)}')

    return render(request, 'cases/chat.html', {
        'caso': caso,
        'messages': caso.chat_messages.all()
    })
