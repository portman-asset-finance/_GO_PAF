from django.urls import path
from . import views

app_name='dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
	path('agreementlist', views.AgreementEnquiryList, name='AgreementEnquiryList'),
	path('ddforecastlist', views.DDForecastList, name='DDForecastList'),
    path('dd_forecast_xlsx/<str:input_date>', views.dd_forecast_xlsx, name='dd_forecast_xlsx'),
    path('paymentprofile_xlsx/<str:agreement_id>', views.paymentprofile_xlsx, name='paymentprofile_xlsx'),
    path('sage_xlsx/<str:agreement_id>', views.sage_xlsx, name='sage_xlsx'),
    path('paymentprofile_gross_xlsx/<str:agreement_id>', views.paymentprofile_gross_xlsx, name='paymentprofile_gross_xlsx'),
    path('statement_of_account_xlsx/<str:agreement_id>', views.statement_of_account_xlsx, name='statement_of_account_xlsx'),
    path('statement_of_account_allocated_xlsx/<str:agreement_id>', views.statement_of_account_allocated_xlsx,
            name='statement_of_account_allocated_xlsx'),
    path('<str:agreement_id>', views.AgreementEnquiryDetail, name='AgreementEnquiryDetail'),
    path('convert/<str:agreement_id>', views.convert_to_go, name='convert_to_go'),
    path('convert/sentinel/<str:agreement_id>', views.convert_to_sentinel, name='convert_to_sentinel'),

    path('print_pdf_CURRENT_VAT_STATEMENT_view/<str:agreement_id>', views.print_pdf_CURRENT_VAT_STATEMENT_view,
         name='print_pdf_CURRENT_VAT_STATEMENT_view'),
    path('print_pdf_NEXT_VAT_STATEMENT_view/<str:agreement_id>', views.print_pdf_NEXT_VAT_STATEMENT_view,
         name='print_pdf_NEXT_VAT_STATEMENT_view'),

    path('pdf_CURRENT_VAT_STATEMENT_view/<str:agreement_id>', views.pdf_CURRENT_VAT_STATEMENT_view,
         name='pdf_CURRENT_VAT_STATEMENT_view'),
    path('pdf_NEXT_VAT_STATEMENT_view/<str:agreement_id>', views.pdf_NEXT_VAT_STATEMENT_view,
         name='pdf_NEXT_VAT_STATEMENT_view'),

    # Card 72 Multiple year VAT Statements
    path('print_pdf_FULL_VAT_STATEMENT/<str:agreement_id>', views.print_pdf_FULL_VAT_STATEMENT, name='print_pdf_FULL_VAT_STATEMENT'),
    path('print_pdf_STATEMENT_OF_ACCOUNT/<str:agreement_id>', views.print_pdf_STATEMENT_OF_ACCOUNT, name='print_pdf_STATEMENT_OF_ACCOUNT'),
    path('print_pdf_EARLY_SETTLEMENT/<str:agreement_id>', views.print_pdf_EARLY_SETTLEMENT, name='print_pdf_EARLY_SETTLEMENT'),
    path('print_pdf_TEMPLATE_TERMINATION/<str:agreement_id>', views.print_pdf_TEMPLATE_TERMINATION, name='print_pdf_TEMPLATE_TERMINATION'),
    path('print_pdf_ARREARS_LETTER/<str:agreement_id>', views.print_pdf_ARREARS_LETTER, name='print_pdf_ARREARS_LETTER'),
    path('print_pdf_ARREARS_RECEIVER_LETTER/<str:agreement_id>', views.print_pdf_ARREARS_RECEIVER_LETTER, name='print_pdf_ARREARS_RECEIVER_LETTER'),
]