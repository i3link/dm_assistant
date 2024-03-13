from django.shortcuts import render

from .models import Pdf, BaseSystem, License, Publisher
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from llama_index.core.retrievers import RouterRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.tools import RetrieverTool
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.selectors import LLMMultiSelector


import json


from django.views import generic
import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    ServiceContext,
)
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from llama_index.core.callbacks.global_handlers import set_global_handler


import openai
import os
from django.shortcuts import render
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

set_global_handler("simple")

client = OpenAI()
openai.api_key = os.environ["OPENAI_API_KEY"]
PERSIST_DIR = "./storage"
SERVICE_CONTEXT = ServiceContext.from_defaults(
    llm=OpenAI(model="gpt-4"),
    )

if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    #DOCUMENTS = SimpleDirectoryReader(input_dir="pdfs", file_extractor={'.pdf2': PDF2Reader()}).load_data()
    DOCUMENTS = SimpleDirectoryReader("pdfs").load_data()
    PDF_INDEX = VectorStoreIndex.from_documents(DOCUMENTS, service_context=SERVICE_CONTEXT)
# store it for later
    PDF_INDEX.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    PDF_INDEX = load_index_from_storage(storage_context, service_context=SERVICE_CONTEXT)
    DOCUMENTS = SimpleDirectoryReader("pdfs").load_data()

NODES = SERVICE_CONTEXT.node_parser.get_nodes_from_documents(DOCUMENTS)
cohere_rerank = CohereRerank(api_key=os.environ["COHERE_API_KEY"], top_n=3)


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main object
    num_docs = Pdf.objects.all().count()
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # The 'all()' is implied by default.
    num_publishers = Publisher.objects.count()

    context = {
        'num_docs': num_docs,
        'num_publishers': num_publishers,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)
@login_required
def chatbot_view(request):
    """View function for search page of site."""
    
    # Render the HTML template chat.html with the data in the context variable
    if PDF_INDEX:
        memory = ChatMemoryBuffer.from_defaults(token_limit=10000)
        v_retriever = VectorIndexRetriever(PDF_INDEX, similarity_top_k=10)
        bm25_retriever = BM25Retriever.from_defaults(nodes=NODES, similarity_top_k=10)
        
        retriever_tools = [
           RetrieverTool.from_defaults(
               retriever=v_retriever,
               description="Useful nearly all the time.",
           ),
           RetrieverTool.from_defaults(
               retriever=bm25_retriever,
               description="Useful for very specific information about locations, items, characters, or npcs.",
           ),
        ]

        retriever = RouterRetriever.from_defaults(
           retriever_tools=retriever_tools,
           service_context=SERVICE_CONTEXT,
           select_multi=True,
           selector=LLMMultiSelector.from_defaults()
        )


        #response_synthesizer = get_response_synthesizer(response_mode="refine")
        
        chat_engine = ContextChatEngine(
            memory=memory,
            prefix_messages = [ChatMessage(role='system', content="""You are a chatbot, able to have normal interactions, as well as talk
                about any documents related to Pathfinder 2e and the Season of Ghosts adventure.  When you give an answer to a question, make sure to detail the response exactly, as the rules in pathfinder are complicated. 
                this explanation should include step by step instructions, and any relevant rules or tables.""")],
            retriever=retriever,
            llm=OpenAI(model="gpt-4"),
            #verbose=True,
            #response_synthesizer=response_synthesizer,
            node_postprocessors=[cohere_rerank],
        )
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
            response = chat_engine.chat(user_input)
            
            logger = logging.getLogger(__name__)
            logger.info(f"User inputted: {user_input} and chatbot replied: {response.response}")  
            
            # Extract chatbot replies from the response (TODO: let the chatbot reply with multiple messages at once)
            chatbot_response = response.response
            
            # Append chatbot replies to the conversation
            conversation.append({"role": "assistant", "content": chatbot_response})

            # Update the conversation in the session
            request.session['conversation'] = conversation

            return render(request, 'chat.html', {'user_input': user_input, 'chatbot_replies': chatbot_response, 'conversation': conversation})
        else:
            #request.session.clear()
            return render(request, 'chat.html', {'conversation': conversation})

@login_required
def chatbot_query_view(request):
    """View function for search page of site."""
    
    # Render the HTML template chat.html with the data in the context variable
    if PDF_INDEX:
        v_retriever = VectorIndexRetriever(PDF_INDEX)
        bm25_retriever = BM25Retriever.from_defaults(nodes=NODES, similarity_top_k=2)
        
        retriever_tools = [
            RetrieverTool.from_defaults(
                retriever=v_retriever,
                description="Useful in most cases",
            ),
            RetrieverTool.from_defaults(
                retriever=bm25_retriever,
                description="Useful if searching about specific information",
            ),
        ]
        retriever = RouterRetriever.from_defaults(
            retriever_tools=retriever_tools,
            service_context=SERVICE_CONTEXT,
            select_multi=True,
        )

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
            nodes = retriever.retrieve(user_input)
            results = []
            for node, score in nodes:
                #logging.warn(node.metadata)
                text_node = node[1]
                text_dict = text_node.to_dict()
                text_dict['score'] =  score
                results.append(json.dumps(text_dict))
                #logging.warn(text_node.text)
                #logging.warn(score)
            #logging.warn(dir(node))
            #logging.warn(nodes)
            
            logger = logging.getLogger(__name__)
            #logger.info(f"User inputted: {user_input} and chatbot replied: {nodes}")  
            
            # Extract chatbot replies from the response (TODO: let the chatbot reply with multiple messages at once)
            chatbot_responses = [result + "\n" for result in results]
            
            # Append chatbot replies to the conversation
            for chatbot_response in chatbot_responses:
                conversation.append({"role": "assistant", "content": chatbot_response})

            # Update the conversation in the session
            request.session['conversation'] = conversation

            return render(request, 'query.html', {'user_input': user_input, 'chatbot_replies': chatbot_responses, 'conversation': conversation})
        else:
            return render(request, 'query.html', {'conversation': conversation})

class PdfListView(LoginRequiredMixin, generic.ListView):
    model = Pdf
    paginate_by = 10

class PdfDetailView(LoginRequiredMixin, generic.DetailView):
    model = Pdf