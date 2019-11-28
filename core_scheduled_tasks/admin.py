from django.contrib import admin

from .models import GoScheduler, GoSchedulerConfig, GoSchedulerLog


admin.site.register(GoScheduler)
admin.site.register(GoSchedulerLog)
admin.site.register(GoSchedulerConfig)
