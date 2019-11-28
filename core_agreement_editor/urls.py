from django.urls import path, re_path
from . import views

app_name='core_agreement_editor'

urlpatterns = [
    path('editors/', views.editor_list, name='editor_list'),
    # path('', views.editor_list, name='editor_list'),
    path('editors/update_or_create/<str:agreement_id>', views.update_or_create, name='update_or_create'),
    path('editors/create/<str:agreement_id>', views.editor_create, name='editor_create'),
    path('editors/create/', views.editor_create_list, name='editor_create_list'),
    re_path(r'^editors/(?P<pk>\d+)/update/$', views.editor_update, name='editor_update'),
    re_path(r'^editors/(?P<pk>\d+)/delete/$', views.editor_delete, name='editor_delete'),
    path('editor_within_agreement/<str:agreement_id>', views.editor_within_agreement, name='editor_within_agreement'),
    path('editors/modalchangedate/<str:agreement_id>', views.modalchangedate, name='modalchangedate'),
    path('editors/modalchangefees/<str:agreement_id>', views.modalchangefees, name='modalchangefees'),
    path('editors/modalchangevalues/<str:agreement_id>', views.modalchangevalues, name='modalchangevalues'),
    path('editors/modalsettlement/<str:agreement_id>', views.modalsettlement, name='modalsettlement'),
    path('editors/modalglobaltermination/<str:agreement_id>', views.modalglobal_termination, name='modalglobal_termination'),
    path('editors/modalconsolidate/<str:agreement_id>', views.modalconsolidate, name='modalconsolidate'),
    path('editors/modalaccountinfo/<str:agreement_id>', views.modalaccountinfo, name='modalaccountinfo'),
    path('editors/agreement_detail/<str:agreement_id>', views.agreement_detail, name='agreement_detail'),
    path('print_pdf_EARLY_SETTLEMENT/<str:agreement_id>', views.print_pdf_EARLY_SETTLEMENT, name='print_pdf_EARLY_SETTLEMENT'),
    path('editors/remove_consolidation_agreement/<str:agreement_id>', views.remove_consolidation_agreement, name='remove_consolidation_agreement')
    # path('print_pdf_EARLY_SETTLEMENT/<str:agreement_id>/<str:arrears_total_collected>', views.print_pdf_EARLY_SETTLEMENT, name='print_pdf_EARLY_SETTLEMENT'),
]