from django.shortcuts import render

from .models import Pdf, BaseSystem, License, Publisher
from django.views import generic
import os.path
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
import os
from django.shortcuts import render
import openai
from openai import OpenAI
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

openai.api_key = os.environ["OPENAI_API_KEY"]
client = OpenAI()
PERSIST_DIR = "./storage"

if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    DOCUMENTS = SimpleDirectoryReader("pdfs").load_data()
    PDF_INDEX = VectorStoreIndex.from_documents(DOCUMENTS)
    # store it for later
    PDF_INDEX.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    PDF_INDEX = load_index_from_storage(storage_context)

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main object
    num_docs = Pdf.objects.all().count()

    # The 'all()' is implied by default.
    num_publishers = Publisher.objects.count()

    context = {
        'num_docs': num_docs,
        'num_publishers': num_publishers,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

def chatbot_view(request):
    """View function for search page of site."""
    # Render the HTML template search.html with the data in the context variable
    if PDF_INDEX:
        chat_engine = PDF_INDEX.as_chat_engine(streaming=True)
        ## We have an active index, so let's use it to help us chat with the user!
        conversation = request.session.get('conversation', [])

        if request.method == 'POST':
            user_input = request.POST.get('user_input')

            # Define your chatbot's predefined prompts
            prompts = []

            # Append user input to the conversation
            if user_input:
                conversation.append({"role": "user", "content": user_input})

            # Append conversation messages to prompts
            prompts.extend(conversation)

            # Set up and invoke the ChatGPT model
            response = chat_engine.query(user_input)
            
            logger = logging.getLogger(__name__)
            logger.info(f"User inputted: {user_input} and chatbot replied: {response.response}")  
            
            # Extract chatbot replies from the response (TODO: let the chatbot reply with multiple messages at once)
            chatbot_response = response.response
            
            # Append chatbot replies to the conversation
            conversation.append({"role": "assistant", "content": chatbot_response})

            # Update the conversation in the session
            request.session['conversation'] = conversation

            logger.warn({'user_input': user_input, 'chatbot_replies': chatbot_response, 'conversation': conversation})

            return render(request, 'chat.html', {'user_input': user_input, 'chatbot_replies': chatbot_response, 'conversation': conversation})
        else:
            request.session.clear()
            return render(request, 'chat.html', {'conversation': conversation})
        
class PdfListView(generic.ListView):
    model = Pdf
    paginate_by = 10

class PdfDetailView(generic.DetailView):
    model = Pdf