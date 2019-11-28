from django.urls import path
from . import views

app_name='core_companies_house'

urlpatterns = [
    path('companies_house', views.companies_house, name='companies_house'),
    path('update', views.update_companies_house, name='update_companies_house'),
    path('count', views.active_companies_house, name='active_companies_house')
]