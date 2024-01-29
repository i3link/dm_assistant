from django.contrib import admin
from .models import Publisher, Pdf, License, BaseSystem 

admin.site.register(Publisher)
admin.site.register(Pdf)
admin.site.register(License)
admin.site.register(BaseSystem)
