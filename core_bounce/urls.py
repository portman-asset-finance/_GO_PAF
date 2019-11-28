from django.urls import path
from . import views

app_name='core_bounce'

urlpatterns = [
    path('process_bacs_files/', views.process_bacs_files, name='process_bacs_file'),
    path('process_datacash_files/', views.process_datacash_files, name='process_datacash_file')
]