from django.urls import path, re_path
from . import views

app_name='core_agreement_notice'

urlpatterns = [
    path('notices/', views.notice_list, name='notice_list'),
    # path('', views.notice_list, name='notice_list'),
    path('notices/update_or_create/<str:agreement_id>', views.update_or_create, name='update_or_create'),
    path('notices/create/<str:agreement_id>', views.notice_create, name='notice_create'),
    path('notices/create/', views.notice_create_list, name='notice_create_list'),
    re_path(r'^notices/(?P<pk>\d+)/update/$', views.notice_update, name='notice_update'),
    re_path(r'^notices/(?P<pk>\d+)/delete/$', views.notice_delete, name='notice_delete'),
    path('notice_within_agreement/<str:agreement_id>', views.notice_within_agreement, name='notice_within_agreement'),
]