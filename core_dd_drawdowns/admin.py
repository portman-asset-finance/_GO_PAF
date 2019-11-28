from django.contrib import admin

from .models import DrawDown, BatchHeaders, StatusDefinition, BatchLock

admin.site.register(DrawDown)
admin.site.register(BatchLock)
admin.site.register(BatchHeaders)
admin.site.register(StatusDefinition)
