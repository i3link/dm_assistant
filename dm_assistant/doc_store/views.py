from django.shortcuts import render

from .models import Pdf, BaseSystem, License, Publisher
from django.views import generic
from llama_index import VectorStoreIndex, SimpleDirectoryReader
import os
from django.shortcuts import render
from openai import ChatCompletion
import openai
from openai import OpenAI
import logging

openai.api_key = os.environ["OPENAI_API_KEY"]
client = OpenAI()
DOCUMENTS = SimpleDirectoryReader('pdfs').load_data()
PDF_INDEX = VectorStoreIndex.from_documents(DOCUMENTS)

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
            response = client.chat.completions.create(model="gpt-3.5-turbo",
            messages=prompts
            )
            logger = logging.getLogger(__name__)
            logger.warning(response)            
            # Extract chatbot replies from the response
            
            #chatbot_replies = [message['message']['content'] for message in response.choices if message['message']['role'] == 'assistant']
            chatbot_response = response.choices[0].message.content
            
            # Append chatbot replies to the conversation
            conversation.append({"role": "assistant", "content": chatbot_response})

            # Update the conversation in the session
            request.session['conversation'] = conversation

            return render(request, 'chat.html', {'user_input': user_input, 'chatbot_replies': chatbot_response, 'conversation': conversation})
        else:
            request.session.clear()
            return render(request, 'chat.html', {'conversation': conversation})
        
class PdfListView(generic.ListView):
    model = Pdf
    paginate_by = 10

class PdfDetailView(generic.DetailView):
    model = Pdf