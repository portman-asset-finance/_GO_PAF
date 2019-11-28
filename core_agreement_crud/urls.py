
from django.urls import path

from . import views

app_name = 'core_agreement_crud'

urlpatterns = [
    path('customer/search', views.auto_complete, name='auto_complete'),
    path('agreementlist', views.AgreementEnquiryList, name='AgreementEnquiryList'),
    path('active', views.active, name='active'),
    path('scapegoat', views.scapegoat, name='scapegoat'),
    path('customer/<str:customer_number>', views.get_customer, name='get_customer'),
    path('agreement_management_tab1', views.agreement_management_tab1, name='agreement_management_tab1'),
    path('agreement_management_tab1_1/<str:current_agreement_id>', views.agreement_management_tab1_1, name='agreement_management_tab1_1'),
    path('agreement_management_tab2/<str:agreement_id>', views.agreement_management_tab2, name='agreement_management_tab2'),
    path('agreement_management_tab3/<str:agreement_id>', views.agreement_management_tab3, name='agreement_management_tab3'),
    path('agreement_management_tab4/<str:agreement_id>', views.agreement_management_tab4, name='agreement_management_tab4'),
    path('agreement_management_tab5/<str:agreement_id>', views.agreement_management_tab5, name='agreement_management_tab5'),
    path('<str:agreement_id>', views.AgreementManagementDetail, name='AgreementManagementDetail'),
    path('archive_agreement/<str:agreement_id>', views.archive_agreement, name='archive_agreement'),
    path('unarchive_agreement/<str:agreement_id>', views.unarchive_agreement, name='unarchive_agreement'),
    # TODO: PAF Changes - Start
    path('refund/<str:agreement_id>', views.refund, name='refund'),
    path('go_agreement_button_selector/', views.go_agreement_button_selector, name='go_agreement_button_selector'),
    # TODO: PAF Changes - End

]
