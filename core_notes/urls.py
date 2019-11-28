from django.urls import path

from . import views

app_name='notes'

urlpatterns = [
    path('contact', views.create_or_update_contact, name='create_or_update_contact'),
    path('contact/<int:contact_id>', views.manage_contact, name='manage_contact'),
    path('', views.main, name='main'),
    path('<int:note_id>', views.note, name='note'),
    path('types', views.type, name='type'),
    path('asset', views.upload_asset, name='upload_asset'),
    path('asset/<asset_id>', views.asset, name='asset'),
    path('<customer_id>', views.main, name='main'),
    path('<customer_id>/<agreement_id>', views.main, name='main')
]

