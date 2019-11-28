from django.contrib import admin

from .models import Note, Type, Asset

admin.site.register(Note)
admin.site.register(Type)
admin.site.register(Asset)
