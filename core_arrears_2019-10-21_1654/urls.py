from django.urls import path, re_path
from . import views

app_name='core_arrears'

urlpatterns = [
    path('', views.arrears_by_agreement_view, name='arrears_by_agreement_view'),
    path('arrears_by_duedate', views.arrears_by_duedate_view, name='arrears_by_duedate_view'),
    path('change_target_agent', views.change_target_agent, name='change_target_agent'),
    path('<str:agreement_id>', views.arrears_by_arrears_summary_view, name='arrears_by_arrears_summary_view'),
    path('<str:ara_agreement_id>/<str:ara_arrears_id>/update', views.arrear_update, name='arrear_update'),
    path('<str:ras_agreement_id>/<str:ras_arrears_id>/<str:ras_allocation_id>/update',
                                views.arrear_receipt_view, name='arrear_receipt_view'),

]