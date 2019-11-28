from django.contrib import admin

from .models import LazyBatchConfig, LazyBatchLog

admin.site.register(LazyBatchLog)
admin.site.register(LazyBatchConfig)
