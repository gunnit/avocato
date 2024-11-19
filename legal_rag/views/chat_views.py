import json
import requests
import tempfile
import os
from typing import List
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings
from PyPDF2 import PdfReader

class RagSystem:
    """RAG system implementation"""
    def __init__(self):
        self.qa_chain = None
        self.chat_history = []
        self.vectorstore = None
        self.pdf_urls = [
            "https://www.studiocataldi.it/codicepenale/codicepenale.pdf",
        ]

    def initialize_system(self):
        """Initialize the RAG system with PDF content"""
        try:
            # Extract text from PDFs
            all_text = ""
            for url in self.pdf_urls:
                all_text += self._get_pdf_text(url)

            # Split text into smaller chunks for more precise matching
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # Smaller chunks for more precise matching
                chunk_overlap=100,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            chunks = text_splitter.split_text(all_text)

            # Create embeddings and vector store
            embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            self.vectorstore = Chroma.from_texts(chunks, embeddings)

            # Initialize Anthropic model with latest configuration
            llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=0,
                max_tokens=1024,
                anthropic_api_key=settings.ANTHROPIC_API_KEY
            )

            # Create conversational chain
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}  # Retrieve more chunks for better context
                ),
                return_source_documents=True,
                verbose=True
            )

        except Exception as e:
            print(f"Error initializing system: {str(e)}")
            raise

    def _get_pdf_text(self, pdf_url: str) -> str:
        """Download and extract text from PDF"""
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            text = ""
            with open(temp_file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()

            os.unlink(temp_file_path)
            return text
        except Exception as e:
            print(f"Error processing PDF {pdf_url}: {str(e)}")
            return ""

    def _check_relevance(self, query: str) -> bool:
        """Check if the query is relevant to the document content"""
        try:
            # Get relevant documents and their scores
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=3)
            
            # More lenient threshold for relevance
            return any(score > 0.3 for _, score in docs_and_scores)
        except Exception as e:
            print(f"Error checking relevance: {str(e)}")
            return True  # Default to allowing the query if check fails

    def process_message(self, message: str) -> str:
        """Process a user message and return the response"""
        try:
            # Initialize system if needed
            if self.qa_chain is None:
                self.initialize_system()

            # First check if the question is relevant to our document
            if not self._check_relevance(message):
                return ("Mi dispiace, ma la tua domanda non sembra essere correlata al contenuto del Codice Penale Italiano. "
                       "Posso rispondere solo a domande su argomenti specificamente trattati in questo documento legale. "
                       "Per favore, fai una domanda sul contenuto del Codice Penale Italiano.")

            # Format message for Claude with very strict instructions
            system_message = """ISTRUZIONI IMPORTANTI:
            1. Sei un assistente legale specializzato che risponde ESCLUSIVAMENTE a domande basate sul documento del Codice Penale Italiano fornito.
            2. NON devi MAI fornire informazioni al di fuori di questo specifico documento.
            3. NON devi MAI fare supposizioni o interpretazioni oltre a quanto esplicitamente dichiarato nel documento.
            4. Se la risposta esatta non si trova nel documento, rispondi con: "Questa informazione specifica non è presente nel documento del Codice Penale Italiano."
            5. Cita sempre gli articoli, le sezioni o i paragrafi specifici del documento nelle tue risposte.
            6. Non intraprendere discussioni legali generali o fornire informazioni da altre fonti.
            7. Se ti viene chiesto qualcosa al di fuori del Codice Penale Italiano, rispondi che puoi rispondere solo a domande su questo specifico documento.
            8. TUTTE LE RISPOSTE DEVONO ESSERE IN ITALIANO."""

            # Get response from RAG system using invoke()
            response = self.qa_chain.invoke({
                "question": message,
                "chat_history": self.chat_history,
                "system_message": system_message
            })

            # Verify the response contains relevant source documents
            if not response.get('source_documents'):
                return ("Non riesco a trovare informazioni specifiche su questo nel documento del Codice Penale Italiano. "
                       "Per favore, fai una domanda sul contenuto che è esplicitamente trattato nel documento.")

            # Add a reminder about the source of information
            answer = response['answer']
            answer += "\n\nNota: Questa risposta è basata esclusivamente sul contenuto del Codice Penale Italiano."

            # Update chat history
            self.chat_history.append((message, answer))

            return answer

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            raise

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

        response = rag_system.process_message(message)
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
