import json
import time
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from openai import OpenAI

class RagSystem:
    """RAG system implementation using OpenAI Assistant"""
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = "asst_xT2TnzkEZcvDDMRKnEcSshvX"

    def initialize_system(self, request):
        """Initialize the system by creating a new thread"""
        try:
            # Create a new thread for this session if not exists
            if 'thread_id' not in request.session:
                thread = self.client.beta.threads.create()
                request.session['thread_id'] = thread.id
            return True
        except Exception as e:
            print(f"Error initializing system: {str(e)}")
            return False

    def process_message(self, request, message: str) -> str:
        """Process a user message and return the response"""
        try:
            # Initialize system if needed
            if 'thread_id' not in request.session:
                success = self.initialize_system(request)
                if not success:
                    return "Si è verificato un errore durante l'inizializzazione del sistema."

            thread_id = request.session['thread_id']

            # Add the user's message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            # Run the assistant on the thread
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Wait for the run to complete with timeout
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while True:
                if time.time() - start_time > timeout:
                    return "Timeout durante l'elaborazione della richiesta."
                
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    return "Si è verificato un errore durante l'elaborazione della richiesta."
                
                time.sleep(1)  # Wait 1 second between checks

            # Get the assistant's response
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            # Get the latest assistant message
            for msg in messages.data:
                if msg.role == "assistant":
                    response = msg.content[0].text.value
                    return response

            return "Non è stato possibile ottenere una risposta."

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return "Si è verificato un errore durante l'elaborazione della richiesta."

# Create a single instance of the RAG system
rag_system = RagSystem()

@login_required
@csrf_protect
@require_http_methods(["POST"])
def chat_view(request):
    """Handle chat requests"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()

        if not message:
            return JsonResponse({
                'error': 'È necessario inserire un messaggio'
            }, status=400)

        response = rag_system.process_message(request, message)
        return JsonResponse({'response': response})

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Dati JSON non validi'
        }, status=400)
    except Exception as e:
        print(f"Error in chat_view: {str(e)}")
        return JsonResponse({
            'error': 'Si è verificato un errore durante l\'elaborazione della richiesta'
        }, status=500)
