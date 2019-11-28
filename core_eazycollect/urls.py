
from django.urls import path

from . import views

app_name='core_eazycollect'


urlpatterns = [
    path('callback', views.callback, name='callback')
]

