from django.contrib import admin

from .models import SageBatchHeaders, SageBatchTransactions, SageBatchLock

admin.site.register(SageBatchHeaders)
admin.site.register(SageBatchTransactions)
admin.site.register(SageBatchLock)
