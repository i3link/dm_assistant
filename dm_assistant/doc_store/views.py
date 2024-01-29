from django.shortcuts import render

from .models import Pdf, BaseSystem, License, Publisher
from django.views import generic


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

class PdfListView(generic.ListView):
    model = Pdf
    paginate_by = 10

class PdfDetailView(generic.DetailView):
    model = Pdf