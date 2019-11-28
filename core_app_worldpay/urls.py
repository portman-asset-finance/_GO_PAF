from django.urls import path
#from django.conf.urls import url
from core_app_worldpay import views

app_name='core_app_worldpay'

urlpatterns = [
    path('worldpay', views.worldpay, name='worldpay'),
    path('worldpay_charge', views.worldpay_charge, name='worldpay_charge'),
#    path('test_help', views.test_help, name='test_help'),
 #   path('complete', views.test_help, name='test_help'),
#    url(r'^$', views.main, name='index'),
 #   url(r'^auth', views.auth, name='charges'),
]