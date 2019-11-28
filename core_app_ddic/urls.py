from django.urls import path
from . import views

app_name='core_app_ddic'

urlpatterns = [
    path('ddic', views.ddic, name='ddic'),
    path('update', views.update_ddic, name='update_ddic'),
    path('count', views.active_ddic, name='active_ddic')
]