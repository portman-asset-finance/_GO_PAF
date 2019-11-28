from django.urls import path

from . import views

app_name='core_direct_debits'

urlpatterns = [
    path('get-history/<agreement_no>', views.get_dd_history, name='get_dd_history'),
    path('create/<agreement_no>', views.create_new_dd_instruction, name='create_new_dd_instruction'),
    path('cancel/<int:dd_history_id>', views.cancel_dd_instruction, name='cancel_ddi')
]
