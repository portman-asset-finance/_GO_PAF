from django.urls import path, re_path
from . import views

app_name='core_payments'

urlpatterns = [
    path('recordpayment', views.record_payment, name='record_payment'),
    path('<str:agreement_id>', views.payment_receipt_modal, name='payment_receipt_modal'),
    path('<str:agreement_id>/recordpaymentx', views.modal_record_payment, name='modal_record_payment'),
]