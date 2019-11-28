from django.contrib import admin


from .models import RequestType, RequestSet, RequestLog, RequestParameter, CompanyHouse_CompanyProfile


admin.site.register(RequestLog)
admin.site.register(RequestSet)
admin.site.register(RequestType)
admin.site.register(RequestParameter)
admin.site.register(CompanyHouse_CompanyProfile)