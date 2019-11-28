from django.urls import path
from . import views

app_name='core_sage_export'

urlpatterns = [
    path('view', views.view_batches, name='view_batches'),
    path('unlock/<str:sage_batch_ref>', views.unlock_batch, name='unlock_batch'),
    path('batch/<str:sage_batch_ref>', views.view_batch, name='view_batch'),
    path('sage_xlsx/<str:sage_batch_ref>', views.sage_xlsx, name='sage_xlsx'),
    path('details/<str:sage_batch_ref>', views.view_details, name='view_details'),
    path('process_batch/<str:sage_batch_ref>', views.process_batch, name='process_batch'),
    path('split_transaction/<str:transaction_id>', views.split_transaction, name='split_transaction'),
    path('split_transactions/<str:sage_batch_ref>', views.split_transactions, name='split_transactions'),
]