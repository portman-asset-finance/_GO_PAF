"""_go_base URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core_dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', views.signinView, name='index'),
    path('dashboard/', include('core_dashboard.urls')),
    path('core_agreement_crud/', include('core_agreement_crud.urls')),
    path('core_agreement_editor/', include('core_agreement_editor.urls')),
    path('core_agreement_notice', include('core_agreement_notice.urls')),
    path('core_dd_drawdowns/', include('core_dd_drawdowns.urls')),
    path('core_direct_debits/', include('core_direct_debits.urls')),
    path('core_app_ddic/', include('core_app_ddic.urls')),
    path('core_app_worldpay/', include('core_app_worldpay.urls')),
    path('notes/', include('core_notes.urls')),
    path('core_arrears/', include('core_arrears.urls')),
    path('core_payments/', include('core_payments.urls')),
    path('core_sage_export/', include('core_sage_export.urls')),
    path('account/login/', views.signinView, name='signin'),
    path('account/logout/', views.signoutView, name='signout'),
    path('core_bounce/', include('core_bounce.urls')),
    path('core_eazycollect/', include('core_eazycollect.urls')),
    path('core_companies_house/', include('core_companies_house.urls')),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
	urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
