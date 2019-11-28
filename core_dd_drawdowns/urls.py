from django.urls import path
from . import views

app_name='core_dd_drawdowns'

urlpatterns = [
    path('view', views.view_batches, name='view_batches'),
    path('view_batch_by_ref/<str:batch_ref>', views.view_batch_by_ref, name='view_batch_by_ref'),
    path('active', views.active, name='active'),
    path('view/<int:id>', views.view_batch, name='view_batch'),
    path('create/<str:due_date>', views.create_batch, name='create_batch'),
    path('submit/<str:batch_ref>', views.process_drawdowns, name='process_drawdowns'),
    path('update/<str:batch_ref>', views.update_call_date, name='update_call_date'),
    path('delete/<str:batch_ref>/<int:dd_id>', views.delete_drawdown, name='delete_drawdown'),
    path('delete_filtered/<str:batch_ref>', views.delete_drawdowns, name='delete_drawdowns'),
    path('soft_delete/<str:batch_ref>/<int:dd_id>', views.soft_delete_drawdown, name='soft_delete_drawdown'),
    path('soft_deletes/<str:batch_ref>', views.soft_delete_drawdowns, name='soft_delete_drawdowns'),
    path('re_add/<str:batch_ref>/<int:dd_id>', views.re_add_drawdown, name='re_add_drawdown'),
    path('re_adds/<str:batch_ref>', views.re_add_drawdowns, name='re_add_drawdowns'),
    path('unlock/<str:batch_id>', views.unlock_batch, name='unlock_batch'),
    path('archive/<str:batch_ref>', views.archive_batch, name='archive_batch')
]
