from django.db import models
from django.urls import reverse
import os

# Create your models here.
# Create a set of models that will be used to store pdf files for rpg systems. 
# Vectors created from those pdfs, 
# Publisher of the pdfs, 
# The base system, and license information for the pdfs.

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField(max_length=200)
    def __str__(self):
        return self.name
    
class License(models.Model):
    name = models.CharField(max_length=200)
    required_text = models.TextField()
    website = models.URLField(max_length=200)
    def __str__(self):
        return self.name

class BaseSystem(models.Model):
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=200)
    website = models.URLField(max_length=200)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Pdf(models.Model):
    uuid = models.UUIDField(primary_key=True)
    title = models.CharField(max_length=200)
    authors = models.CharField(max_length=200)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    license = models.ForeignKey(License, on_delete=models.CASCADE)
    base_system = models.ForeignKey(BaseSystem, on_delete=models.CASCADE)
    ordering = ['title', 'publisher']
    file = models.FileField(upload_to='pdfs/')

    def get_absolute_url(self):
        return reverse('pdf-detail', args=[str(self.uuid)])

    def __str__(self):
        return self.title + " by " + self.authors \
        + " from " + self.publisher.name + " for " \
        + self.base_system.name + " " + self.base_system.version \
        + " under " + self.license.name + " license"
    #def save(self, *args, **kwargs):
    #    if self.file:
    #        ### Generate a vector from the pdf file
    #        from llama_index import VectorStoreIndex, SimpleDirectoryReader
    #        documents = SimpleDirectoryReader('pdfs').load_data()
    #        ## When we add a new pdf, update the index
    #        models.PDF_INDEX = VectorStoreIndex('pdfs', documents)
    #
    #    super(Pdf, self).save(*args, **kwargs)
