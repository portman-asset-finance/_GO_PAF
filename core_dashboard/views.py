# Django Imports
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.http import HttpResponse

# Python Imports
import decimal, io, datetime, pytz

# Third Party Imports
from dateutil.relativedelta import *
from xlsxwriter.workbook import Workbook
#JC Additions
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, Frame, BaseDocTemplate, PageTemplate, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from reportlab.pdfgen import canvas
from xlsxwriter.workbook import Workbook
import decimal, datetime
import random
from datetime import timedelta

from core_dd_drawdowns.models import DrawDown


from core_agreement_crud.models import  go_agreement_querydetail, \
                                        go_customers, \
                                        go_account_transaction_summary, \
                                        go_account_transaction_detail


from core.models import go_extensions, \
                        ncf_dd_schedule, \
                        ncf_datacash_drawdowns, \
                        ncf_dd_audit_log, \
                        ncf_regulated_agreements


from .filters import go_agreement_querydetail_Filter, \
                     go_account_transaction_summary_Filter

from core_agreement_crud.models import go_agreement_index

from .functions import convert_to_go_agreement, convert_back_to_sentinal
from .print_vat_statements_pdf import PrintVatStatement


# Convert To Go Agreement
# -----------------------
@login_required(login_url='signin')
def convert_to_go(request, agreement_id):
    if request.method == 'POST':
        if convert_to_go_agreement(agreement_id, request.user):
            return redirect('core_agreement_crud:agreement_management_tab4', agreement_id=agreement_id)
    return AgreementEnquiryDetail(request, agreement_id)


# Convert To Sentinel Agreement
# -----------------------------
@login_required(login_url='signin')
def convert_to_sentinel(request, agreement_id):
    if request.method == 'POST':
        convert_back_to_sentinal(agreement_id, request.user)
    return AgreementEnquiryDetail(request, agreement_id)


# Dashboard
# ---------
@login_required(login_url="signin")
def dashboard(request):
    healthy = True
    valid_bacsrun = True
    valid_bounce01 = True
    valid_bounce02 = True
    today = datetime.date.today()

    # Process General Health Indicators
    extensions = go_extensions.objects.filter(ap_extension_active=True, ap_extension_next_interface_run__isnull=False)
    for extension in extensions:
        if datetime.date.today() >= extension.ap_extension_next_interface_run.date():
            healthy = False

    # Process DD Schedule and Bounce Day Indicators
    dd_current = ncf_dd_schedule.objects.get(dd_status=999)
    dd_calendar_items = ncf_dd_schedule.objects.filter(dd_status__in=[999, 922])
    dd_current_due_date = ncf_datacash_drawdowns.objects.filter(dd_due_date=dd_current.dd_calendar_due_date).exists()
    dd_extensions = go_extensions.objects.filter(ap_extension_active=True,
                                                   ap_extension_next_interface_run__isnull=True)

    for dd_extension in dd_extensions:

        if dd_extension.ap_extension_code == 'bacsrun':
            if not dd_current_due_date and today > dd_current.dd_call_date:
                healthy = False
                valid_bacsrun = False

        if dd_extension.ap_extension_code == 'bounceday1':
            if (today > dd_current.dd_bounce_date01) and \
                    (dd_extension.ap_extension_last_interface_run.date() < dd_current.dd_bounce_date01):
                healthy = False
                valid_bounce01 = False

        if dd_extension.ap_extension_code == 'bounceday2':
            if (today > dd_current.dd_bounce_date02) and \
                    (dd_extension.ap_extension_last_interface_run.date() < dd_current.dd_bounce_date01):
                healthy = False
                valid_bounce02 = False


    return render(request, 'dashboard/dashboard_home.html', {'extensions':extensions,
                                                             'dd_extensions':dd_extensions,
                                                             'dd_current':dd_current,
                                                             'dd_calender_items':dd_calendar_items,
                                                             'healthy':healthy,
                                                             'valid_bacsrun':valid_bacsrun,
                                                             'valid_bounce01':valid_bounce01,
                                                             'valid_bounce02': valid_bounce02,
                                                             'today':today})


# Agreement Enquiry Screens
# -------------------------
@login_required(login_url="signin")
def AgreementEnquiryList(request):
    agreement_extract = go_agreement_querydetail.objects.all()
    agreement_list = go_agreement_querydetail_Filter(request.GET, queryset=agreement_extract)
    agreement_index_extract = go_agreement_index.objects.all()
    # go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    paginator = Paginator(agreement_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') or request.GET.get('customercompany') \
                 or request.GET.get('agreementauthority') or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')

    request.session['arrears_by_arrears_return_querystring'] = {}
    request.session['arrears_by_arrears_return_querystring'] = request.get_full_path()

    return render(request, 'dashboard/dashboard_agreement_enquiry_list.html', {'agreement_list':agreement_list,
                                                                       'agreement_list_qs': pub,
                                                                        'has_filter': has_filter})


@login_required(login_url="signin")
def AgreementEnquiryDetail_save_20190805(request, agreement_id):

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)\
                        .order_by('transtypedesc',)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id).order_by('transactiondate', 'transactionsourceid')
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False) \
                                                                                .order_by('transtypedesc', )
    bacs_audit = ncf_dd_audit_log.objects.filter(da_agreement_id=agreement_id)\
                                            .order_by('-da_effective_date', 'da_source')

    # Get Regulated Status
    agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=agreement_id).exists()
    if agreement_regulated:
        agreement_regulated_flag = True
    else:
        agreement_regulated_flag = False

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    # Agreement Payable Net of VAT
    try:
        agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        agreement_payable_net = 0

    # Add in Fees if they exist
    try:
        agreement_fees_net = account_detail_fees.aggregate(Sum('transnetpayment'))
        if agreement_fees_net is not None:
            agreement_payable_net += agreement_fees_net["transnetpayment__sum"]
    except:
        agreement_fees_net = None
        agreement_payable_net = 0
        pass

    # Agreement Payable Gross of VAT
    agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

    # Agreement Instalment Gross
    agreement_instalment_gross = agreement_detail.agreementinstalmentnet
    if agreement_detail.agreementinstalmentvat  is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    # Sundry Items
    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    if agreement_type == 'Lease':
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    else:
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=first_rental_date) \
                                                                            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                          transactionsourceid__in=['SP1', 'GO1'],
                                                                          transtypeid__isnull=True,
                                                                          transactiondate__gte=first_rental_date)\
                                                                          .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0


    # Add Gross of Vat to account summary queryset
    # row_index = 0
    # for row in account_summary:
    #     row.transvatpayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
    #     if row.transactionsourceid in ['SP1', 'SP2', 'SP3', 'GO1', 'GO3']:
    #         if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
    #             row_index += 1
    #     row.row_index = row_index
    #
    # # Add Gross of Vat to account detail queryset
    # for row in account_detail:
    #     row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    row_index = 0
    for row in account_summary:
        # if row.transactionsourceid in ['GO8','GO9', 'SP9'] and row.transvatpayment is not None:
        if row.transactionsourceid in ['GO8','GO9', 'SP9']:
            # row.transgrosspayment = row.transnetpayment + row.transvatpayment
            row.transgrosspayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
        else:
            row.transgrosspayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
        if row.transactionsourceid in ['GO1', 'GO2', 'GO3', 'SP1', 'SP2', 'SP3']:
            if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
                row_index += 1
        row.row_index = row_index

    # Add Gross of Vat to account detail queryset
    for row in account_detail:
        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    # Return to Template
    return render(request, 'dashboard/dashboard_agreement_enquiry_detail.html',
                {'agreement_detail':agreement_detail,
                 'agreement_customer': agreement_customer,
                 'agreement_payable_net': agreement_payable_net,
                 'agreement_payable_gross':agreement_payable_gross,
                 'agreement_instalment_gross':agreement_instalment_gross,
                 'agreement_fees_net':agreement_fees_net,
                 'bacs_audit':bacs_audit,
                 'account_detail':account_detail,
                 'account_summary':account_summary,
                 'settlement_figure':settlement_figure,
                 'settlement_figure_vat':settlement_figure_vat,
                 'agreement_type':agreement_type,
                 'doc_fee_count':doc_fee_count,
                 'primary_count':primary_count,
                 'secondary_count':secondary_count,
                 'agreement_regulated_flag':agreement_regulated_flag,
                 'go_id':go_id})


@login_required(login_url="signin")
def AgreementEnquiryDetail(request, agreement_id):

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)

    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)\
                        .order_by('transtypedesc',)

    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)\
                        .order_by('transactiondate', 'transactionsourceid')

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)

    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False) \
                                                                                .order_by('transtypedesc', )

    bacs_audit = ncf_dd_audit_log.objects.filter(da_agreement_id=agreement_id)\
                                            .order_by('-da_reporting_date', 'da_source')

    # Get Regulated Status
    agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=agreement_id).exists()
    if agreement_regulated:
        agreement_regulated_flag = True
    else:
        agreement_regulated_flag = False

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    # Agreement Payable Net of VAT
    try:
        agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        agreement_payable_net = 0

    # Add in Fees if they exist
    try:
        agreement_fees_net = account_detail_fees.aggregate(Sum('transnetpayment'))
        if agreement_fees_net is not None:
            agreement_payable_net += agreement_fees_net["transnetpayment__sum"]
    except:
        agreement_fees_net = None
        agreement_payable_net = 0
        pass

    # Agreement Payable Gross of VAT
    agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

    # Agreement Instalment Gross
    agreement_instalment_gross = agreement_detail.agreementinstalmentnet
    if agreement_detail.agreementinstalmentvat  is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    # Sundry Items
    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'), Sum('transgrosspayment') )
    settlement_figure_net = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_gross = settlement_figure_queryset['transgrosspayment__sum']
    settlement_figure_vat = settlement_figure_gross - settlement_figure_net

    # if agreement_type == 'Lease':
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    # else:
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    # After VAT Changes in Database Stored Procedures
    # settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    # settlement_figure_gross_queryset = account_summary.aggregate(Sum('transgrosspayment'))
    # settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    # if settlement_figure_gross_queryset:
    #     settlement_figure_gross = settlement_figure_gross_queryset['transgrosspayment__sum']
    # else:
    #     settlement_figure_gross = 0
    # if agreement_type == 'Lease':
    #     if settlement_figure_gross:
    #         settlement_figure_vat = settlement_figure_gross - settlement_figure
    #     else:
    #         settlement_figure_vat = 0
    # else:
    #     settlement_figure_vat = 0

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=first_rental_date) \
                                                                            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                          transactionsourceid__in=['SP1', 'GO1'],
                                                                          transtypeid__isnull=True,
                                                                          transactiondate__gte=first_rental_date)\
                                                                          .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0


    # Add Gross of Vat to account summary queryset
    # row_index = 0
    # for row in account_summary:
    #     row.transvatpayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
    #     if row.transactionsourceid in ['SP1', 'SP2', 'SP3', 'GO1', 'GO3']:
    #         if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
    #             row_index += 1
    #     row.row_index = row_index
    #
    # # Add Gross of Vat to account detail queryset
    # for row in account_detail:
    #     row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    row_index = 0
    for row in account_summary:

        # if row.transactionsourceid in ['GO8','GO9', 'SP9'] and row.transvatpayment is not None:
        # if row.transactionsourceid in ['GO8','GO9','GO1']:
        #     row.transgrosspayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
        # else:
        #     row.transgrosspayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)

        if row.transactionsourceid in ['GO1', 'GO2', 'GO3', 'SP1', 'SP2', 'SP3']:
            if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
                row_index += 1
        row.row_index = row_index

    # Add Gross of Vat to account detail queryset
    # for row in account_detail:
    #     row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    show_sentinal_button = True
    if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
        show_sentinal_button = False

    # Return to Template
    return render(request, 'dashboard/dashboard_agreement_enquiry_detail.html',
                {'agreement_detail':agreement_detail,
                 'agreement_customer': agreement_customer,
                 'agreement_payable_net': agreement_payable_net,
                 'agreement_payable_gross':agreement_payable_gross,
                 'agreement_instalment_gross':agreement_instalment_gross,
                 'agreement_fees_net':agreement_fees_net,
                 'bacs_audit':bacs_audit,
                 'account_detail':account_detail,
                 'account_summary':account_summary,
                 'settlement_figure_net': settlement_figure_net,
                 'settlement_figure_gross':settlement_figure_gross,
                 'settlement_figure_vat':settlement_figure_vat,
                 'agreement_type':agreement_type,
                 'doc_fee_count':doc_fee_count,
                 'primary_count':primary_count,
                 'secondary_count':secondary_count,
                 'agreement_regulated_flag':agreement_regulated_flag,
                 'go_id':go_id,
                 'show_sentinel_button': show_sentinal_button})


# DD Audit Enquiries
# ------------------
@login_required(login_url="signin")
def DDForecastList(request):
    dd_extract = go_account_transaction_summary.objects.filter(transagreementclosedflag_id='901',
                                                                      transagreementcloseddate__isnull=True,
                                                                      transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3'],
                                                                      transddpayment=True) \
                                                                        .order_by('transactiondate', 'agreementnumber')


    dd_list = go_account_transaction_summary_Filter(request.GET, queryset=dd_extract)

    # Total Gross Forecast Draw Down
    forecast_gross_drawdown = dd_list.qs.aggregate(Sum('transgrosspayment'))
    if not forecast_gross_drawdown["transgrosspayment__sum"]:
        forecast_gross_drawdown["transgrosspayment__sum"] = 0
    forecast_gross_drawdown_value = forecast_gross_drawdown["transgrosspayment__sum"]

    try:
        forecast_gross_drawdown_count = dd_list.qs.count()
    except:
        forecast_gross_drawdown_count = 0

    # Total Gross Forecast Bounces due to DDI issues
    forecast_gross_bounce = dd_list.qs.filter(transagreementddstatus_id='I').aggregate(Sum('transgrosspayment'))
    if not forecast_gross_bounce["transgrosspayment__sum"]:
        forecast_gross_bounce["transgrosspayment__sum"] = 0
    forecast_gross_bounce_value = forecast_gross_bounce["transgrosspayment__sum"]

    try:
        forecast_gross_bounce_count = dd_list.qs.filter(transagreementddstatus_id='I').count()
    except:
        forecast_gross_bounce_count = 0

    # Total Gross Foercast Receipts excluding Refer to Payer
    forecast_gross_received_value = forecast_gross_drawdown["transgrosspayment__sum"] - forecast_gross_bounce["transgrosspayment__sum"]
    forecast_gross_received_count = forecast_gross_drawdown_count - forecast_gross_bounce_count

    if forecast_gross_drawdown_value > 0:
        forecast_gross_drawdown_percent = 100
        forecast_gross_bounce_percent = (forecast_gross_bounce_value/forecast_gross_drawdown_value) * 100
        forecast_gross_received_percent = (forecast_gross_received_value / forecast_gross_drawdown_value) * 100
    else:
        forecast_gross_drawdown_percent = 0
        forecast_gross_bounce_percent = 0
        forecast_gross_received_percent = 0


    paginator = Paginator(dd_list.qs, 9)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') or request.GET.get('transcustomercompany') \
                 or request.GET.get('transagreementddstatus') or request.GET.get('transactiondate') \
                 or request.GET.get('transagreementdefname') or request.GET.get('transactionsourcedesc')
    return render(request, 'dashboard/dashboard_dd_forecast_list.html', {'dd_list':dd_list,
                                                                         'dd_list_qs': pub,
                                                                         'forecast_gross_drawdown_value' : forecast_gross_drawdown_value,
                                                                         'forecast_gross_bounce_value' : forecast_gross_bounce_value,
                                                                         'forecast_gross_received_value' : forecast_gross_received_value,
                                                                         'forecast_gross_drawdown_count' : forecast_gross_drawdown_count,
                                                                         'forecast_gross_bounce_count' : forecast_gross_bounce_count,
                                                                         'forecast_gross_received_count': forecast_gross_received_count,
                                                                         'forecast_gross_bounce_percent': forecast_gross_bounce_percent,
                                                                         'forecast_gross_received_percent': forecast_gross_received_percent,
                                                                         'forecast_gross_drawdown_percent': forecast_gross_drawdown_percent,
                                                                         'has_filter': has_filter})

# Print Routines
# -------------------------------------
@login_required(login_url="signin")
def dd_forecast_xlsx(request, input_date):
    dd_extract = go_account_transaction_summary.objects.filter(transagreementclosedflag_id='901',
                                                                      transagreementcloseddate__isnull=True,
                                                                      transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3'],
                                                                      transddpayment=True,
                                                                      transactiondate=input_date)  \
        .order_by('agreementnumber')

    # Write to Excel
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    header = workbook.add_format({'bold': True})
    header.set_bg_color('#F2F2F2')
    header_a = workbook.add_format({'bold': True})
    header_a.set_bg_color('#F2F2F2')
    header_a.set_align('center')
    header_b = workbook.add_format({'bold': True})
    header_b.set_bg_color('#F2F2F2')
    header_b.set_align('right')
    date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    center = workbook.add_format()
    center.set_align('center')
    italic_right = workbook.add_format()
    italic_right.set_align('right')
    italic_right.set_italic()
    italic_center = workbook.add_format()
    italic_center.set_align('center')
    italic_center.set_italic()

    worksheet.set_column('A:A', 24)
    worksheet.set_column('B:B', 86)
    worksheet.set_column('C:C', 22)
    worksheet.set_column('D:D', 18)
    worksheet.set_column('E:E', 16)
    worksheet.set_column('F:F', 22)
    worksheet.set_column('G:G', 22)

    col_header_format = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                             'align': 'center'})
    col_header_format.set_font_color('#1f4e78')
    col_header_format.set_bg_color('#F2F2F2')

    col_header_format_left = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                                  'align': 'left'})
    col_header_format_left.set_font_color('#1f4e78')
    col_header_format_left.set_bg_color('#F2F2F2')

    col_header_format_right = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                                  'align': 'right'})
    col_header_format_right.set_font_color('#1f4e78')
    col_header_format_right.set_bg_color('#F2F2F2')
    col_header_format_right.set_indent(3)

    # Write Header
    worksheet.write(0, 0, 'AgreementNumber', col_header_format)
    worksheet.write(0, 1, 'Customer Name', col_header_format_left)
    worksheet.write(0, 2, 'Agreement Type', col_header_format_left)
    worksheet.write(0, 3, 'DD Date', col_header_format)
    worksheet.write(0, 4, 'DD Status', col_header_format)
    worksheet.write(0, 5, 'Agreement Stage', col_header_format)
    worksheet.write(0, 6, 'Gross Value', col_header_format_right)

    n = 0
    for drawdown in dd_extract:
        n += 1

        worksheet.write(n, 0, drawdown.agreementnumber, center)
        worksheet.write(n, 1, drawdown.transcustomercompany)
        worksheet.write(n, 2, drawdown.transagreementdefname)
        worksheet.write(n, 3, drawdown.transactiondate, date)
        if drawdown.transagreementddstatus_id == 'I':
            worksheet.write(n, 4, 'Inactive', center)
        else:
            worksheet.write(n, 4, 'Active', center)
        worksheet.write(n, 5, drawdown.transactionsourcedesc, center)
        worksheet.write(n, 6, drawdown.transgrosspayment, money)

    worksheet.autofilter(0, 0, n, 6)
    workbook.close()
    output.seek(0)

    filename = 'GO DD Drawdown Forecast @ {date}.xlsx' \
        .format(date=input_date)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


@login_required(login_url="signin")
def paymentprofile_xlsx(request, agreement_id):

    # Get Data
    # ========
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)

    # Write to Excel
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    header = workbook.add_format({'bold': True})
    header.set_bg_color('#F2F2F2')
    header_a = workbook.add_format({'bold': True})
    header_a.set_bg_color('#F2F2F2')
    header_a.set_align('center')
    header_b = workbook.add_format({'bold': True})
    header_b.set_bg_color('#F2F2F2')
    header_b.set_align('right')
    date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    center = workbook.add_format()
    center.set_align('center')
    italic_right = workbook.add_format()
    italic_right.set_align('right')
    italic_right.set_italic()
    italic_center = workbook.add_format()
    italic_center.set_align('center')
    italic_center.set_italic()

    worksheet.set_column('A:A', 14)
    worksheet.set_column('B:B', 14)
    worksheet.set_column('C:C', 14)
    worksheet.set_column('D:D', 50)
    worksheet.set_column('E:E', 14)
    worksheet.set_column('F:F', 6)
    worksheet.set_column('G:G', 14)
    worksheet.set_column('H:H', 6)

    # Write Header
    worksheet.write(0, 0, 'Agreement', header_a)
    worksheet.write(0, 1, 'Record Type', header_a)
    worksheet.write(0, 2, 'Date', header_a)
    worksheet.write(0, 3, 'Description', header)
    worksheet.write(0, 4, 'Value', header_b)
    worksheet.write(0, 5, ' ', header_a)
    worksheet.write(0, 6, 'Balance', header_b)
    worksheet.write(0, 7, ' ', header_a)

    n = 0
    val_summary = 0

    for transaction in account_summary:
        n += 1
        val_summary += transaction.transnetpayment
        if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'SP2' or transaction.transactionsourceid == 'SP3'\
                or transaction.transactionsourceid == 'GO1' or transaction.transactionsourceid == 'GO3':
            worksheet.write(n, 0, transaction.agreementnumber, center)
            worksheet.write(n, 1, 'Profile', italic_center)
            worksheet.write(n, 2, transaction.transactiondate, date)
            if transaction.transactiondate < agreement_detail.agreementfirstpaymentdate:
                worksheet.write(n, 3, 'Manual Payment Due')
            else:
                if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'GO1':
                    worksheet.write(n, 3, 'Primary Payment Due')
                else:
                    worksheet.write(n, 3, 'Secondary Payment Due')
            worksheet.write(n, 4, round(transaction.transnetpayment,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 5, '+VAT', center)
            worksheet.write(n, 6, round(val_summary,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 7, '+VAT', center)
        else:
            worksheet.write(n, 0, transaction.agreementnumber, center)
            worksheet.write(n, 1, 'History', italic_center)
            worksheet.write(n, 2, transaction.transactiondate, date)
            worksheet.write(n, 3, transaction.transtypedesc, italic_right)
            worksheet.write(n, 4, round(transaction.transnetpayment,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 5, '+VAT', center)
            worksheet.write(n, 6, round(val_summary,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 7, '+VAT', center)

    workbook.close()
    output.seek(0)
    if agreement_detail.agreementdefname != 'Hire Purchase':
        filename = 'GO ' + agreement_id + ' Payment Profile (Lease) - Net of VAT @ {date:%Y-%m-%d}.xlsx'\
                                                .format(date=datetime.datetime.now())
    else:
        filename = 'GO ' + agreement_id + ' Payment Profile (HP) - No VAT @ {date:%Y-%m-%d}.xlsx' \
            .format(date=datetime.datetime.now())

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


def sage_xlsx(request, agreement_id):

    # Write to Excel
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    header = workbook.add_format({'bold': True})
    header.set_bg_color('#F2F2F2')
    header_a = workbook.add_format({'bold': True})
    header_a.set_bg_color('#F2F2F2')
    header_a.set_align('center')
    header_b = workbook.add_format({'bold': True})
    header_b.set_bg_color('#F2F2F2')
    header_b.set_align('right')
    date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    center = workbook.add_format()
    center.set_align('center')
    italic_right = workbook.add_format()
    italic_right.set_align('right')
    italic_right.set_italic()
    italic_center = workbook.add_format()
    italic_center.set_align('center')
    italic_center.set_italic()

    worksheet.set_column('A:A', 14)
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 14)
    worksheet.set_column('F:F', 14)
    worksheet.set_column('G:G', 14)
    worksheet.set_column('H:H', 14)
    worksheet.set_column('I:I', 14)
    worksheet.set_column('J:J', 14)
    worksheet.set_column('K:K', 14)
    worksheet.set_column('L:L', 14)
    worksheet.set_column('M:M', 14)
    worksheet.set_column('N:N', 14)
    worksheet.set_column('O:O', 14)

    # Write Header
    worksheet.write(0, 0, 'Type', header_a)
    worksheet.write(0, 1, 'Account Reference', header_a)
    worksheet.write(0, 2, 'Nominal A/C Ref', header_a)
    worksheet.write(0, 3, 'Department Code', header_a)
    worksheet.write(0, 4, 'Date', header_a)
    worksheet.write(0, 5, 'Reference', header_a)
    worksheet.write(0, 6, 'Details', header_a)
    worksheet.write(0, 7, 'Net Amount', header_a)
    worksheet.write(0, 8, 'Tax Code', header_a)
    worksheet.write(0, 9, 'Tax Amount', header_a)
    worksheet.write(0, 10, 'Exchange Rate', header_a)
    worksheet.write(0, 11, 'Extra Reference', header_a)
    worksheet.write(0, 12, 'User Name', header_a)
    worksheet.write(0, 13, 'Project Refn', header_a)
    worksheet.write(0, 14, 'Cost Code Refn', header_a)

    n = 0
    val_summary = 0

    # for transaction in account_summary:
    #     n += 1
    #     val_summary += transaction.transnetpayment
    #     if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'SP2' or transaction.transactionsourceid == 'SP3'\
    #             or transaction.transactionsourceid == 'GO1' or transaction.transactionsourceid == 'GO3':
    #         worksheet.write(n, 0, transaction.agreementnumber, center)
    #         worksheet.write(n, 1, 'Profile', italic_center)
    #         worksheet.write(n, 2, transaction.transactiondate, date)
    #         if transaction.transactiondate < agreement_detail.agreementfirstpaymentdate:
    #             worksheet.write(n, 3, 'Manual Payment Due')
    #         else:
    #             if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'GO1':
    #                 worksheet.write(n, 3, 'Primary Payment Due')
    #             else:
    #                 worksheet.write(n, 3, 'Secondary Payment Due')
    #         worksheet.write(n, 4, transaction.transnetpayment, money)
    #         if agreement_detail.agreementdefname != 'Hire Purchase':
    #             worksheet.write(n, 5, '+VAT', center)
    #         worksheet.write(n, 6, val_summary, money)
    #         if agreement_detail.agreementdefname != 'Hire Purchase':
    #             worksheet.write(n, 7, '+VAT', center)
    #     else:
    #         worksheet.write(n, 0, transaction.agreementnumber, center)
    #         worksheet.write(n, 1, 'History', italic_center)
    #         worksheet.write(n, 2, transaction.transactiondate, date)
    #         worksheet.write(n, 3, transaction.transtypedesc, italic_right)
    #         worksheet.write(n, 4, transaction.transnetpayment, money)
    #         if agreement_detail.agreementdefname != 'Hire Purchase':
    #             worksheet.write(n, 5, '+VAT', center)
    #         worksheet.write(n, 6, val_summary, money)
    #         if agreement_detail.agreementdefname != 'Hire Purchase':
    #             worksheet.write(n, 7, '+VAT', center)

    workbook.close()
    output.seek(0)

    filename = 'Sage Export @ {date:%Y-%m-%d}.xlsx'\
                                                .format(date=datetime.datetime.now())

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


@login_required(login_url="signin")
def paymentprofile_gross_xlsx(request, agreement_id):

    # Get Data
    # ========
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)

    # Add Gross of Vat to account summary queryset
    for row in account_summary:
        row.transvatpayment = row.transgrosspayment

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    # Write to Excel
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    header = workbook.add_format({'bold': True})
    header.set_bg_color('#F2F2F2')
    header_a = workbook.add_format({'bold': True})
    header_a.set_bg_color('#F2F2F2')
    header_a.set_align('center')
    header_b = workbook.add_format({'bold': True})
    header_b.set_bg_color('#F2F2F2')
    header_b.set_align('right')
    date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    center = workbook.add_format()
    center.set_align('center')
    italic_right = workbook.add_format()
    italic_right.set_align('right')
    italic_right.set_italic()
    italic_center = workbook.add_format()
    italic_center.set_align('center')
    italic_center.set_italic()

    worksheet.set_column('A:A', 14)
    worksheet.set_column('B:B', 14)
    worksheet.set_column('C:C', 14)
    worksheet.set_column('D:D', 50)
    worksheet.set_column('E:E', 14)
    worksheet.set_column('F:F', 6)
    worksheet.set_column('G:G', 14)
    worksheet.set_column('H:H', 6)

    # Write Header
    worksheet.write(0, 0, 'Agreement', header_a)
    worksheet.write(0, 1, 'Record Type', header_a)
    worksheet.write(0, 2, 'Date', header_a)
    worksheet.write(0, 3, 'Description', header)
    worksheet.write(0, 4, 'Value', header_b)
    worksheet.write(0, 5, ' ', header_a)
    worksheet.write(0, 6, 'Balance', header_b)
    worksheet.write(0, 7, ' ', header_a)

    n = 0
    val_summary = 0

    for transaction in account_summary:
        n += 1
        val_summary += transaction.transvatpayment
        if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'SP2' or transaction.transactionsourceid == 'SP3' \
                or transaction.transactionsourceid == 'GO1' or transaction.transactionsourceid == 'GO3' :
            worksheet.write(n, 0, transaction.agreementnumber, center)
            worksheet.write(n, 1, 'Profile', italic_center)
            worksheet.write(n, 2, transaction.transactiondate, date)
            if transaction.transactiondate < agreement_detail.agreementfirstpaymentdate:
                worksheet.write(n, 3, 'Manual Payment Due')
            else:
                if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'GO1':
                    worksheet.write(n, 3, 'Primary Payment Due')
                else:
                    worksheet.write(n, 3, 'Secondary Payment Due')
            worksheet.write(n, 4, round(transaction.transvatpayment,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 5, 'Incl. VAT', center)
            worksheet.write(n, 6, round(val_summary,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 7, 'Incl. VAT', center)
        else:
            worksheet.write(n, 0, transaction.agreementnumber, center)
            worksheet.write(n, 1, 'History', italic_center)
            worksheet.write(n, 2, transaction.transactiondate, date)
            worksheet.write(n, 3, transaction.transtypedesc, italic_right)
            worksheet.write(n, 4, round(transaction.transvatpayment,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 5, 'Incl. VAT', center)
            worksheet.write(n, 6, round(val_summary,2), money)
            if agreement_detail.agreementdefname != 'Hire Purchase':
                worksheet.write(n, 7, 'Incl. VAT', center)

    workbook.close()
    output.seek(0)
    filename = 'GO ' + agreement_id + ' Payment Profile (Lease) - Gross of VAT @ {date:%Y-%m-%d}.xlsx'\
                                                .format(date=datetime.datetime.now())
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


@login_required(login_url="signin")
def statement_of_account_allocated_xlsx(request, agreement_id):

    # Get Data
    # ========
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_summary_01 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id
                                                                ,transactionsourceid__in=['SP1','SP2', 'SP3', 'GO1', 'GO3'])

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=first_rental_date) \
            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=first_rental_date) \
            .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary_01.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    val_term = doc_fee_count + primary_count + secondary_count

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    # Initialise worksheet
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    worksheet.fit_to_pages(1, 1)  # Fit to 1x1 pages.

    # Set cell formats
    header_a = workbook.add_format({'bold': True})
    header_a.set_align('left')
    header_b = workbook.add_format({'align': 'left'})
    header_date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    header_date.set_align('left')
    list_date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    list_date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    money_total = workbook.add_format({'num_format': '£#,##0.00', 'bold': True})
    money_total.set_align('right')
    money_total.set_bottom(6)
    center = workbook.add_format()
    center.set_align('center')

    fontsize_9 = workbook.add_format({'font_name': 'Calibri', 'font_size': 9,
                                         'align': 'left'})

    fontsize_9_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 9,
                                      'align': 'center'})

    fontsize_10_blue_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 10,
                                             'align': 'center'})
    fontsize_10_blue_center.set_font_color('#1f4e78')

    header_format = workbook.add_format({'bold': True, 'underline': 1, 'font_name': 'Calibri', 'font_size': 16,
                                         'align': 'center'})

    col_header_format = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                             'align': 'center'})

    col_header_format_left = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                             'align': 'left'})

    # Set column and row dimensions
    worksheet.set_column('A:A', 8.43)
    worksheet.set_column('B:B', 9.14)
    worksheet.set_column('C:C', 8.86)
    worksheet.set_column('D:D', 10)
    worksheet.set_column('E:E', 8.43)
    worksheet.set_column('F:F', 5.57)
    worksheet.set_column('G:G', 5.57)
    worksheet.set_column('H:H', 5)
    worksheet.set_column('I:I', 5.57)
    worksheet.set_column('J:J', 5.57)
    worksheet.set_column('K:K', 5)
    worksheet.set_column('L:L', 11.14)
    worksheet.set_column('M:M', 8.43)
    worksheet.set_column('N:N', 8)
    worksheet.set_column('O:O', 8)
    worksheet.set_column('P:P', 8.43)

    worksheet.set_row(0,5)
    worksheet.set_row(1,21)
    worksheet.set_row(2,21)
    worksheet.set_row(3,21)
    worksheet.set_row(4,21)
    worksheet.set_row(5,7.5)
    worksheet.set_row(6,21)
    worksheet.set_row(7,7.5)
    worksheet.set_row(12, 7.5)
    worksheet.set_row(14, 5)

    # Write Header
    # worksheet.insert_image('L2', 'staticfiles/assets/images/others/blackrock-curved-bold-logo.png')
    worksheet.insert_image('L2', 'staticfiles/assets/images/others/bluerock-logo.png')
    worksheet.merge_range('A7:P7', 'STATEMENT OF ACCOUNT', header_format)

    worksheet.write('B9', 'Customer Number:', header_a)
    worksheet.write('D9', agreement_customer.customernumber, header_b)
    worksheet.write('L9', 'Broker ID:', header_a)
    worksheet.write('M9', 'NCF002', header_b)

    worksheet.write('B10', 'Agreement Number:', header_a)
    worksheet.write('D10', agreement_detail.agreementnumber, header_b)
    worksheet.write('L10', 'Broker:', header_a)
    worksheet.write('M10', 'Nationwide Corporate Finance Ltd', header_b)

    val_now = datetime.datetime.now()
    worksheet.write('B11', 'Agreement Date:', header_a)
    worksheet.write('D11', agreement_detail.agreementagreementdate, header_date)
    worksheet.write('L11', 'Internal Ref:', header_a)
    worksheet.write('M11', '{apel}-{mmyy}'.format(apel=agreement_detail.agreementnumber,
                                                      mmyy=val_now.strftime("%m%y")), header_b)

    worksheet.write('B12', 'Term:', header_a)
    worksheet.write('D12', '{txt_term} Months'.format(txt_term=val_term), header_b)

    worksheet.merge_range('B14:C14', 'Payment Date', col_header_format)
    worksheet.merge_range('D14:E14', 'Payment Description', col_header_format_left)
    worksheet.merge_range('F14:H14', 'Payment Amount', col_header_format)
    worksheet.merge_range('I14:K14', 'Received Amount', col_header_format)
    worksheet.merge_range('L14:M14', 'Payment Status', col_header_format)
    worksheet.merge_range('N14:O14', 'Payment Number', col_header_format)

    # Get Business Calendar Date Range for Today's Date
    # business = CDay(calendar=EnglandAndWalesHolidayCalendar())
    current_date_three_business_days_earlier = datetime.date.today() + relativedelta(days=-4)
    current_date_three_business_days_later = datetime.date.today() + relativedelta(days=+4)

    # Write Detail Lines
    n = 14
    val_paid = 0
    val_due = 0

    for transaction in account_summary_01:

        # Write Next Row
        n += 1
        # running_total_01 = 0
        worksheet.merge_range(n,1,n,2, transaction.transactiondate, list_date)

        if transaction.transactiondate < agreement_detail.agreementfirstpaymentdate:
            worksheet.merge_range(n, 3, n, 4, 'Documentation Fee')
            txn_date_three_business_days_earlier = transaction.transactiondate + relativedelta(days=-20)
            txn_date_three_business_days_later = agreement_detail.agreementfirstpaymentdate + relativedelta(days=-1)
        else:
            worksheet.merge_range(n, 3, n, 4, 'Monthly Repayment')
            txn_date_three_business_days_earlier = transaction.transactiondate  # + relativedelta(days=-2)
            txn_date_three_business_days_later = (transaction.transactiondate + relativedelta(
                months=+1)) + relativedelta(days=-1)

        worksheet.merge_range(n, 5, n, 6, round(transaction.transnetpayment,2), money)

        if agreement_type == 'Lease':
            worksheet.write(n, 7, '+VAT', fontsize_9)

        # Get transaction value
        account_summary_02 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                    transactiondate__gte=txn_date_three_business_days_earlier,
                                                    transactiondate__lte=txn_date_three_business_days_later).\
                                                                exclude(transactionsourceid__in=['SP1','SP2', 'SP3', 'GO1', 'GO3'])

        transaction_total_query = account_summary_02.aggregate(Sum('transnetpayment'))
        transaction_total = transaction_total_query["transnetpayment__sum"]
        if not transaction_total:
            transaction_total = 0
        else:
            if abs(transaction_total) <= 0.01:
                transaction_total = 0
        transaction_total = -transaction_total


        val_due = val_due + transaction.transnetpayment
        # worksheet.merge_range(n, 18, n, 19, val_due, money)

        val_paid = val_paid + transaction_total
        # worksheet.merge_range(n, 20, n, 21, val_paid, money)

        payment_balance = transaction_total - transaction.transnetpayment

        if abs(payment_balance) <= 0.01:
            transaction_total = transaction.transnetpayment
            payment_balance = transaction_total - transaction.transnetpayment

        # worksheet.merge_range(n, 22, n, 23, payment_balance, money)

        val_outstanding_balance_cfwd = val_paid - val_due
        # worksheet.merge_range(n, 24, n, 25, val_outstanding_balance_cfwd, money)

        # Set Payment Status based on today's date
        val_payment_status = ''
        if transaction.transactiondate.date() <= (current_date_three_business_days_earlier):

            if val_outstanding_balance_cfwd == 0:
                val_payment_status = 'Received'
            else:
                if payment_balance == -transaction.transnetpayment:
                    val_payment_status = 'Not Received'
                else:
                    if payment_balance == 0:
                        val_payment_status = 'Received'
                    else:
                        if payment_balance > 0:
                            if val_outstanding_balance_cfwd > 0:
                                val_payment_status = 'Advance Received'
                            else:
                                val_payment_status = 'Received'
                        else:
                            val_payment_status = 'Part Paid'
        else:

            if transaction.transactiondate.date() >= (current_date_three_business_days_later):

                if val_outstanding_balance_cfwd < 0:
                    val_payment_status = 'Not Yet Due'
                else:
                    if (val_outstanding_balance_cfwd >= transaction.transnetpayment)\
                            or (val_outstanding_balance_cfwd == 0):
                        val_payment_status = 'Received'
                    else:
                        val_payment_status = 'Part Paid'

            else:

                if val_outstanding_balance_cfwd == 0:
                    val_payment_status = 'Received'
                else:
                    if payment_balance == -transaction.transnetpayment:
                        val_payment_status = 'Expected'
                        transaction_total = transaction.transnetpayment
                    else:
                        if payment_balance == 0:
                            val_payment_status = 'Received'
                        else:
                            if payment_balance > 0:
                                if val_outstanding_balance_cfwd > 0:
                                    val_payment_status = 'Advance Received'
                                else:
                                    val_payment_status = 'Received'
                            else:
                                val_payment_status = 'Part Paid'

        worksheet.merge_range(n, 8, n, 9, round(transaction_total,2), money)

        if agreement_type == 'Lease':
            worksheet.write(n, 10, '+VAT', fontsize_9)

        worksheet.merge_range(n, 11, n, 12, val_payment_status, center)

        if n == 15:
            worksheet.merge_range(n, 13, n, 14, '-', center)
        else:
            worksheet.merge_range(n, 13, n, 14, n-15, center)



    # write total section
    # first line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    worksheet.merge_range(n, 1, n, 2, 'Total Amount Paid:', header_a)
    worksheet.merge_range(n, 5, n, 6, " ", money_total)
    formula_for_paid = 'SUM(I16:J{end})'.format(end=n-1)
    worksheet.write_formula(n, 5, formula_for_paid, money_total)

    if agreement_type == 'Lease':
        worksheet.write(n, 7, '+VAT', fontsize_9)

    # next line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    worksheet.merge_range(n, 1, n, 3, 'Total Amount Due If Terminated:', header_a)
    worksheet.merge_range(n, 5, n, 6, " ", money_total)
    formula_for_outstanding = 'SUM(F16:G{end})-SUM(I16:J{end})'.format(end=n - 3)
    worksheet.write_formula(n, 5, formula_for_outstanding, money_total)

    if agreement_type == 'Lease':
        worksheet.write(n, 7, '+VAT', fontsize_9)

    # next line
    n += 1
    worksheet.set_row(n, 15.75)
    terms_line = 'The term will always include any primary or secondary payments due' \
                 ' in accordance with terms & conditions of the agreement.'
    worksheet.merge_range(n,0,n,15, terms_line, fontsize_9_center)

    # next line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    fca_line = 'VAT Reg No. 974 5940 73 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No:' \
               ' 729205 | Company Reg No. 06944649.'
    worksheet.merge_range(n,0,n,15,  fca_line, fontsize_10_blue_center)

    # Close workbook
    workbook.close()
    output.seek(0)

    # Generate workbook name
    filename = agreement_id + ' @ {date:%Y-%m-%d} - Account Statement - DD Allocated.xlsx'\
                                                .format(date=datetime.datetime.now())

    # Generate response for excel and prompted save target
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


@login_required(login_url="signin")
def statement_of_account_xlsx(request, agreement_id):

    # Get Data
    # ========
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)

    account_summary_01 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id
                                                                ,transactionsourceid__in=['SP1','SP2', 'SP3', 'GO1', 'GO3'])

    receipts_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,). \
                                                        exclude(transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3'])\
                                                        .aggregate(Sum('transnetpayment'))

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=first_rental_date) \
            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=first_rental_date) \
            .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary_01.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    val_term = doc_fee_count + primary_count + secondary_count

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    # Initialise worksheet
    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True, 'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    worksheet.fit_to_pages(1, 1)  # Fit to 1x1 pages.

    # Set cell formats
    header_a = workbook.add_format({'bold': True})
    header_a.set_align('left')
    header_b = workbook.add_format({'align': 'left'})
    header_date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    header_date.set_align('left')
    list_date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    list_date.set_align('center')
    money = workbook.add_format({'num_format': '£#,##0.00'})
    money.set_align('right')
    money_total = workbook.add_format({'num_format': '£#,##0.00', 'bold': True})
    money_total.set_align('right')
    money_total.set_bottom(6)
    center = workbook.add_format()
    center.set_align('center')

    fontsize_9 = workbook.add_format({'font_name': 'Calibri', 'font_size': 9,
                                         'align': 'left'})

    fontsize_9_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 9,
                                      'align': 'center'})

    fontsize_10_blue_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 10,
                                             'align': 'center'})
    fontsize_10_blue_center.set_font_color('#1f4e78')

    header_format = workbook.add_format({'bold': True, 'underline': 1, 'font_name': 'Calibri', 'font_size': 16,
                                         'align': 'center'})

    col_header_format = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                             'align': 'center'})

    col_header_format_left = workbook.add_format({'underline': 1, 'font_name': 'Calibri', 'font_size': 11,
                                             'align': 'left'})

    # Set column and row dimensions
    worksheet.set_column('A:A', 8.43)
    worksheet.set_column('B:B', 9.14)
    worksheet.set_column('C:C', 8.86)
    worksheet.set_column('D:D', 10)
    worksheet.set_column('E:E', 8.43)
    worksheet.set_column('F:F', 5.57)
    worksheet.set_column('G:G', 5.57)
    worksheet.set_column('H:H', 5)
    worksheet.set_column('I:I', 5.57)
    worksheet.set_column('J:J', 5.57)
    worksheet.set_column('K:K', 5)
    worksheet.set_column('L:L', 11.14)
    worksheet.set_column('M:M', 8.43)
    worksheet.set_column('N:N', 8)
    worksheet.set_column('O:O', 8)
    worksheet.set_column('P:P', 8.43)

    worksheet.set_row(0,5)
    worksheet.set_row(1,21)
    worksheet.set_row(2,21)
    worksheet.set_row(3,21)
    worksheet.set_row(4,21)
    worksheet.set_row(5,7.5)
    worksheet.set_row(6,21)
    worksheet.set_row(7,7.5)
    worksheet.set_row(12, 7.5)
    worksheet.set_row(14, 5)

    # Write Header
    # worksheet.insert_image('L2', 'staticfiles/assets/images/others/blackrock-curved-bold-logo.png')
    worksheet.insert_image('L2', 'staticfiles/assets/images/others/bluerock-logo.png')
    worksheet.merge_range('A7:P7', 'STATEMENT OF ACCOUNT', header_format)

    worksheet.write('B9', 'Customer Number:', header_a)
    worksheet.write('D9', agreement_customer.customernumber, header_b)
    worksheet.write('L9', 'Broker ID:', header_a)
    worksheet.write('M9', 'NCF002', header_b)

    worksheet.write('B10', 'Agreement Number:', header_a)
    worksheet.write('D10', agreement_detail.agreementnumber, header_b)
    worksheet.write('L10', 'Broker:', header_a)
    worksheet.write('M10', 'Nationwide Corporate Finance Ltd', header_b)

    val_now = datetime.datetime.now()
    worksheet.write('B11', 'Agreement Date:', header_a)
    worksheet.write('D11', agreement_detail.agreementagreementdate, header_date)
    worksheet.write('L11', 'Internal Ref:', header_a)
    worksheet.write('M11', '{apel}-{mmyy}'.format(apel=agreement_detail.agreementnumber,
                                                      mmyy=val_now.strftime("%m%y")), header_b)

    worksheet.write('B12', 'Term:', header_a)
    worksheet.write('D12', '{txt_term} Months'.format(txt_term=val_term), header_b)

    worksheet.merge_range('B14:C14', 'Payment Date', col_header_format)
    worksheet.merge_range('D14:E14', 'Payment Description', col_header_format_left)
    worksheet.merge_range('F14:H14', 'Payment Amount', col_header_format)
    worksheet.merge_range('I14:K14', 'Received Amount', col_header_format)
    worksheet.merge_range('L14:M14', 'Payment Status', col_header_format)
    worksheet.merge_range('N14:O14', 'Payment Number', col_header_format)

    # Get Business Calendar Date Range for Today's Date
    # business = CDay(calendar=EnglandAndWalesHolidayCalendar())
    current_date_three_business_days_earlier = datetime.date.today() + relativedelta(days=-4)
    current_date_three_business_days_later = datetime.date.today() + relativedelta(days=+4)

    # Write Detail Lines
    n = 14

    if receipts_total["transnetpayment__sum"]:
        wip_receipts_total = -receipts_total["transnetpayment__sum"]
    else:
        wip_receipts_total = 0

    for transaction in account_summary_01:

        # Write Next Row
        n += 1
        # running_total_01 = 0
        worksheet.merge_range(n,1,n,2, transaction.transactiondate, list_date)

        if transaction.transactiondate < agreement_detail.agreementfirstpaymentdate:
            worksheet.merge_range(n, 3, n, 4, 'Documentation Fee')
        else:
            worksheet.merge_range(n, 3, n, 4, 'Monthly Repayment')

        worksheet.merge_range(n, 5, n, 6, round(transaction.transnetpayment,2), money)

        if agreement_type == 'Lease':
            worksheet.write(n, 7, '+VAT', fontsize_9)

        val_payment_status = ''
        if wip_receipts_total > 0:
            wip_receipts_total =  wip_receipts_total - transaction.transnetpayment
            if wip_receipts_total >= 0:
                received_value = transaction.transnetpayment
                val_payment_status = 'Received'
            else:
                received_value = transaction.transnetpayment + wip_receipts_total
                val_payment_status = 'Part Paid'
        else:
            received_value = 0
            if transaction.transactiondate.date() >= (current_date_three_business_days_later):
                val_payment_status = 'Not Yet Due'
            else:
                if transaction.transactiondate.date() <= (current_date_three_business_days_earlier):
                        val_payment_status = 'Not Received'
                else:
                    val_payment_status = 'Expected'

        worksheet.merge_range(n, 8, n, 9, round(received_value,2), money)

        if agreement_type == 'Lease':
            worksheet.write(n, 10, '+VAT', fontsize_9)

        worksheet.merge_range(n, 11, n, 12, val_payment_status, center)

        if n == 15:
            worksheet.merge_range(n, 13, n, 14, '-', center)
        else:
            worksheet.merge_range(n, 13, n, 14, n-15, center)

    # write total section
    # first line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    worksheet.merge_range(n, 1, n, 2, 'Total Amount Paid:', header_a)
    worksheet.merge_range(n, 5, n, 6, " ", money_total)
    formula_for_paid = 'SUM(I16:J{end})'.format(end=n-1)
    worksheet.write_formula(n, 5, formula_for_paid, money_total)

    if agreement_type == 'Lease':
        worksheet.write(n, 7, '+VAT', fontsize_9)

    # next line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    worksheet.merge_range(n, 1, n, 3, 'Total Amount Due If Terminated:', header_a)
    worksheet.merge_range(n, 5, n, 6, " ", money_total)
    formula_for_outstanding = 'SUM(F16:G{end})-SUM(I16:J{end})'.format(end=n - 3)
    worksheet.write_formula(n, 5, formula_for_outstanding, money_total)

    if agreement_type == 'Lease':
        worksheet.write(n, 7, '+VAT', fontsize_9)

    # next line
    n += 1
    worksheet.set_row(n, 15.75)
    terms_line = 'The term will always include any primary or secondary payments due' \
                 ' in accordance with terms & conditions of the agreement.'
    worksheet.merge_range(n,0,n,15, terms_line, fontsize_9_center)

    # next line
    n += 1
    worksheet.set_row(n, 7.5)

    # next line
    n += 1
    fca_line = 'VAT Reg No. 974 5940 73 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No:' \
               ' 729205 | Company Reg No. 06944649.'
    worksheet.merge_range(n,0,n,15,  fca_line, fontsize_10_blue_center)

    # Close workbook
    workbook.close()
    output.seek(0)

    # Generate workbook name
    filename = agreement_id + ' @ {date:%Y-%m-%d} - Account Statement.xlsx'\
                                                .format(date=datetime.datetime.now())

    # Generate response for excel and prompted save target
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


# Signin/Signout
# --------------
def signinView(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard:dashboard')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/signin.html', {'form': form})

def signoutView(request):
    logout(request)
    return redirect('signin')

# VAT Statements
# --------------
def print_pdf_NEXT_VAT_STATEMENT_view(request, agreement_id):

    now = datetime.datetime.now()
    calendar_year = now.year + 1

    response = HttpResponse(content_type='application/pdf')
    filename = 'GO ' + agreement_id + " (" + str(calendar_year) + ")" + " VAT Statement - PRINT Version"
    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    buffer = BytesIO()

    report = PrintVatStatement(buffer, 'Letter', agreement_id, calendar_year, 'PRINT')
    pdf = report.print_users()
    print(pdf)
    response.write(pdf)
    return response

def print_pdf_CURRENT_VAT_STATEMENT_view(request, agreement_id):

    now = datetime.datetime.now()
    calendar_year = now.year

    response = HttpResponse(content_type='application/pdf')
    filename = 'GO ' + agreement_id + " (" + str(calendar_year) + ")" + " VAT Statement - PRINT Version"
    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    buffer = BytesIO()

    report = PrintVatStatement(buffer, 'Letter', agreement_id, calendar_year, 'PRINT')
    pdf = report.print_users()
    print(pdf)
    response.write(pdf)
    return response

def pdf_NEXT_VAT_STATEMENT_view(request, agreement_id):

    now = datetime.datetime.now()
    calendar_year = now.year + 1

    response = HttpResponse(content_type='application/pdf')
    filename = 'GO ' + agreement_id + " (" + str(calendar_year) + ")" + " VAT Statement - PDF Version"
    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    buffer = BytesIO()

    report = PrintVatStatement(buffer, 'Letter', agreement_id, calendar_year, 'PDF')
    pdf = report.print_users()
    print(pdf)
    response.write(pdf)
    return response

def pdf_CURRENT_VAT_STATEMENT_view(request, agreement_id):

    now = datetime.datetime.now()
    calendar_year = now.year

    response = HttpResponse(content_type='application/pdf')
    filename = 'GO ' + agreement_id + " (" + str(calendar_year) + ")" + " VAT Statement - PDF Version"
    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    buffer = BytesIO()

    report = PrintVatStatement(buffer, 'Letter', agreement_id, calendar_year, 'PDF')
    pdf = report.print_users()
    print(pdf)
    response.write(pdf)
    return response

def print_pdf_NEXT_VAT_STATEMENT(request, agreement_id, calendar_year):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                               transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', ).first()
    Agreement_Start_Date= Agreement_Start.transactiondate

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', )
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                       transactionsourceid__in=['SP1', 'GO1'],
                                                                       transtypeid__isnull=False).order_by('transactiondate')
    print(calendar_year)
    FROM_DATE = str(calendar_year)+'-01-01'
    TO_DATE = str(calendar_year)+'-12-31'
    # print(workingdate)
    # FROM_DATE = '2020-01-01'
    # TO_DATE = '2020-12-31'


    account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                                 transtypeid__isnull=True,
                                                                                 transactiondate__gte=FROM_DATE,
                                                                                 transactiondate__lt=TO_DATE
                                                                                 ).order_by('transactiondate')
    count_transactions = account_detail_rentals.count()



    try:
        Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        Rentals2 = 0

    try:
        Rentals= account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
        if Rentals is not None:
            Rentals += Rentals2[account_detail_rentals.transnetpayment]
    except:
        pass

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    # Agreement Payable Net of VAT
    try:
        agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        agreement_payable_net = 0

    # Add in Fees if they exist
    try:
        agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
        if agreement_fees_net is not None:
            agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
    except:
        pass

    # Agreement Payable Gross of VAT
    agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()
    data3 = ("", "")

    first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=Agreement_Start_Date).count()
    except:
        doc_fee_count = 0
    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=Agreement_Start_Date).count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3','GO3']).count()
    except:
        secondary_count = 0

    for row in account_detail:
        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    agreement_instalment_gross = agreement_detail.agreementinstalmentnet
    if agreement_detail.agreementinstalmentvat is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    array = []
    # TODO: GO#110 Vat Statement Correction 2 - Start
    TOTAL_NET = 0
    TOTAL_VAT = 0
    TOTAL_GROSS = 0
    # TODO: GO#110 Vat Statement Correction 2 - End
    Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                  transtypedesc='Documentation Fee',
                                                                  transactionsourceid__in=['SP1', 'GO1'],
                                                                  transactiondate__gte=FROM_DATE,
                                                                  transactiondate__lt=TO_DATE
                                                                  )
    # TODO: GO#110 Vat Statement Correction 2 - Start
    for a in Manual_Payment:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))), \
            array.append(str("Manual"))
            # array.append(str('£0.00'))
            # array.append(str('£0.00'))
            NET_Column = round(a.transnetpayment, 2)
            TOTAL_NET = TOTAL_NET + NET_Column

            array.append(str("£" + format(NET_Column, ',')))

            Manual_Payment_vat = round(a.transnetpayment * decimal.Decimal(0.2), 2)

            array.append(str("£" + format(Manual_Payment_vat, ','))),
            TOTAL_VAT = TOTAL_VAT + Manual_Payment_vat

            Gross = round(Manual_Payment_vat + a.transnetpayment, 2)
            TOTAL_GROSS = TOTAL_GROSS + Gross
            array.append(str("£" + format(Gross, ','))),
    # TODO: GO#110 Vat Statement Correction 2 - End
    Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                             transtypedesc='Documentation Fee 2',
                                                             transactionsourceid__in=['SP1', 'GO1'],
                                                             transactiondate__gte=FROM_DATE,
                                                             transactiondate__lt=TO_DATE
                                                                  )

    # TODO: GO#110 Vat Statement Correction 2 - Start
    for a in Doc_Fee_2:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))), \
            array.append(str("Manual"))

            NET_Column = round(a.transnetpayment, 2)
            TOTAL_NET = TOTAL_NET + NET_Column
            array.append(str("£" + format(NET_Column, ',')))

            Manual_Payment_vat = round(a.transnetpayment * decimal.Decimal(0.2), 2)
            if agreement_type == "HP":
                array.append("£0.00")
                GROSS_Column = round(a.transnetpayment, 2)
                array.append(str("£" + format(GROSS_Column, ',')))
                TOTAL_GROSS = TOTAL_GROSS + NET_Column
            else:
                array.append(str("£" + format(Manual_Payment_vat, ','))),
                TOTAL_VAT = TOTAL_VAT + Manual_Payment_vat
                Gross = round(Manual_Payment_vat + a.transnetpayment, 2)
                array.append(str("£" + format(Gross, ','))),
                TOTAL_GROSS = TOTAL_GROSS + Gross
    # TODO: GO#110 Vat Statement Correction 2 - End

    for transaction in account_detail_rentals:

        array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),

        if transaction.transactiondate > Agreement_Start_Date:
            array.append(str("Direct Debit")),
        else: array.append(str("Manual")),

        BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                  transactionsourceid__in=['SP1', 'GO1'],
                                                                                  transtypeid__isnull=False,
                                                                                  transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                  transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Fees_Correct = BAMF_fees['transnetpayment__sum']
        if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)

        Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                        transactionsourceid__in=['SP1', 'GO1'],
                                                                        transtypeid__isnull=False,
                                                                        transtypedesc='Risk Fee',
                                                                        transactiondate=transaction.transactiondate).aggregate(
            Sum('transnetpayment'))
        Risk_Correct = Risk_fees['transnetpayment__sum']
        if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)
        print(Risk_Correct)
        account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                     transactionsourceid__in=['SP1', 'GO1'],
                                                                                     transtypeid__isnull=True,
                                                                                     transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Rentals_Correct = account_detail_rentals['transnetpayment__sum']
        # TODO: GO#110 Vat Statement Correction 2 - Start
        # if agreement_type == "HP":
        #     Rentals_Correct = round(Rentals_Correct + round((Risk_Correct)*decimal.Decimal(0.833333), 2) +Fees_Correct, 2)
        # else:
        Rentals_Correct = round(Rentals_Correct + Risk_Correct + Fees_Correct, 2)
        if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
        array.append(str("£" + format(Rentals_Correct, ','))),
        TOTAL_NET = TOTAL_NET + Rentals_Correct
        Rentals_Correct_vat = round(Rentals_Correct * decimal.Decimal(0.2), 2)
        # TODO: GO#110 Vat Statement Correction 2 - End

        if agreement_type == "HP":
            print('example')
            # TODO: GO#110 Vat Statement Correction 2 - Start
            vat_hp = round((Risk_Correct) * decimal.Decimal(0.2) + (Fees_Correct * decimal.Decimal(0.2)), 2)
            print(vat_hp)
            array.append(str("£" + format(vat_hp, ','))),
            TOTAL_VAT = TOTAL_VAT + vat_hp
        else:
            array.append(str("£" + format(Rentals_Correct_vat, ','))),
            TOTAL_VAT = TOTAL_VAT + Rentals_Correct_vat

        if agreement_type == "HP":
            installment_total = round(Rentals_Correct + (round(vat_hp, 2)), 2)
            # TODO: GO#110 Vat Statement Correction 2 - End
        else: installment_total=Rentals_Correct+Rentals_Correct_vat

        # TODO: GO#110 Vat Statement Correction 2 - Start
        array.append(str("£" + format(installment_total, ','))),
        TOTAL_GROSS = TOTAL_GROSS + installment_total



    n = len(array)
    print(n)
    x = 0
    data3 = []
    # data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
    data3.append(['Date', 'Type', 'Net', 'VAT', 'Gross'])
    while x <= n - 1:
        a = x
        b = a + 1
        c = b + 1
        d = c + 1
        e = d + 1
        data3.append([array[a], array[b], array[c], array[d], array[e]])
        x = x + 5

    t3 = Table(data3, colWidths=98, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                          ('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                          ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                                          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                                                          ])

    b2 = str("£" + format(TOTAL_NET, ','))
    d2 = str("£" + format(round(TOTAL_VAT, 2), ','))
    f2 = str("£" + format(round(TOTAL_GROSS, 2), ','))
    a2 = Paragraph("<b>Net:</b>", sample_style_sheet['BodyText'])
    c2 = Paragraph("<b>VAT:</b>", sample_style_sheet['BodyText'])
    e2 = Paragraph("<b>Total:</b>", sample_style_sheet['BodyText'])

    # TODO: GO#110 Vat Statement Correction 2 - End




    # n = len(array)
    # print(n)
    # x = 0
    # data3=[]
    # # data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
    # data3.append(['Date', 'Type', 'Net', 'VAT', 'Gross'])
    # while x <= n-1:
    #     a=x
    #     b=a+1
    #     c=b+1
    #     d=c+1
    #     e=d+1
    #     # f=e+1
    #     # g=f+1
    #     # data3.append([array[a], array[b],array[c],array[d],array[e],array[f],array[g]])
    #     data3.append([array[a], array[b],array[c],array[d],array[e]])
    #     x=x+5

    # t3 = Table(data3, colWidths=98, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
    #                                                       ('BOX',(0,0),(-1,-1),1,colors.black),
    #                                                       ('GRID',(0,0),(-1,-1),0.5,colors.black),
    #                                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    #                                                       ])
    #
    # account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
    #                                                                       transactionsourceid__in=['SP1', 'GO1'],
    #                                                                       transactiondate__gte=FROM_DATE,
    #                                                                       transactiondate__lt=TO_DATE
    #                                                                       ).aggregate(Sum('transnetpayment'))
    # account_summary_rentals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
    #                                                                         transactionsourceid__in=['SP1', 'GO1'],
    #                                                                         transactiondate__gte=FROM_DATE,
    #                                                                         transactiondate__lt=TO_DATE
    #                                                                         ).aggregate(Sum('transgrosspayment'))
    #
    # # Total_Value = account_summary_rentals['transgrosspayment__sum']
    # # Net_Value = account_detail_rentals['transnetpayment__sum']
    # #
    # # if agreement_type == "HP":
    # #     # Net_Value_vat=("£0.00")
    # #     d2 = str("£0.00")
    # # else:
    # #     print(FROM_DATE)
    # #     print(TO_DATE)
    # #
    # #     Net_Value_vat = Total_Value - Net_Value
    # #     d2 = str("£" + format(round(Net_Value_vat, 2), ','))
    # #
    # # a2 = Paragraph("<b>Net:</b>",sample_style_sheet['BodyText'])
    # # b2 = str("£"+format(round(Net_Value, 2), ','))
    # # c2 = Paragraph("<b>VAT:</b>",sample_style_sheet['BodyText'])
    # # # d2 = str("£"+format(round(Net_Value_vat, 2), ','))
    # # e2 = Paragraph("<b>Total:</b>",sample_style_sheet['BodyText'])
    # # f2 = str("£"+format(round(Total_Value, 2), ','))




    data6 = [
             ['',a2,b2],
             ['',c2,d2],
             ['',e2, f2],
             ]
    t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                                                           ('BOX', (2, 0), (-1, -1), 1, colors.black),
                                                           ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
                                                           ])

    t6._argW[0] = 4.08 * inch
    t6._argW[1] = 1.36 * inch
    t6._argW[2] = 1.36 * inch

    paragraph_2 = Paragraph(
        "<b>Frequency:</b> Monthly"
        ,
        sample_style_sheet['BodyText']
    )

    data10 = [[ "This invoice has been issued for VAT purposes only and is not a demand for payment."],
              ["VAT can only be recovered by you after each payment has been made."],
              ["VAT Reg No.974594073"],
              ["You will receive these VAT schedules annually over the primary term of your agreement."]]

    paragraph_2.hAlign = 'CENTRE'

    # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [
             [array[0], ''],
             # ['', '', ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], ''],
             [array[6], ''],
    ]

    t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                             ])
    t2._argW[0] = 5.4 * inch
    t2._argW[1] = 1.4 * inch
    # t2._argW[2] = 1.4 * inch

    c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
    d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
    e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
    f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
    g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
    h3 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
    j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])

    data7 =  [[c3, d3,i3,j3, e3, f3,""],\
             [g3, h3,""],
              ]
    t7 = Table(data7, colWidths=100, rowHeights=15, style=[
                                                           ('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                           ('BOX', (0, 0), (0, -1), .5, colors.black),
                                                           ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
                                                           ])

    t7._argW[0] = 1.4 * inch
    t7._argW[1] = 0.9 * inch
    t7._argW[2] = 0.8 * inch
    t7._argW[3] = 0.5 * inch
    t7._argW[4] = 1.0 * inch
    t7._argW[5] = 0.8 * inch
    t7._argW[6] = 1.4 * inch

    data8 = [["","VAT SCHEDULE",""],]

    t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                             ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                                                             ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
                                                                  ])

    t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])

    paragraph_4 = Paragraph(
        " "
        ,
        sample_style_sheet['BodyText']
    )
    # im2 = Image("static/assets/images/others/bluerock-footer.PNG", width=6.8 * inch, height=1 * inch)
    im2 = Image("static/assets/images/others/bluerockfooter.PNG", width=6.5 * inch, height=1.05 * inch)

    flowables.append(im)
    flowables.append(t2)
    flowables.append(paragraph_4)
    flowables.append(t7)
    flowables.append(paragraph_4)
    flowables.append(t8)
    flowables.append(t3)
    flowables.append(t6)
    count_transactions= -(count_transactions-12)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    flowables.append(t10)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    # flowables.append(PageBreak())
    flowables.append(im2)
    my_doc.build(flowables)

    pdf_NEXT_VAT_STATEMENT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'Apellio ' + agreement_id + " VAT Statement"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_NEXT_VAT_STATEMENT_value)
    return response

# def print_pdf_VAT_STATEMENT(request, agreement_id):
#     pdf_buffer = BytesIO()
#     my_doc = SimpleDocTemplate(pdf_buffer)
#     flowables = []
#
#     Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', ).first()
#     Agreement_Start_Date= Agreement_Start.transactiondate
#
#     agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
#     agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
#     account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', )
#     account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
#     account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                               transactionsourceid__in=['SP1', 'GO1'],
#                                                                               transtypeid__isnull=False).order_by(
#         'transactiondate') \
#
#     account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                  transactionsourceid__in=['SP1', 'GO1'],
#                                                                                  transtypeid__isnull=True,
#                                                                                  transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                                  transactiondate__lt='2019-12-31'
#                                                                                  ).order_by('transactiondate')
#     count_transactions = account_detail_rentals.count()
#
#
#
#     try:
#         Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
#     except:
#         Rentals2 = 0
#
#     try:
#         Rentals= account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
#         if Rentals is not None:
#             Rentals += Rentals2[account_detail_rentals.transnetpayment]
#     except:
#         pass
#
#     # Agreement Type
#     if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
#         agreement_type = 'Lease'
#         sales_tax_rate = 1.2
#     else:
#         agreement_type = 'HP'
#         sales_tax_rate = 1.0
#
#     # Agreement Payable Net of VAT
#     try:
#         agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
#     except:
#         agreement_payable_net = 0
#
#     # Add in Fees if they exist
#     try:
#         agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
#         if agreement_fees_net is not None:
#             agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
#     except:
#         pass
#
#     # Agreement Payable Gross of VAT
#     agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))
#
#     sample_style_sheet = getSampleStyleSheet()
#     sample_style_sheet.list()
#     data3 = ("", "")
#
#     first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")
#
#     # get Number of Document Fees
#     try:
#         doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                             transactionsourceid__in=['SP1', 'GO1'],
#                                                                             transactiondate__lt=Agreement_Start_Date).count()
#     except:
#         doc_fee_count = 0
#     # get Number of Primaries
#     try:
#         primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                             transactionsourceid__in=['SP1', 'GO1'],
#                                                                             transtypeid__isnull=True,
#                                                                             transactiondate__gte=Agreement_Start_Date).count()
#     except:
#         primary_count = 0
#
#     # get Number of Secondaries
#     try:
#         secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3','GO3']).count()
#     except:
#         secondary_count = 0
#
#     for row in account_detail:
#         row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)
#
#     agreement_instalment_gross = agreement_detail.agreementinstalmentnet
#     if agreement_detail.agreementinstalmentvat is not None:
#         agreement_instalment_gross += agreement_detail.agreementinstalmentvat
#     if agreement_detail.agreementinstalmentins is not None:
#         agreement_instalment_gross += agreement_detail.agreementinstalmentins
#
#     array = []
#     Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transtypedesc='Documentation Fee',
#                                                                          transactionsourceid__in=['SP1', 'GO1']
#                                                                   ,
#                                                                          transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                          transactiondate__lt='2019-12-31'
#                                                                   )
#     for a in Manual_Payment:
#         if a.transactiondate is not None:
#             array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
#             array.append(str("Manual"))
#             array.append(str('£0.00'))
#             array.append(str('£0.00'))
#             array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
#             if agreement_type == "HP":
#                 array.append("£0.00")
#                 array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             else:
#                 array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
#                 Gross = Manual_Payment_vat+ a.transnetpayment
#                 array.append(str("£" + format(round(Gross, 2), ','))),
#
#     Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transtypedesc='Documentation Fee 2',
#                                                                          transactionsourceid__in=['SP1', 'GO1']
#                                                                   ,
#                                                                          transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                          transactiondate__lt='2019-12-31'
#                                                                   )
#
#     for a in Doc_Fee_2:
#         if a.transactiondate is not None:
#             array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
#             array.append(str("Manual"))
#
#             array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
#             if agreement_type == "HP":
#                 array.append("£0.00")
#                 array.append(str('£0.00'))
#                 array.append(str('£0.00'))
#                 array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             else:
#                 array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
#                 Gross = Manual_Payment_vat+ a.transnetpayment
#                 array.append(str('£0.00'))
#                 array.append(str('£0.00'))
#                 array.append(str("£" + format(round(Gross, 2), ','))),
#
#     for transaction in account_detail_rentals:
#         array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),
#         print(transaction.transactiondate.strftime("%d/%m/%Y"))
#         print(Agreement_Start_Date.strftime("%d/%m/%Y"))
#
#         if transaction.transactiondate > Agreement_Start_Date:
#             array.append(str("Direct Debit")),
#         else: array.append(str("Manual")),
#
#         BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                   transactionsourceid__in=['SP1', 'GO1'],
#                                                                                   transtypeid__isnull=False,
#                                                                                   transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
#                                                                                   transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
#         Fees_Correct = BAMF_fees['transnetpayment__sum']
#         if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)
#
#         Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                         transactionsourceid__in=['SP1', 'GO1'],
#                                                                         transtypeid__isnull=False,
#                                                                         transtypedesc='Risk Fee',
#                                                                         transactiondate=transaction.transactiondate).aggregate(
#             Sum('transnetpayment'))
#         Risk_Correct = Risk_fees['transnetpayment__sum']
#         if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)
#
#
#
#         account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                      transactionsourceid__in=['SP1', 'GO1'],
#                                                                                      transtypeid__isnull=True,
#                                                                                      transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
#         Rentals_Correct = account_detail_rentals['transnetpayment__sum']
#         Rentals_Correct = Rentals_Correct + Risk_Correct
#         if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
#         array.append(str("£"+format(round(Rentals_Correct, 2), ','))),
#         Rentals_Correct_vat = Rentals_Correct *decimal.Decimal(0.2)
#         if agreement_type == "HP":
#             array.append("£0.00")
#         else: array.append(str("£"+format(round(Rentals_Correct_vat, 2), ','))),
#
#         array.append(str("£"+format(round(Fees_Correct, 2), ','))),
#         Fees_Correct_vat = Fees_Correct * decimal.Decimal(0.2)
#         if agreement_type == "HP":
#             array.append("£0.00")
#         else: array.append(str("£"+format(round(Fees_Correct_vat, 2), ','))),
#
#         if agreement_type == "HP":
#             installment_total = Rentals_Correct + Fees_Correct
#         else: installment_total=Rentals_Correct+Fees_Correct+Rentals_Correct_vat+Fees_Correct_vat
#
#         array.append(str("£"+format(round(installment_total, 2), ','))),
#
#     n = len(array)
#     x = 0
#     data3=[]
#
#     data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
#     while x <= n-1:
#         a=x
#         b=a+1
#         c=b+1
#         d=c+1
#         e=d+1
#         f=e+1
#         g=f+1
#         data3.append([array[a], array[b],array[c],array[d],array[e],array[f],array[g]])
#         x=x+7
#
#     t3 = Table(data3, colWidths=70, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
#                                                           ('BOX',(0,0),(-1,-1),1,colors.black),
#                                                           ('GRID',(0,0),(-1,-1),0.5,colors.black),
#                                                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
#                                                           ])
#
#     account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                  transactionsourceid__in=['SP1', 'GO1'],
#                                                                                  transactiondate__gte = '2019-01-01',
#                                                                                  transactiondate__lt = '2019-12-31'
#                                                                                  ).aggregate(Sum('transnetpayment'))
#     account_summary_rentals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
#                                                                           transactionsourceid__in=['SP1', 'GO1'],
#                                                                           transactiondate__gte='2019-01-01',
#                                                                           transactiondate__lt='2019-12-31'
#                                                                           ).aggregate(Sum('transgrosspayment'))
#
#     Total_Value = account_summary_rentals['transgrosspayment__sum']
#     Net_Value = account_detail_rentals['transnetpayment__sum']
#
#     if agreement_type == "HP":
#         # Net_Value_vat=("£0.00")
#         d2 = str("£0.00")
#     else:
#         Net_Value_vat = Total_Value - Net_Value
#         d2 = str("£" + format(round(Net_Value_vat, 2), ','))
#
#     a2 = Paragraph("<b>Net:</b>",sample_style_sheet['BodyText'])
#     b2 = str("£"+format(round(Net_Value, 2), ','))
#     c2 = Paragraph("<b>VAT:</b>",sample_style_sheet['BodyText'])
#     # d2 = str("£"+format(round(Net_Value_vat, 2), ','))
#     e2 = Paragraph("<b>Total:</b>",sample_style_sheet['BodyText'])
#     f2 = str("£"+format(round(Total_Value, 2), ','))
#
#     data6 = [
#              ['',a2,b2],
#              ['',c2,d2],
#              ['',e2, f2],
#              ]
#     t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
#                                                            ('BOX', (2, 0), (-1, -1), 1, colors.black),
#                                                            ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
#                                                            ])
#
#     t6._argW[0] = 4.86 * inch
#     t6._argW[1] = .97 * inch
#     t6._argW[2] = .97 * inch
#
#     paragraph_2 = Paragraph(
#         "<b>Frequency:</b> Monthly"
#         ,
#         sample_style_sheet['BodyText']
#     )
#
#     data10 = [[ "This invoice has been issued for VAT purposes only and is not a demand for payment."],
#               ["VAT can only be recovered by you after each payment has been made."],
#               ["VAT Reg No.974594073"],
#               ["You will receive these VAT schedules annually over the primary term of your agreement."]]
#
#     paragraph_2.hAlign = 'CENTRE'
#
#     # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     im.hAlign = 'RIGHT'
#
#     if agreement_customer.customeraddress1:
#         address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
#     else:
#         address1 = ''
#     if agreement_customer.customeraddress2:
#         address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
#     else:
#         address2 = ''
#     if agreement_customer.customeraddress3:
#         address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
#     else:
#         address3 = ''
#     if agreement_customer.customeraddress4:
#         address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
#     else:
#         address4 = ''
#     if agreement_customer.customeraddress5:
#         address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
#     else:
#         address5 = ''
#     if agreement_customer.customerpostcode:
#         postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
#     array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
#     while ('' in array): array.remove('')
#     array.append('')
#     array.append('')
#     array.append('')
#     array.append('')
#     array.append('')
#
#     data2 = [
#              [array[0], ''],
#              # ['', '', ''],
#              [array[1], ''],
#              [array[2], ''],
#              [array[3], ''],
#              [array[4], ''],
#              [array[5], ''],
#              [array[6], ''],
#     ]
#
#     t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
#                                                              ])
#     t2._argW[0] = 5.4 * inch
#     t2._argW[1] = 1.4 * inch
#     # t2._argW[2] = 1.4 * inch
#
#     c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
#     d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
#     e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
#     f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
#     g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
#     h3 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
#     i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
#     j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])
#
#     data7 =  [[c3, d3,i3,j3, e3, f3,""],\
#              [g3, h3,""],
#               ]
#     t7 = Table(data7, colWidths=100, rowHeights=15, style=[
#                                                            ('BOX', (0, 0), (-2, -1), 1, colors.black),
#                                                            ('BOX', (0, 0), (0, -1), .5, colors.black),
#                                                            ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
#                                                            ])
#
#     t7._argW[0] = 1.4 * inch
#     t7._argW[1] = 0.9 * inch
#     t7._argW[2] = 0.8 * inch
#     t7._argW[3] = 0.5 * inch
#     t7._argW[4] = 1.0 * inch
#     t7._argW[5] = 0.8 * inch
#     t7._argW[6] = 1.4 * inch
#
#     data8 = [["","VAT SCHEDULE",""],]
#
#     t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
#                                                              ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
#                                                              ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
#                                                                   ])
#
#     t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])
#
#     paragraph_4 = Paragraph(
#         " "
#         ,
#         sample_style_sheet['BodyText']
#     )
#     # im2 = Image("static/assets/images/others/bluerock-footer.PNG", width=6.8 * inch, height=1 * inch)
#     im2 = Image("static/assets/images/others/bluerockfooter.PNG", width=6.8 * inch, height=1.3 * inch)
#
#     flowables.append(im)
#     flowables.append(t2)
#     flowables.append(paragraph_4)
#     flowables.append(t7)
#     flowables.append(paragraph_4)
#     flowables.append(t8)
#     flowables.append(t3)
#     flowables.append(t6)
#     count_transactions= -(count_transactions-12)
#     if count_transactions != 0:
#         for n in range(count_transactions):
#             flowables.append(paragraph_4)
#     flowables.append(t10)
#     if count_transactions != 0:
#         for n in range(count_transactions):
#             flowables.append(paragraph_4)
#     flowables.append(im2)
#     my_doc.build(flowables)
#
#     pdf_VAT_STATEMENT_value = pdf_buffer.getvalue()
#     pdf_buffer.close()
#     response = HttpResponse(content_type='application.pdf')
#
#     filename = 'GO ' + agreement_id + " VAT Statement"
#
#     response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename
#
#     response.write(pdf_VAT_STATEMENT_value)
#     return response
# # Card 72 Multiple year VAT Statements
# def print_pdf_FULL_VAT_STATEMENT(request, agreement_id):
#     pdf_buffer = BytesIO()
#     my_doc = SimpleDocTemplate(pdf_buffer)
#     flowables = []
#
#     Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', ).first()
#     Agreement_Start_Date= Agreement_Start.transactiondate
#
#     agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
#     agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
#     account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', )
#     account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
#     account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                               transactionsourceid__in=['SP1', 'GO1'],
#                                                                               transtypeid__isnull=False).order_by(
#         'transactiondate') \
#
#     account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                  transactionsourceid__in=['SP1', 'GO1'],
#                                                                                  transtypeid__isnull=True,
#                                                                                  transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                                  transactiondate__lt='2119-12-31'
#                                                                                  ).order_by('transactiondate')
#     count_transactions = account_detail_rentals.count()
#
#
#
#     try:
#         Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
#     except:
#         Rentals2 = 0
#
#     try:
#         Rentals= account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
#         if Rentals is not None:
#             Rentals += Rentals2[account_detail_rentals.transnetpayment]
#     except:
#         pass
#
#     # Agreement Type
#     if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
#         agreement_type = 'Lease'
#         sales_tax_rate = 1.2
#     else:
#         agreement_type = 'HP'
#         sales_tax_rate = 1.0
#
#     # Agreement Payable Net of VAT
#     try:
#         agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
#     except:
#         agreement_payable_net = 0
#
#     # Add in Fees if they exist
#     try:
#         agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
#         if agreement_fees_net is not None:
#             agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
#     except:
#         pass
#
#     # Agreement Payable Gross of VAT
#     agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))
#
#     sample_style_sheet = getSampleStyleSheet()
#     sample_style_sheet.list()
#     data3 = ("", "")
#
#     first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")
#
#     # get Number of Document Fees
#     try:
#         doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                             transactionsourceid__in=['SP1', 'GO1'],
#                                                                             transactiondate__lt=Agreement_Start_Date).count()
#     except:
#         doc_fee_count = 0
#     # get Number of Primaries
#     try:
#         primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                             transactionsourceid__in=['SP1', 'GO1'],
#                                                                             transtypeid__isnull=True,
#                                                                             transactiondate__gte=Agreement_Start_Date).count()
#     except:
#         primary_count = 0
#
#     # get Number of Secondaries
#     try:
#         secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3','GO3']).count()
#     except:
#         secondary_count = 0
#
#     for row in account_detail:
#         row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)
#
#     agreement_instalment_gross = agreement_detail.agreementinstalmentnet
#     if agreement_detail.agreementinstalmentvat is not None:
#         agreement_instalment_gross += agreement_detail.agreementinstalmentvat
#     if agreement_detail.agreementinstalmentins is not None:
#         agreement_instalment_gross += agreement_detail.agreementinstalmentins
#
#     array = []
#     Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transtypedesc='Documentation Fee',
#                                                                          transactionsourceid__in=['SP1', 'GO1']
#                                                                   ,
#                                                                          transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                          transactiondate__lt='2119-12-31'
#                                                                   )
#     for a in Manual_Payment:
#         if a.transactiondate is not None:
#             array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
#             array.append(str("Manual"))
#             array.append(str('£0.00'))
#             array.append(str('£0.00'))
#             array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
#             if agreement_type == "HP":
#                 array.append("£0.00")
#                 array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             else:
#                 array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
#                 Gross = Manual_Payment_vat+ a.transnetpayment
#                 array.append(str("£" + format(round(Gross, 2), ','))),
#
#     Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                          transtypedesc='Documentation Fee 2',
#                                                                          transactionsourceid__in=['SP1', 'GO1']
#                                                                   ,
#                                                                          transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
#                                                                          transactiondate__lt='2119-12-31'
#                                                                   )
#
#     for a in Doc_Fee_2:
#         if a.transactiondate is not None:
#             array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
#             array.append(str("Manual"))
#
#             array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
#             if agreement_type == "HP":
#                 array.append("£0.00")
#                 array.append(str('£0.00'))
#                 array.append(str('£0.00'))
#                 array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
#             else:
#                 array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
#                 Gross = Manual_Payment_vat+ a.transnetpayment
#                 array.append(str('£0.00'))
#                 array.append(str('£0.00'))
#                 array.append(str("£" + format(round(Gross, 2), ','))),
#
#     for transaction in account_detail_rentals:
#         array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),
#         print(transaction.transactiondate.strftime("%d/%m/%Y"))
#         print(Agreement_Start_Date.strftime("%d/%m/%Y"))
#
#         if transaction.transactiondate > Agreement_Start_Date:
#             array.append(str("Direct Debit")),
#         else: array.append(str("Manual")),
#
#         BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                   transactionsourceid__in=['SP1', 'GO1'],
#                                                                                   transtypeid__isnull=False,
#                                                                                   transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
#                                                                                   transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
#         Fees_Correct = BAMF_fees['transnetpayment__sum']
#         if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)
#
#         Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                         transactionsourceid__in=['SP1', 'GO1'],
#                                                                         transtypeid__isnull=False,
#                                                                         transtypedesc='Risk Fee',
#                                                                         transactiondate=transaction.transactiondate).aggregate(
#             Sum('transnetpayment'))
#         Risk_Correct = Risk_fees['transnetpayment__sum']
#         if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)
#
#
#
#         account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                      transactionsourceid__in=['SP1', 'GO1'],
#                                                                                      transtypeid__isnull=True,
#                                                                                      transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
#         Rentals_Correct = account_detail_rentals['transnetpayment__sum']
#         Rentals_Correct = Rentals_Correct + Risk_Correct
#         if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
#         array.append(str("£"+format(round(Rentals_Correct, 2), ','))),
#         Rentals_Correct_vat = Rentals_Correct *decimal.Decimal(0.2)
#         if agreement_type == "HP":
#             array.append("£0.00")
#         else: array.append(str("£"+format(round(Rentals_Correct_vat, 2), ','))),
#
#         array.append(str("£"+format(round(Fees_Correct, 2), ','))),
#         Fees_Correct_vat = Fees_Correct * decimal.Decimal(0.2)
#         if agreement_type == "HP":
#             array.append("£0.00")
#         else: array.append(str("£"+format(round(Fees_Correct_vat, 2), ','))),
#
#         if agreement_type == "HP":
#             installment_total = Rentals_Correct + Fees_Correct
#         else: installment_total=Rentals_Correct+Fees_Correct+Rentals_Correct_vat+Fees_Correct_vat
#
#         array.append(str("£"+format(round(installment_total, 2), ','))),
#
#     n = len(array)
#     x = 0
#     data3=[]
#
#     data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
#     while x <= n-1:
#         a=x
#         b=a+1
#         c=b+1
#         d=c+1
#         e=d+1
#         f=e+1
#         g=f+1
#         data3.append([array[a], array[b],array[c],array[d],array[e],array[f],array[g]])
#         x=x+7
#
#     t3 = Table(data3, colWidths=70, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
#                                                           ('BOX',(0,0),(-1,-1),1,colors.black),
#                                                           ('GRID',(0,0),(-1,-1),0.5,colors.black),
#                                                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
#                                                           ])
#
#     account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
#                                                                                  transactionsourceid__in=['SP1', 'GO1'],
#                                                                                  transactiondate__gte = '2019-01-01',
#                                                                                  transactiondate__lt = '2119-12-31'
#                                                                                  ).aggregate(Sum('transnetpayment'))
#     account_summary_rentals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
#                                                                           transactionsourceid__in=['SP1', 'GO1'],
#                                                                           transactiondate__gte='2019-01-01',
#                                                                           transactiondate__lt='2119-12-31'
#                                                                           ).aggregate(Sum('transgrosspayment'))
#
#     Total_Value = account_summary_rentals['transgrosspayment__sum']
#     Net_Value = account_detail_rentals['transnetpayment__sum']
#
#     if agreement_type == "HP":
#         # Net_Value_vat=("£0.00")
#         d2 = str("£0.00")
#     else:
#         Net_Value_vat = Total_Value - Net_Value
#         d2 = str("£" + format(round(Net_Value_vat, 2), ','))
#
#     a2 = Paragraph("<b>Net:</b>",sample_style_sheet['BodyText'])
#     b2 = str("£"+format(round(Net_Value, 2), ','))
#     c2 = Paragraph("<b>VAT:</b>",sample_style_sheet['BodyText'])
#     # d2 = str("£"+format(round(Net_Value_vat, 2), ','))
#     e2 = Paragraph("<b>Total:</b>",sample_style_sheet['BodyText'])
#     f2 = str("£"+format(round(Total_Value, 2), ','))
#
#     data6 = [
#              ['',a2,b2],
#              ['',c2,d2],
#              ['',e2, f2],
#              ]
#     t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
#                                                            ('BOX', (2, 0), (-1, -1), 1, colors.black),
#                                                            ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
#                                                            ])
#
#     t6._argW[0] = 4.86 * inch
#     t6._argW[1] = .97 * inch
#     t6._argW[2] = .97 * inch
#
#     paragraph_2 = Paragraph(
#         "<b>Frequency:</b> Monthly"
#         ,
#         sample_style_sheet['BodyText']
#     )
#
#     data10 = [[ "This invoice has been issued for VAT purposes only and is not a demand for payment."],
#               ["VAT can only be recovered by you after each payment has been made."],
#               ["VAT Reg No.974594073"],
#               ["You will receive these VAT schedules annually over the primary term of your agreement."]]
#
#     paragraph_2.hAlign = 'CENTRE'
#
#     # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
#     im.hAlign = 'RIGHT'
#
#     if agreement_customer.customeraddress1:
#         address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
#     else:
#         address1 = ''
#     if agreement_customer.customeraddress2:
#         address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
#     else:
#         address2 = ''
#     if agreement_customer.customeraddress3:
#         address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
#     else:
#         address3 = ''
#     if agreement_customer.customeraddress4:
#         address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
#     else:
#         address4 = ''
#     if agreement_customer.customeraddress5:
#         address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
#     else:
#         address5 = ''
#     if agreement_customer.customerpostcode:
#         postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
#     array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
#     while ('' in array): array.remove('')
#     array.append('')
#     array.append('')
#     array.append('')
#     array.append('')
#     array.append('')
#
#     data2 = [
#              [array[0], ''],
#              # ['', '', ''],
#              [array[1], ''],
#              [array[2], ''],
#              [array[3], ''],
#              [array[4], ''],
#              [array[5], ''],
#              [array[6], ''],
#     ]
#
#     t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
#                                                              ])
#     t2._argW[0] = 5.4 * inch
#     t2._argW[1] = 1.4 * inch
#     # t2._argW[2] = 1.4 * inch
#
#     c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
#     d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
#     e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
#     f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
#     g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
#     h3 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
#     i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
#     j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])
#
#     data7 =  [[c3, d3,i3,j3, e3, f3,""],\
#              [g3, h3,""],
#               ]
#     t7 = Table(data7, colWidths=100, rowHeights=15, style=[
#                                                            ('BOX', (0, 0), (-2, -1), 1, colors.black),
#                                                            ('BOX', (0, 0), (0, -1), .5, colors.black),
#                                                            ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
#                                                            ])
#
#     t7._argW[0] = 1.4 * inch
#     t7._argW[1] = 0.9 * inch
#     t7._argW[2] = 0.8 * inch
#     t7._argW[3] = 0.5 * inch
#     t7._argW[4] = 1.0 * inch
#     t7._argW[5] = 0.8 * inch
#     t7._argW[6] = 1.4 * inch
#
#     data8 = [["","VAT SCHEDULE",""],]
#
#     t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
#                                                              ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
#                                                              ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
#                                                                   ])
#
#     t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])
#
#     paragraph_4 = Paragraph(
#         " "
#         ,
#         sample_style_sheet['BodyText']
#     )
#     # im2 = Image("static/assets/images/others/bluerock-footer.PNG", width=6.8 * inch, height=1 * inch)
#     im2 = Image("static/assets/images/others/bluerockfooter.PNG", width=6.8 * inch, height=1.3 * inch)
#
#     flowables.append(im)
#     flowables.append(t2)
#     flowables.append(paragraph_4)
#     flowables.append(t7)
#     flowables.append(paragraph_4)
#     flowables.append(t8)
#     flowables.append(t3)
#     flowables.append(t6)
#     count_transactions= -(count_transactions-12)
#     if count_transactions != 0:
#         for n in range(count_transactions):
#             flowables.append(paragraph_4)
#     flowables.append(t10)
#     if count_transactions != 0:
#         for n in range(count_transactions):
#             flowables.append(paragraph_4)
#     flowables.append(im2)
#     my_doc.build(flowables)
#
#     pdf_VAT_STATEMENT_value = pdf_buffer.getvalue()
#     pdf_buffer.close()
#     response = HttpResponse(content_type='application.pdf')
#
#     filename = 'GO ' + agreement_id + " VAT Statement"
#
#     response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename
#
#     response.write(pdf_VAT_STATEMENT_value)
#     return response

def print_pdf_VAT_STATEMENT(request, agreement_id):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                               transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', ).first()
    Agreement_Start_Date= Agreement_Start.transactiondate

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', )
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False).order_by(
        'transactiondate') \

    account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                                 transtypeid__isnull=True,
                                                                                 transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                                 transactiondate__lt='2019-12-31'
                                                                                 ).order_by('transactiondate')
    count_transactions = account_detail_rentals.count()



    try:
        Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        Rentals2 = 0

    try:
        Rentals= account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
        if Rentals is not None:
            Rentals += Rentals2[account_detail_rentals.transnetpayment]
    except:
        pass

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    # Agreement Payable Net of VAT
    try:
        agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        agreement_payable_net = 0

    # Add in Fees if they exist
    try:
        agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
        if agreement_fees_net is not None:
            agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
    except:
        pass

    # Agreement Payable Gross of VAT
    agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()
    data3 = ("", "")

    first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=Agreement_Start_Date).count()
    except:
        doc_fee_count = 0
    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=Agreement_Start_Date).count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3','GO3']).count()
    except:
        secondary_count = 0

    for row in account_detail:
        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    agreement_instalment_gross = agreement_detail.agreementinstalmentnet
    if agreement_detail.agreementinstalmentvat is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    array = []
    Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transtypedesc='Documentation Fee',
                                                                         transactionsourceid__in=['SP1', 'GO1']
                                                                  ,
                                                                         transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                         transactiondate__lt='2019-12-31'
                                                                  )
    for a in Manual_Payment:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
            array.append(str("Manual"))
            # array.append(str('£0.00'))
            # array.append(str('£0.00'))
            array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
            if agreement_type == "HP":
                array.append("£0.00")
                array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            else:
                array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
                Gross = Manual_Payment_vat+ a.transnetpayment
                array.append(str("£" + format(round(Gross, 2), ','))),

    Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transtypedesc='Documentation Fee 2',
                                                                         transactionsourceid__in=['SP1', 'GO1']
                                                                  ,
                                                                         transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                         transactiondate__lt='2019-12-31'
                                                                  )

    for a in Doc_Fee_2:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
            array.append(str("Manual"))

            array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
            if agreement_type == "HP":
                array.append("£0.00")
                # array.append(str('£0.00'))
                # array.append(str('£0.00'))
                array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            else:
                array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
                Gross = Manual_Payment_vat+ a.transnetpayment
                # array.append(str('£0.00'))
                # array.append(str('£0.00'))
                array.append(str("£" + format(round(Gross, 2), ','))),

    for transaction in account_detail_rentals:

        array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),
        print(transaction.transactiondate.strftime("%d/%m/%Y"))
        print(Agreement_Start_Date.strftime("%d/%m/%Y"))

        if transaction.transactiondate > Agreement_Start_Date:
            array.append(str("Direct Debit")),
        else: array.append(str("Manual")),

        BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                  transactionsourceid__in=['SP1', 'GO1'],
                                                                                  transtypeid__isnull=False,
                                                                                  transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                  transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Fees_Correct = BAMF_fees['transnetpayment__sum']
        if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)

        Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                        transactionsourceid__in=['SP1', 'GO1'],
                                                                        transtypeid__isnull=False,
                                                                        transtypedesc='Risk Fee',
                                                                        transactiondate=transaction.transactiondate).aggregate(
            Sum('transnetpayment'))
        Risk_Correct = Risk_fees['transnetpayment__sum']
        if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)

        account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                     transactionsourceid__in=['SP1', 'GO1'],
                                                                                     transtypeid__isnull=True,
                                                                                     transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Rentals_Correct = account_detail_rentals['transnetpayment__sum']
        Rentals_Correct = Rentals_Correct + Risk_Correct
        if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
        array.append(str("£"+format(round(Rentals_Correct, 2), ','))),
        Rentals_Correct_vat = Rentals_Correct *decimal.Decimal(0.2)
        if agreement_type == "HP":
            array.append("£0.00")
        else: array.append(str("£"+format(round(Rentals_Correct_vat, 2), ','))),

        # array.append(str("£"+format(round(Fees_Correct, 2), ','))),
        Fees_Correct_vat = Fees_Correct * decimal.Decimal(0.2)
        # if agreement_type == "HP":
        #     array.append("£0.00")
        # else: array.append(str("£"+format(round(Fees_Correct_vat, 2), ','))),

        if agreement_type == "HP":
            installment_total = Rentals_Correct
        # else: installment_total=Rentals_Correct+Fees_Correct+Rentals_Correct_vat+Fees_Correct_vat
        else: installment_total=Rentals_Correct+Rentals_Correct_vat

        array.append(str("£"+format(round(installment_total, 2), ','))),

    n = len(array)
    print(n)
    x = 0
    data3=[]
    # data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
    data3.append(['Date', 'Type', 'Net', 'VAT', 'Gross'])
    while x <= n-1:
        a=x
        b=a+1
        c=b+1
        d=c+1
        e=d+1
        # f=e+1
        # g=f+1
        # data3.append([array[a], array[b],array[c],array[d],array[e],array[f],array[g]])
        data3.append([array[a], array[b],array[c],array[d],array[e]])
        x=x+5

    t3 = Table(data3, colWidths=98, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                          ('BOX',(0,0),(-1,-1),1,colors.black),
                                                          ('GRID',(0,0),(-1,-1),0.5,colors.black),
                                                          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                                                          ])

    account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                                 transactiondate__gte = '2019-01-01',
                                                                                 transactiondate__lt = '2019-12-31'
                                                                                 ).aggregate(Sum('transnetpayment'))
    account_summary_rentals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactionsourceid__in=['SP1', 'GO1'],
                                                                          transactiondate__gte='2019-01-01',
                                                                          transactiondate__lt='2019-12-31'
                                                                          ).aggregate(Sum('transgrosspayment'))

    Total_Value = account_summary_rentals['transgrosspayment__sum']
    Net_Value = account_detail_rentals['transnetpayment__sum']

    if agreement_type == "HP":
        # Net_Value_vat=("£0.00")
        d2 = str("£0.00")
    else:
        Net_Value_vat = Total_Value - Net_Value
        d2 = str("£" + format(round(Net_Value_vat, 2), ','))

    a2 = Paragraph("<b>Net:</b>",sample_style_sheet['BodyText'])
    b2 = str("£"+format(round(Net_Value, 2), ','))
    c2 = Paragraph("<b>VAT:</b>",sample_style_sheet['BodyText'])
    # d2 = str("£"+format(round(Net_Value_vat, 2), ','))
    e2 = Paragraph("<b>Total:</b>",sample_style_sheet['BodyText'])
    f2 = str("£"+format(round(Total_Value, 2), ','))

    data6 = [
             ['',a2,b2],
             ['',c2,d2],
             ['',e2, f2],
             ]
    t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                                                           ('BOX', (2, 0), (-1, -1), 1, colors.black),
                                                           ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
                                                           ])

    t6._argW[0] = 4.08 * inch
    t6._argW[1] = 1.36 * inch
    t6._argW[2] = 1.36 * inch

    paragraph_2 = Paragraph(
        "<b>Frequency:</b> Monthly"
        ,
        sample_style_sheet['BodyText']
    )

    data10 = [[ "This invoice has been issued for VAT purposes only and is not a demand for payment."],
              ["VAT can only be recovered by you after each payment has been made."],
              ["VAT Reg No.974594073"],
              ["You will receive these VAT schedules annually over the primary term of your agreement."]]

    paragraph_2.hAlign = 'CENTRE'

    # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [
             [array[0], ''],
             # ['', '', ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], ''],
             [array[6], ''],
    ]

    t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                             ])
    t2._argW[0] = 5.4 * inch
    t2._argW[1] = 1.4 * inch
    # t2._argW[2] = 1.4 * inch

    c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
    d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
    e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
    f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
    g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
    h3 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
    j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])

    data7 =  [[c3, d3,i3,j3, e3, f3,""],\
             [g3, h3,""],
              ]
    t7 = Table(data7, colWidths=100, rowHeights=15, style=[
                                                           ('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                           ('BOX', (0, 0), (0, -1), .5, colors.black),
                                                           ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
                                                           ])

    t7._argW[0] = 1.4 * inch
    t7._argW[1] = 0.9 * inch
    t7._argW[2] = 0.8 * inch
    t7._argW[3] = 0.5 * inch
    t7._argW[4] = 1.0 * inch
    t7._argW[5] = 0.8 * inch
    t7._argW[6] = 1.4 * inch

    data8 = [["","VAT SCHEDULE",""],]

    t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                             ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                                                             ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
                                                                  ])

    t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])

    paragraph_4 = Paragraph(
        " "
        ,
        sample_style_sheet['BodyText']
    )
    # im2 = Image("static/assets/images/others/bluerock-footer.PNG", width=6.8 * inch, height=1 * inch)
    im2 = Image("static/assets/images/others/bluerockfooter.PNG", width=6.8 * inch, height=1.3 * inch)

    flowables.append(im)
    flowables.append(t2)
    flowables.append(paragraph_4)
    flowables.append(t7)
    flowables.append(paragraph_4)
    flowables.append(t8)
    flowables.append(t3)
    flowables.append(t6)
    count_transactions= -(count_transactions-12)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    flowables.append(t10)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    flowables.append(im2)
    my_doc.build(flowables)

    pdf_VAT_STATEMENT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " VAT Statement"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_VAT_STATEMENT_value)
    return response

# Card 72 Multiple year VAT Statements
def print_pdf_FULL_VAT_STATEMENT(request, agreement_id):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                               transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', ).first()
    Agreement_Start_Date= Agreement_Start.transactiondate

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transactionsourceid__in=['SP1', 'GO1']).order_by('transactiondate', )
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False).order_by(
        'transactiondate') \

    account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                                 transtypeid__isnull=True,
                                                                                 transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                                 transactiondate__lt='2119-12-31'
                                                                                 ).order_by('transactiondate')
    count_transactions = account_detail_rentals.count()



    try:
        Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        Rentals2 = 0

    try:
        Rentals= account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
        if Rentals is not None:
            Rentals += Rentals2[account_detail_rentals.transnetpayment]
    except:
        pass

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    # Agreement Payable Net of VAT
    try:
        agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
    except:
        agreement_payable_net = 0

    # Add in Fees if they exist
    try:
        agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
        if agreement_fees_net is not None:
            agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
    except:
        pass

    # Agreement Payable Gross of VAT
    agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()
    data3 = ("", "")

    first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transactiondate__lt=Agreement_Start_Date).count()
    except:
        doc_fee_count = 0
    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=Agreement_Start_Date).count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3','GO3']).count()
    except:
        secondary_count = 0

    for row in account_detail:
        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    agreement_instalment_gross = agreement_detail.agreementinstalmentnet
    if agreement_detail.agreementinstalmentvat is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    array = []
    Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transtypedesc='Documentation Fee',
                                                                         transactionsourceid__in=['SP1', 'GO1']
                                                                  ,
                                                                         transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                         transactiondate__lt='2119-12-31'
                                                                  )
    for a in Manual_Payment:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
            array.append(str("Manual"))
            # array.append(str('£0.00'))
            # array.append(str('£0.00'))
            array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
            if agreement_type == "HP":
                array.append("£0.00")
                array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            else:
                array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
                Gross = Manual_Payment_vat+ a.transnetpayment
                array.append(str("£" + format(round(Gross, 2), ','))),

    Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                         transtypedesc='Documentation Fee 2',
                                                                         transactionsourceid__in=['SP1', 'GO1']
                                                                  ,
                                                                         transactiondate__gte='2019-01-01', #TODO: Fix Dates on selection
                                                                         transactiondate__lt='2119-12-31'
                                                                  )

    for a in Doc_Fee_2:
        if a.transactiondate is not None:
            array.append(str((a.transactiondate.strftime("%d/%m/%Y")))),\
            array.append(str("Manual"))

            array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            Manual_Payment_vat= a.transnetpayment*decimal.Decimal(0.2)
            if agreement_type == "HP":
                array.append("£0.00")
                # array.append(str('£0.00'))
                # array.append(str('£0.00'))
                array.append(str("£" + format(round(a.transnetpayment, 2), ',')))
            else:
                array.append(str("£" + format(round(Manual_Payment_vat, 2), ','))),
                Gross = Manual_Payment_vat+ a.transnetpayment
                # array.append(str('£0.00'))
                # array.append(str('£0.00'))
                array.append(str("£" + format(round(Gross, 2), ','))),

    for transaction in account_detail_rentals:
        array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),
        print(transaction.transactiondate.strftime("%d/%m/%Y"))
        print(Agreement_Start_Date.strftime("%d/%m/%Y"))

        if transaction.transactiondate > Agreement_Start_Date:
            array.append(str("Direct Debit")),
        else: array.append(str("Manual")),

        BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                  transactionsourceid__in=['SP1', 'GO1'],
                                                                                  transtypeid__isnull=False,
                                                                                  transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                  transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Fees_Correct = BAMF_fees['transnetpayment__sum']
        if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)

        Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                        transactionsourceid__in=['SP1', 'GO1'],
                                                                        transtypeid__isnull=False,
                                                                        transtypedesc='Risk Fee',
                                                                        transactiondate=transaction.transactiondate).aggregate(
            Sum('transnetpayment'))
        Risk_Correct = Risk_fees['transnetpayment__sum']
        if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)



        account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                     transactionsourceid__in=['SP1', 'GO1'],
                                                                                     transtypeid__isnull=True,
                                                                                     transactiondate=transaction.transactiondate).aggregate(Sum('transnetpayment'))
        Rentals_Correct = account_detail_rentals['transnetpayment__sum']
        Rentals_Correct = Rentals_Correct + Risk_Correct + Fees_Correct
        # Rentals_Correct = Rentals_Correct + Risk_Correct
        if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
        array.append(str("£"+format(round(Rentals_Correct, 2), ','))),
        Rentals_Correct_vat = Rentals_Correct *decimal.Decimal(0.2)
        if agreement_type == "HP":
            array.append("£0.00")
        else: array.append(str("£"+format(round(Rentals_Correct_vat, 2), ','))),

        # array.append(str("£"+format(round(Fees_Correct, 2), ','))),
        Fees_Correct_vat = Fees_Correct * decimal.Decimal(0.2)
        # if agreement_type == "HP":
        #     array.append("£0.00")
        # else: array.append(str("£"+format(round(Fees_Correct_vat, 2), ','))),

        if agreement_type == "HP":
            installment_total = Rentals_Correct
        else: installment_total=Rentals_Correct+Rentals_Correct_vat
        # else: installment_total=Rentals_Correct+Fees_Correct+Rentals_Correct_vat+Fees_Correct_vat

        array.append(str("£"+format(round(installment_total, 2), ','))),

    n = len(array)
    x = 0
    data3=[]

    # data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
    data3.append(['Date', 'Type', 'Net', 'VAT', 'Gross'])
    while x <= n-1:
        a=x
        b=a+1
        c=b+1
        d=c+1
        e=d+1
        f=e+1
        g=f+1
        # data3.append([array[a], array[b],array[c],array[d],array[e],array[f],array[g]])
        data3.append([array[a], array[b], array[c], array[d], array[e]])
        x=x+5

    t3 = Table(data3, colWidths=98, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                          ('BOX',(0,0),(-1,-1),1,colors.black),
                                                          ('GRID',(0,0),(-1,-1),0.5,colors.black),
                                                          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                                                          ])

    account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                                 transactiondate__gte = '2019-01-01',
                                                                                 transactiondate__lt = '2119-12-31'
                                                                                 ).aggregate(Sum('transnetpayment'))
    account_summary_rentals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactionsourceid__in=['SP1', 'GO1'],
                                                                          transactiondate__gte='2019-01-01',
                                                                          transactiondate__lt='2119-12-31'
                                                                          ).aggregate(Sum('transgrosspayment'))

    Total_Value = account_summary_rentals['transgrosspayment__sum']
    Net_Value = account_detail_rentals['transnetpayment__sum']

    if agreement_type == "HP":
        # Net_Value_vat=("£0.00")
        d2 = str("£0.00")
    else:
        Net_Value_vat = Total_Value - Net_Value
        d2 = str("£" + format(round(Net_Value_vat, 2), ','))

    a2 = Paragraph("<b>Net:</b>",sample_style_sheet['BodyText'])
    b2 = str("£"+format(round(Net_Value, 2), ','))
    c2 = Paragraph("<b>VAT:</b>",sample_style_sheet['BodyText'])
    # d2 = str("£"+format(round(Net_Value_vat, 2), ','))
    e2 = Paragraph("<b>Total:</b>",sample_style_sheet['BodyText'])
    f2 = str("£"+format(round(Total_Value, 2), ','))

    data6 = [
             ['',a2,b2],
             ['',c2,d2],
             ['',e2, f2],
             ]
    t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                                                           ('BOX', (2, 0), (-1, -1), 1, colors.black),
                                                           ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
                                                           ])

    t6._argW[0] = 4.08 * inch
    t6._argW[1] = 1.36 * inch
    t6._argW[2] = 1.36 * inch

    paragraph_2 = Paragraph(
        "<b>Frequency:</b> Monthly"
        ,
        sample_style_sheet['BodyText']
    )

    data10 = [[ "This invoice has been issued for VAT purposes only and is not a demand for payment."],
              ["VAT can only be recovered by you after each payment has been made."],
              ["VAT Reg No.974594073"],
              ["You will receive these VAT schedules annually over the primary term of your agreement."]]

    paragraph_2.hAlign = 'CENTRE'

    # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [
             [array[0], ''],
             # ['', '', ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], ''],
             [array[6], ''],
    ]

    t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                             ])
    t2._argW[0] = 5.4 * inch
    t2._argW[1] = 1.4 * inch
    # t2._argW[2] = 1.4 * inch

    c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
    d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
    e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
    f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
    g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
    h3 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
    j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])

    data7 =  [[c3, d3,i3,j3, e3, f3,""],\
             [g3, h3,""],
              ]
    t7 = Table(data7, colWidths=100, rowHeights=15, style=[
                                                           ('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                           ('BOX', (0, 0), (0, -1), .5, colors.black),
                                                           ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
                                                           ])

    t7._argW[0] = 1.4 * inch
    t7._argW[1] = 0.9 * inch
    t7._argW[2] = 0.8 * inch
    t7._argW[3] = 0.5 * inch
    t7._argW[4] = 1.0 * inch
    t7._argW[5] = 0.8 * inch
    t7._argW[6] = 1.4 * inch

    data8 = [["","VAT SCHEDULE",""],]

    t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                             ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                                                             ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
                                                                  ])

    t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])

    paragraph_4 = Paragraph(
        " "
        ,
        sample_style_sheet['BodyText']
    )
    # im2 = Image("static/assets/images/others/bluerock-footer.PNG", width=6.8 * inch, height=1 * inch)
    im2 = Image("static/assets/images/others/bluerockfooter.PNG", width=6.8 * inch, height=1.3 * inch)

    flowables.append(im)
    flowables.append(t2)
    flowables.append(paragraph_4)
    flowables.append(t7)
    flowables.append(paragraph_4)
    flowables.append(t8)
    flowables.append(t3)
    flowables.append(t6)
    count_transactions= -(count_transactions-12)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    flowables.append(t10)
    if count_transactions != 0:
        for n in range(count_transactions):
            flowables.append(paragraph_4)
    flowables.append(im2)
    my_doc.build(flowables)

    pdf_VAT_STATEMENT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " VAT Statement"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_VAT_STATEMENT_value)
    return response

def print_pdf_STATEMENT_OF_ACCOUNT(request, agreement_id):
    # NOT CURRENTLY USED IN APPLICATION @ 2019-10-23
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)

    flowables = []

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transgrosspayment'))
    settlement_figure_vat = settlement_figure_queryset['transgrosspayment__sum']

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure_net = settlement_figure_queryset['transnetpayment__sum']
    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'GO1'],
                                                                            transtypeid__isnull=True,
                                                                            transactiondate__gte=first_rental_date) \
            .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    settlement_figure_queryset = account_summary.aggregate(Sum('transgrosspayment'))
    settlement_figure_vat = settlement_figure_queryset['transgrosspayment__sum']

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure_net = settlement_figure_queryset['transnetpayment__sum']

    first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")

    today_date = datetime.date.today()
    new_today_date = today_date.strftime("%m%y")

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()

    paragraph_0 = Paragraph(
        "<b>Customer Number: </b>" + agreement_customer.customernumber
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_1 = Paragraph(
        "<b>Broker ID:</b> NCF002 "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_2 = Paragraph(
        "<b>Agreement Number: </b>" + agreement_id
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_3 = Paragraph(
        "<b>Broker:</b> Nationwide Corporate Finance"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_4 = Paragraph(
        "<b>Agreement Date: </b>" + str(first_rental_date, )
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(
        "<b>Inital Ref: </b>" + agreement_id[4:] + "-APE-" + new_today_date
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(
        "<b>Term:</b> " + str(primary_count)
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_22 = Paragraph(

        "<u>Statement of Account</u>",

        sample_style_sheet['Heading1']
    )
    paragraph_40 = Paragraph(

        "The term will always include any primary or secondary payments due in accordance with terms & conditions of the agreement.",

        sample_style_sheet['BodyText']
    )
    paragraph_41 = Paragraph(

        "VAT Reg No. 974 5940 73 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No: 729205 | Company Reg No. 06944649.",

        sample_style_sheet['BodyText']
    )

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t2 = Table(data2, colWidths=225, rowHeights=15)

    flowables.append(t2)
    flowables.append(paragraph_22)
    flowables.append(paragraph_0)
    flowables.append(paragraph_1)
    flowables.append(paragraph_2)
    flowables.append(paragraph_3)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)
    flowables.append(paragraph_6)

    data = [['Payment Date', 'Payment Description', 'Payment Amount', '', 'Payment Status', 'Payment Number'],
            ]
    t = Table(data, colWidths=70, rowHeights=20)

    t._argW[1] = 1.7 * inch
    t._argW[2] = 0.7 * inch
    t._argW[3] = 0.7 * inch
    t._argW[4] = 1.7 * inch
    t._argW[5] = 0.7 * inch
    flowables.append(t)

    flowables.append(paragraph_40)
    flowables.append(paragraph_41)

    my_doc.build(flowables)

    pdf_STATEMENT_OF_ACCOUNT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " Statement of Account"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_STATEMENT_OF_ACCOUNT_value)
    return response

def print_pdf_EARLY_SETTLEMENT(request, agreement_id):
    # NOT CURRENTLY USED IN APPLICATION @ 2019-10-23
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer,
                               rightMargin=50,
                               leftMargin=50,
                               topMargin=20,
                               bottomMargin=50
                               )
    flowables = []

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_queryset_gross = account_summary.aggregate(Sum('transgrosspayment'))
    settlement_figure_gross = settlement_figure_queryset_gross['transgrosspayment__sum']
    if agreement_type == 'Lease':
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    else:
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    next_rental_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'SP2',
                                                                                                     'SP3', 'GO1', 'GO3'],
                                                                            transtypeid__isnull=False,
                                                                            transactiondate__gt=datetime.date.today()).first()
    next = next_rental_date.transactiondate.strftime("%d/%m/%Y")

    paragraph_33 = Paragraph(

        "<u> Early Termination Figure </u>",

        sample_style_sheet['Heading1']
    )

    a = Paragraph('''<u>Hire Agreement Number:</u>''', sample_style_sheet['BodyText'])
    b = Paragraph('''<u>Hire Agreement Name:</u>''', sample_style_sheet['BodyText'])
    c = Paragraph('''<u>Goods:</u>''', sample_style_sheet['BodyText'])
    d = Paragraph('''Terminal Settlement Figure:''', sample_style_sheet['Heading4'])
    e = Paragraph("£" + str(format(round(settlement_figure_gross, 2), ',')), sample_style_sheet['Heading4'])
    table3 = [a, agreement_id], \
             [b, agreement_customer.customercompany], \
             [c, "As per schedule NCF01"], \
             [d, e]

    paragraph_4 = Paragraph(
        "In response to your request for a termination figure for agreement " + agreement_id + " we have pleasure in providing the following information. For security purposes the termination details are provided by email and post.If you have not requested this, please contact us immediately."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(

        "Your Account details are protected by the Data Protection Act (DPA), so we can only discuss your account with you. We will not discuss details of your account with any other person unless you first give us your express permission to do so. This is to ensure the details about your business remain secure at all times. "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(
        "These types of agreements have huge tax benefits to your business and are not interest only contracts, we are not allowed or permitted to discount over a certain level, however there are no penalties for early termination. This figure has been calculated after taking into account the transactions up to and including todays date and is valid until the date shown below. We are assuming that your bank will not recall any direct debit, standing order and any cheques already received by us will be honoured. The Termination Sum which you will have to pay upon early termination of this Agreement will be based upon the remaining total gross rentals shown on the agreement in the Rental payments section as also shown in clause 9 (b). This termination sum represents damages and not a supply of services therefore you will not receive a separate vat invoice as per clause 9 (d). The total payable below is only valid until the date shown below subject to the agreement being upto date. "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_7 = Paragraph(
        "<b>Important - Your Personal Information</b> - We may use your personal information for a variety of purposes and further details of the use of information by us can be found about this and your other rights if you see our Fair Processing Notice at: www.bluerockfinance.co.uk / fair - processing - notice /. We consider that such processing is necessary for our legitimate interests in considering applications and in operating Agreements and our business, and it is a requirement of entering into an Agreement. You have a right to object to our processing your information on grounds relating to your particular situation."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_8 = Paragraph(
        "If you decide to terminate the agreement early and applying the maximum discount possible, including the notice period, please see below:       "
        ,
        sample_style_sheet['BodyText']
    )

    f = Paragraph("Total Payable for Settlement:", sample_style_sheet['Heading4'])
    h = Paragraph("Valid Until:", sample_style_sheet['Heading4'])
    i = Paragraph(next, sample_style_sheet['Heading4'])

    table5 = [f, e, h, i],

    j = Paragraph("Bank Name:", sample_style_sheet['BodyText'])
    k = Paragraph("Coutts & Co", sample_style_sheet['BodyText'])
    l = Paragraph("Account No & Sort Code:", sample_style_sheet['BodyText'])
    m = Paragraph("0576 9981   18 - 00 - 02", sample_style_sheet['BodyText'])

    n = Paragraph("Account Name:", sample_style_sheet['BodyText'])
    o = Paragraph("Bluerock Secured Finance", sample_style_sheet['BodyText'])
    p = Paragraph("Reference:", sample_style_sheet['BodyText'])
    q = Paragraph(agreement_id, sample_style_sheet['BodyText'])

    table4 = [j, k, l, m], \
             [n, o, p, q]

    paragraph_11 = Paragraph(
        "We offer a new business discount for further finance taken out prior to the valid until date shown above. If you would like to discuss the end of hire options & requirements, then please contact your broker."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_12 = Paragraph(
        "We would like to take this opportunity to thank you for using Bluerock Secured Finance Ltd and wish you "
        "and your business every success in the future."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_125 = Paragraph(
        "",
        sample_style_sheet['BodyText']
    )

    paragraph_13 = Paragraph(
        " Yours faithfully,"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_14 = Paragraph(
        "Alan Richards"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_15 = Paragraph(
        " Customer Services"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_16 = Paragraph(

        " VAT Reg No. 974 594073 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No: 729205 | Company Reg No. 06944649."
        ,

        sample_style_sheet['Heading6']
    )

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t2 = Table(data2, colWidths=247, rowHeights=15)
    t3 = Table(table3, colWidths=247, rowHeights=15, style=[])
    t5 = Table(table5, colWidths=99, rowHeights=18, style=[])
    t4 = Table(table4, colWidths=120, rowHeights=15, style=[])

    t4._argW[0] = 1.2 * inch
    t4._argW[1] = 2 * inch
    t4._argW[2] = 1.9 * inch
    t4._argW[3] = 1.8 * inch

    t5._argW[0] = 2.4 * inch
    t5._argW[1] = 1.5 * inch
    t5._argW[2] = 1.5 * inch
    t5._argW[3] = 1.5 * inch

    flowables.append(t2)
    flowables.append(paragraph_33)
    flowables.append(t3)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)
    flowables.append(paragraph_6)
    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(t5)
    flowables.append(t4)
    flowables.append(paragraph_11)
    flowables.append(paragraph_12)
    flowables.append(paragraph_13)
    flowables.append(paragraph_125)
    flowables.append(paragraph_125)
    flowables.append(paragraph_125)
    flowables.append(paragraph_14)
    flowables.append(paragraph_15)
    flowables.append(paragraph_16)

    my_doc.build(flowables)

    pdf_EARLY_SETTLEMENT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " Early Settlement Figure"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_EARLY_SETTLEMENT_value)
    return response

def print_pdf_TEMPLATE_TERMINATION(request, agreement_id):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    sample_style_sheet = getSampleStyleSheet()

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False) \
        .order_by('transtypedesc', )
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_vat = settlement_figure_queryset['transgrosspayment__sum']
    # if agreement_type == 'Lease':
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    # else:
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    styles = getSampleStyleSheet()
    Elements = []

    words = "lorem ipsum dolor sit amet consetetur sadipscing elitr sed diam nonumy eirmod tempor invidunt ut labore et".split()
    doc = BaseDocTemplate('basedoc.pdf', showBoundary=1)

    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + doc.width / 2 + 6, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col2')

    Elements.append(Paragraph(" ".join([random.choice(words) for i in range(1000)]), styles['Normal']))
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2]), ])

    try:
        future_rentals_count = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                     transactiondate__gt=datetime.date.today()).count()
    except:
        future_rentals_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    Notice_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).aggregate(Sum('transnetpayment'))
    Notice_Rentals = Notice_Rentals_queryset['transnetpayment__sum']


    Notice_Rentals_queryset_gross = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).aggregate(Sum('transgrosspayment'))
    Notice_Rentals_gross = Notice_Rentals_queryset_gross['transgrosspayment__sum']

    if Notice_Rentals:
        if agreement_type == 'Lease':
            Notice_Rentals_vat = Notice_Rentals_gross
        else:
            Notice_Rentals_vat = Notice_Rentals
    else:
        Notice_Rentals = 0
        Notice_Rentals_vat = 0


    #
    # if agreement_type == 'Lease':
    #     Notice_Rentals_vat = Notice_Rentals_gross
    # else:
    #     Notice_Rentals_vat = Notice_Rentals

    next_rental_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'SP2',
                                                                                                     'SP3', 'GO1', 'GO3'],
                                                                            transtypeid__isnull=False,
                                                                            transactiondate__gt=datetime.date.today()).first()

    Future_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                     transactiondate__gt=datetime.date.today()).aggregate(Sum('transnetpayment'))
    Future_Rentals = Future_Rentals_queryset['transnetpayment__sum']

    Future_Rentals_queryset_gross = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                           transactiondate__gt=datetime.date.today()).aggregate(Sum('transgrosspayment'))
    Future_Rentals_gross = Future_Rentals_queryset_gross['transgrosspayment__sum']

    if agreement_type == 'Lease':
        Future_Rentals_vat = Future_Rentals_gross
    else:
       Future_Rentals_vat = Future_Rentals

    today = datetime.date.today()
    sample_style_sheet.list()

    account_summary_01 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id
                                                                              , transactionsourceid__in=['SP1', 'SP2',
                                                                                                 'SP3', 'GO1', 'GO3'])
    expected_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                      transactiondate__lte=datetime.date.today(),
                      transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3']).aggregate(Sum('transnetpayment'),
                                                                                             Sum('transgrosspayment'))

    receipts_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactiondate__lte=datetime.date.today()).\
        exclude(transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3']).aggregate(Sum('transnetpayment'),
                                                                                       Sum('transgrosspayment'))

    if receipts_total["transnetpayment__sum"] is None:
        Arrears_Arrears = expected_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"]
    else:
        Arrears_Arrears = expected_total["transnetpayment__sum"]+receipts_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"]+receipts_total["transgrosspayment__sum"]

    # if agreement_type == 'Lease':
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)
    # else:
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    try:
        secondary_count = account_summary_01.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    if receipts_total["transnetpayment__sum"] is None:
        wip_receipts_total=0
    else:
        wip_receipts_total = -receipts_total["transnetpayment__sum"]


    Arrears_Term=0
    n = 0
    for transaction in account_summary_01:

        val_payment_status = ''
        if wip_receipts_total > 0:
            wip_receipts_total = wip_receipts_total - transaction.transnetpayment
            if wip_receipts_total >= 0:
                received_value = transaction.transnetpayment
                val_payment_status = 'Received'
            else:
                received_value = transaction.transnetpayment + wip_receipts_total
                val_payment_status = 'Part Paid'
                n = n + 1
            #    Arrears_Term = Arrears_Term + wip_receipts_total
        else:
            received_value = 0
            if str(transaction.transactiondate) >= str(today):
                val_payment_status = 'Not Yet Due'
            else:
                if str(transaction.transactiondate) < str(today):
                    val_payment_status = 'Not Received'
                    n = n + 1
                    Arrears_Term=Arrears_Term + transaction.transnetpayment
                else:
                    val_payment_status = 'Expected'

    Arrear_Fees = decimal.Decimal(1280.00 + (n*360.00))

    Termination_Figure = Future_Rentals_vat + Notice_Rentals_vat + Arrear_Fees + Arrears_Arrears_vat

    a1 = Paragraph("<u>Hire Agreement Number: </u>", sample_style_sheet['BodyText'])
    b1 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    c1 = Paragraph("<u>Hire Agreement Name: </u>", sample_style_sheet['BodyText'])
    d1 = Paragraph(agreement_customer.customercompany, sample_style_sheet['BodyText'])
    e1 = Paragraph("<u>Date of Notice: </u>", sample_style_sheet['BodyText'])
    f1 = Paragraph(str(today.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
    g1 = Paragraph("Goods: As per schedule NCF01", sample_style_sheet['BodyText'])
    h1 = Paragraph("Termination Figure:", sample_style_sheet['Heading4'])
    i1 = Paragraph("£"+str(format(round(Termination_Figure, 2), ',')), sample_style_sheet['Heading4'])


    data5 = [a1, b1, g1], \
            [c1, d1, ""], \
            [e1, f1, ""], \
            [h1, i1, ""]

    paragraph_33 = Paragraph(

        "<u> Notice of Termination </u>",

        sample_style_sheet['Heading1']
    )
    paragraph_33.hAlign = 'CENTRE'

    paragraph_4 = Paragraph(
        "Dear Sirs,"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(
        "The agreement number " + agreement_id + " "+ " has been terminated and there is a liability pursuant to the terms of your Guarantee and Indemnity. We now demand repayment of the termination balance as below." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(

        "<u>TAKE NOTICE</u>" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_7 = Paragraph(
        "That in accordance with the rights vested in the Lessor under the terms of the above agreement, we give formal notice " \
        "that the agreement has now been terminated by reason of a breach of our terms and / or default or insolvency. The Termination " \
        "Sum which you will have to pay upon early termination or early settlement of this Agreement will be based upon the " \
        "remaining total gross rentals shown on the agreement in the Rental payments section as also shown in clause 9(b). This " \
        "termination sum represents damages and not a supply of services therefore you will not receive a vat invoice as per " \
        "the agreement terms clause 9(d). "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_8 = Paragraph(
        "If we do not receive the below Termination Sum of within the next three days, legal " \
        "proceedings will be brought against you and the Guarantors to the Agreement without further notice or delay. " \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_9 = Paragraph(
        "Please note that you are now in possession of our goods without our consent (which will invalidate insurance). You " \
        "must NOT use our goods. "
       ,
        sample_style_sheet['BodyText']
    )
    paragraph_10 = Paragraph(

        "We have instructed our Repossession Agents Brightwell Recovery’s to attend your business address " \
        "with repossession officers to recover our goods. " \
        ,
        sample_style_sheet['BodyText']
    )
    z = Paragraph('''Arrears at Termination''', sample_style_sheet['BodyText'])
    y = str(format(round(Arrears_Arrears_vat, 2), ','))
    x = Paragraph('''Arrears Fees & Legal Fees''', sample_style_sheet['BodyText'])
    w = str(format(round(Arrear_Fees, 2), ','))
    v = Paragraph(str(future_rentals_count) +""+" x Total Gross Future Rentals", sample_style_sheet['BodyText'])
    u = str(format(round(Future_Rentals_vat, 2), ','))
    t = Paragraph(str(secondary_count) +""+ " x Notice Period Rentals", sample_style_sheet['BodyText'])
    s = str(format(round(Notice_Rentals_vat, 2), ','))
    r = Paragraph('''Total Immediately Due''', sample_style_sheet['Heading4'])
    q = str(format(round(Termination_Figure, 2), ','))

    data4 =  ["","","",""],\
             [z,"£", y,""], \
             [x,"£", w,""], \
             [v,"£", u,""], \
             [t,"£", s,""],\
             ["","","",""],\
             [r,"£", q,""]

    j = Paragraph("Bank Name:", sample_style_sheet['BodyText'])
    k = Paragraph("Coutts & Co", sample_style_sheet['BodyText'])
    l = Paragraph("Account No & Sort Code:", sample_style_sheet['BodyText'])
    m = Paragraph("0576 9981   18-00-02", sample_style_sheet['BodyText'])

    n = Paragraph("Account Name:", sample_style_sheet['BodyText'])
    o = Paragraph("Bluerock Secured Finance", sample_style_sheet['BodyText'])
    p = Paragraph("Reference:", sample_style_sheet['BodyText'])
    q = Paragraph(agreement_id, sample_style_sheet['BodyText'])

    table123 = [j, k, l, m], \
             [n, o, p, q]

    t123 = Table(table123, colWidths=118, rowHeights=15, style=[])
    t123._argW[0] = 1.12 * inch
    t123._argW[1] = 1.95 * inch
    t123._argW[2] = 1.72 * inch
    t123._argW[3] = 1.46 * inch

    paragraph_13 = Paragraph(
        "This notice is a final demand for your immediate payment of the sum shown above." \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_165 = Paragraph(
        "Yours faithfully, " \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_17 = Paragraph(
        "Alan Richards" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_18 = Paragraph(
        "Head of Collections" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_19 = Paragraph(
        "VAT Reg No. 974 5940 73 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No: 729205 | Company Reg No.06944649.",
        sample_style_sheet['Heading6']
    )

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t5 = Table(data5, colWidths=154, rowHeights=20)
    t5._argW[0] = 1.9 * inch
    t5._argW[1] = 2.2 * inch
    t5._argW[2] = 2.2 * inch
    t2 = Table(data2, colWidths=225, rowHeights=15)

    table40 = Table(data4, colWidths=200, rowHeights=15, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                                ('FONTNAME', (2, 5), (-1, -1), 'Helvetica-Bold')
                                                                ])
    table40._argW[0] = 2.2 * inch
    table40._argW[1] = 0.5 * inch
    table40._argW[2] = 1 * inch
    table40._argW[3] = 2.6 * inch

    flowables.append(t2)
    flowables.append(paragraph_33)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)
    flowables.append(t5)
    flowables.append(paragraph_6)
    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(paragraph_9)
    flowables.append(paragraph_10)
    flowables.append(table40)
    flowables.append(paragraph_13)
    flowables.append(t123)
    flowables.append(paragraph_165)
    flowables.append(paragraph_17)
    flowables.append(paragraph_18)
    flowables.append(paragraph_19)

    doc.build(Elements)
    my_doc.build(flowables)

    pdf_TEMPLATE_TERMINATION_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " Template Termination"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_TEMPLATE_TERMINATION_value)
    return response

def print_pdf_ARREARS_LETTER(request, agreement_id):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    sample_style_sheet = getSampleStyleSheet()

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False) \
        .order_by('transtypedesc', )
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_vat = settlement_figure_queryset['transgrosspayment__sum']
    # if agreement_type == 'Lease':
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    # else:
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    styles = getSampleStyleSheet()
    Elements = []

    words = "lorem ipsum dolor sit amet consetetur sadipscing elitr sed diam nonumy eirmod tempor invidunt ut labore et".split()
    doc = BaseDocTemplate('basedoc.pdf', showBoundary=1)

    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + doc.width / 2 + 6, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col2')

    Elements.append(Paragraph(" ".join([random.choice(words) for i in range(1000)]), styles['Normal']))
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2]), ])

    try:
        future_rentals_count = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                     transactiondate__gt=datetime.date.today()).count()
    except:
        future_rentals_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    Notice_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3'])\
                                                .aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
    Notice_Rentals = Notice_Rentals_queryset['transnetpayment__sum']
    Notice_Rentals_vat = Notice_Rentals_queryset['transgrosspayment__sum']

    if Notice_Rentals:
        pass
        # if agreement_type == 'Lease':
        #     Notice_Rentals_vat = Notice_Rentals * decimal.Decimal(sales_tax_rate)
        # else:
        #     Notice_Rentals_vat = Notice_Rentals * decimal.Decimal(sales_tax_rate)
    else:
        Notice_Rentals = 0
        Notice_Rentals_vat = 0

    next_rental_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'SP2',
                                                                                                     'SP3', 'GO1', 'GO3'],
                                                                            transtypeid__isnull=False,
                                                                            transactiondate__gt=datetime.date.today()).first()

    Future_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP1', 'GO3'],
                                                     transactiondate__gt=datetime.date.today())\
                                                        .aggregate(Sum('transnetpayment'), Sum('transgrosspayment') )
    Future_Rentals = Future_Rentals_queryset['transnetpayment__sum']
    Future_Rentals_vat = Future_Rentals_queryset['transgrosspayment__sum']

    if Future_Rentals:
        pass
        # if agreement_type == 'Lease':
        #     Future_Rentals_vat = Future_Rentals * decimal.Decimal(sales_tax_rate)
        # else:
        #     Future_Rentals_vat = Future_Rentals * decimal.Decimal(sales_tax_rate)
    else:
        Future_Rentals = 0
        Future_Rentals_vat = 0

    today = datetime.date.today()
    sample_style_sheet.list()

    account_summary_01 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id
                                                                              , transactionsourceid__in=['SP1', 'SP2',
                                                                                                         'SP3', 'GO1', 'GO3'])
    expected_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                          transactiondate__lte=datetime.date.today(),
                                                          transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3'])\
                                                            .aggregate(Sum('transnetpayment'),
                                                                       Sum('transgrosspayment'))

    receipts_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactiondate__lte=datetime.date.today()). \
        exclude(transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3']).aggregate(Sum('transnetpayment'),
                                                                                       Sum('transgrosspayment'))

    if receipts_total["transnetpayment__sum"] is None:
        Arrears_Arrears = expected_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"]
    else:
        Arrears_Arrears = expected_total["transnetpayment__sum"]+receipts_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"]+receipts_total["transgrosspayment__sum"]

    # if agreement_type == 'Lease':
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)
    # else:
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    try:
        secondary_count = account_summary_01.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    if receipts_total["transnetpayment__sum"] is None:
        wip_receipts_total=0
    else:
        wip_receipts_total = -receipts_total["transnetpayment__sum"]


    Arrears_Term=0
    n = 0
    for transaction in account_summary_01:

        val_payment_status = ''
        if wip_receipts_total > 0:
            wip_receipts_total = wip_receipts_total - transaction.transnetpayment
            if wip_receipts_total >= 0:
                received_value = transaction.transnetpayment
                val_payment_status = 'Received'
            else:
                received_value = transaction.transnetpayment + wip_receipts_total
                val_payment_status = 'Part Paid'
                n = n + 1
            #    Arrears_Term = Arrears_Term + wip_receipts_total
        else:
            received_value = 0
            if str(transaction.transactiondate) >= str(today):
                val_payment_status = 'Not Yet Due'
            else:
                if str(transaction.transactiondate) < str(today):
                    val_payment_status = 'Not Received'
                    n = n + 1
                    Arrears_Term=Arrears_Term + transaction.transnetpayment
                else:
                    val_payment_status = 'Expected'

    Arrear_Fees = decimal.Decimal(1280.00 + (n*360.00))

    Termination_Figure = Future_Rentals_vat + Notice_Rentals_vat + Arrear_Fees + Arrears_Arrears_vat

   # = Paragraph(str(today.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])


    a1 = Paragraph("Agreement Number:", sample_style_sheet['BodyText'])
    b1 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    c1 = Paragraph("Amount overdue Inc fees:", sample_style_sheet['BodyText'])
    d1 = "£"+str(format(round(Arrears_Arrears_vat, 2), ','))
    e1 = Paragraph("Property known as:", sample_style_sheet['BodyText'])
    f1 = Paragraph(str("Property 1 Name To Add in Later"), sample_style_sheet['BodyText'])#TODO Property Name
    f2 = Paragraph(str("property 2 name"), sample_style_sheet['BodyText'])
    f3 = Paragraph(str("property 3 name"), sample_style_sheet['BodyText'])
    g1 = str("(the “Agreement”)")
    h1 = str("(the “Arrears”)", )
    i1 = str("(the “Property”)", )
    j1 = str(today.strftime("%d/%m/%Y"))
    k1 = str("Cc: Berman's Solicitors", )
    l1 = str("Cc: Brightwell Recovery", )
    m1 = str("Cc: Brightwell Auctioneers", )


    data5 = [["","",j1],
             [k1, "", ""],
             [l1, "", ""],
             [m1, "", ""],
             ["", "", ""],
             [a1, b1, g1],
             [c1, d1, h1],
             [e1, f1, i1]

   # if property 2:#TODO Multiple Property
  #          ,[e1,f2,i1]
  #  else ,["","",""]
  #  if property 3:
  #  ,[e1,f3,i1]
  #  else: end ,["","",""]
]

    paragraph_4 = Paragraph(
        "Dear Sirs,"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(
        "We refer to the Rental Arrears overdue on the Agreement." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(

        "You are in serious default as you have failed to pay the Rental Arrears. You have ignored previous reminders made by telephone." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_7 = Paragraph(
        "Our funding covenants provided to our securitised lenders require that we follow very strict bad debt procedures "
        "and enforce all rights and remedies available to us without delay or forbearance. We have no choice but to follow "
        "their procedures and legal protocol."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_8 = Paragraph(
        "In order to avoid the <b>Intended Action</b> described below we must therefore demand your immediate payment of the Rental Arrears in cleared funds." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_9 = Paragraph(
        "<b>Further Intended Action -</b>"
       ,
        sample_style_sheet['BodyText']
    )
    paragraph_10 = Paragraph(

        "We will terminate the Agreement and take any or all the following steps and at our entire discretion;"
        ,
        sample_style_sheet['BodyText']
    )
    z = Paragraph("Enforce the Debenture held over the assets of your company by "
                  "the appointment of an administrator; and/or", sample_style_sheet['BodyText'])
    y = str(format(round(Arrears_Arrears_vat, 2), ','))
    x = Paragraph("Notify your bankers that any consent to the operation of your Bank account "
                  "free from our debenture and which we may previously have given, is now withdrawn "
                  "which will result in your Bank account being frozen and/or", sample_style_sheet['BodyText'])
    w = Paragraph("Appoint a Receiver over the Property or issue Court proceedings to enforce our right to "
                  "possession and sale of the Property under the terms of the Charge provided by you and/or", sample_style_sheet['BodyText'])
    v = Paragraph("Your default is automatically flagged on both your personal and business credit file which "
                  "may prohibit you from obtaining credit of any type for a period of time and/or", sample_style_sheet['BodyText'])
    u = Paragraph("Instruct repossession agents to collect and sell the assets listed on the Agreement.", sample_style_sheet['BodyText'])

    data4 =  [["","1.",z],\
             ["","2.",x], \
             ["","3.",w], \
             ["","4.",v], \
             ["","5.",u]]


    t456 = Table(data4, colWidths=200, rowHeights=40, style=[('VALIGN', (0, 0), (-1, -1), 'TOP')
                                                             ])
    t456._argW[0] = -.50 * inch
    t456._argW[1] = 0.5 * inch
    t456._argW[2] = 5.25 * inch


    j = Paragraph("Bank Name:", sample_style_sheet['BodyText'])
    k = Paragraph("Coutts & Co", sample_style_sheet['BodyText'])
    l = Paragraph("Account No & Sort Code:", sample_style_sheet['BodyText'])
    m = Paragraph("0576 9981   18-00-02", sample_style_sheet['BodyText'])

    n = Paragraph("Amount:", sample_style_sheet['BodyText'])
    o = Paragraph("£"+y, sample_style_sheet['BodyText'])
    p = Paragraph("Reference:", sample_style_sheet['BodyText'])
    q = Paragraph(agreement_id, sample_style_sheet['BodyText'])

    table123 = [j, k, l, m], \
             [p, q, n, o]

    t123 = Table(table123, colWidths=118, rowHeights=15, style=[])
    t123._argW[0] = 1.12 * inch
    t123._argW[1] = 1.95 * inch
    t123._argW[2] = 1.72 * inch
    t123._argW[3] = 1.46 * inch

    paragraph_11 = Paragraph(

        "We can only accept the arrears payment on your Agreement for the next 24 hours, you can pay by credit or debit card by telephone. 01234 717398. "
        "After 24 hours your only option is to pay the full agreement debt which you will be pursued for."
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_14 = Paragraph(
        "Alternatively, you can pay by Bank transfer using the details below;" \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_15 = Paragraph(
        "You will not receive any further warning and the Intended Action will be commenced unless the Arrears have been paid in full within the next 24 hours." \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_16 = Paragraph(
        "Yours faithfully, " \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_17 = Paragraph(
        "Alan Richards" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_18 = Paragraph(
        "Head of Collections and Recoveries" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_19 = Paragraph(
        "alan.richards@bluerockfinance.co.uk",
        sample_style_sheet['BodyText']
    )
    paragraph_20 = Paragraph(
        "",
        sample_style_sheet['BodyText']
    )

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t5 = Table(data5, colWidths=175, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                           ])
    t5._argW[0] = 1.9 * inch
    t5._argW[1] = 3.0 * inch
    t5._argW[2] = 1.4 * inch
    t2 = Table(data2, colWidths=225, rowHeights=15)

   # table40 = Table(data4, colWidths=200, rowHeights=15, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                              #  ('FONTNAME', (2, 5), (-1, -1), 'Helvetica-Bold')
                                                               # ])
    #table40._argW[0] = 2.2 * inch
    #table40._argW[1] = 0.5 * inch
   # table40._argW[2] = 1 * inch
    #table40._argW[3] = 2.6 * inch

    flowables.append(t2)
    flowables.append(t5)
    #flowables.append(paragraph_33)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)

    flowables.append(paragraph_6)
    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(paragraph_9)
    flowables.append(paragraph_10)
    flowables.append(t456)
    flowables.append(paragraph_11)
    #flowables.append(table40)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_14)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(t123)
    flowables.append(paragraph_15)
    flowables.append(paragraph_16)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_17)
    flowables.append(paragraph_18)
    flowables.append(paragraph_19)

    doc.build(Elements)
    my_doc.build(flowables)

    pdf_ARREARS_LETTER_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " Arrears Letter"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_ARREARS_LETTER_value)
    return response

def print_pdf_ARREARS_RECEIVER_LETTER(request, agreement_id):
    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    flowables = []

    sample_style_sheet = getSampleStyleSheet()

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=False) \
        .order_by('transtypedesc', )
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_vat = settlement_figure_queryset['transgrosspayment__sum']
    # if agreement_type == 'Lease':
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    # else:
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    styles = getSampleStyleSheet()
    Elements = []

    words = "lorem ipsum dolor sit amet consetetur sadipscing elitr sed diam nonumy eirmod tempor invidunt ut labore et".split()
    doc = BaseDocTemplate('basedoc.pdf', showBoundary=1)

    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + doc.width / 2 + 6, doc.bottomMargin, doc.width / 2 - 6, doc.height, id='col2')

    Elements.append(Paragraph(" ".join([random.choice(words) for i in range(1000)]), styles['Normal']))
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2]), ])

    try:
        future_rentals_count = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                      transactiondate__gt=datetime.date.today()).count()
    except:
        future_rentals_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    Notice_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).aggregate(
        Sum('transnetpayment'), Sum('transgrosspayment'))
    Notice_Rentals = Notice_Rentals_queryset['transnetpayment__sum']
    Notice_Rentals_vat = Notice_Rentals_queryset['transgrosspayment__sum']

    if Notice_Rentals:
        pass
        # if agreement_type == 'Lease':
        #     Notice_Rentals_vat = Notice_Rentals * decimal.Decimal(sales_tax_rate)
        # else:
        #     Notice_Rentals_vat = Notice_Rentals * decimal.Decimal(sales_tax_rate)
    else:
        Notice_Rentals = 0
        Notice_Rentals_vat = 0

    next_rental_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'SP2',
                                                                                                     'SP3', 'GO1', 'GO3'],
                                                                            transtypeid__isnull=False,
                                                                            transactiondate__gt=datetime.date.today()).first()

    Future_Rentals_queryset = account_summary.filter(transactionsourceid__in=['SP1', 'GO1'],
                                                     transactiondate__gt=datetime.date.today()).aggregate(
        Sum('transnetpayment'), Sum('transgrosspayment'))

    Future_Rentals = Future_Rentals_queryset['transnetpayment__sum']
    Future_Rentals_vat = Future_Rentals_queryset['transgrosspayment__sum']

    # if agreement_type == 'Lease':
    #     Future_Rentals_vat = Future_Rentals * decimal.Decimal(sales_tax_rate)
    # else:
    #     Future_Rentals_vat = Future_Rentals * decimal.Decimal(sales_tax_rate)

    today = datetime.date.today()
    sample_style_sheet.list()

    account_summary_01 = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id
                                                                              , transactionsourceid__in=['SP1', 'SP2',
                                                                                                         'SP3', 'GO1', 'GO3'])
    expected_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactiondate__lte=datetime.date.today(),
                                                                          transactionsourceid__in=['SP1', 'SP2',
                                                                                                   'SP3', 'GO1', 'GO3']).aggregate(
        Sum('transnetpayment'), Sum('transgrosspayment'))

    receipts_total = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                          transactiondate__lte=datetime.date.today()). \
        exclude(transactionsourceid__in=['SP1', 'SP2', 'SP3', 'GO1', 'GO3'])\
        .aggregate(Sum('transnetpayment'),
                   Sum('transgrosspayment'))

    if receipts_total["transnetpayment__sum"] is None:
        Arrears_Arrears = expected_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"]
    else:
        Arrears_Arrears = expected_total["transnetpayment__sum"] + receipts_total["transnetpayment__sum"]
        Arrears_Arrears_vat = expected_total["transgrosspayment__sum"] + receipts_total["transgrosspayment__sum"]

    # if agreement_type == 'Lease':
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)
    # else:
    #     Arrears_Arrears_vat = Arrears_Arrears * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    try:
        secondary_count = account_summary_01.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    if agreement_detail.agreementdefname != 'Hire Purchase':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    if receipts_total["transnetpayment__sum"] is None:
        wip_receipts_total = 0
    else:
        wip_receipts_total = -receipts_total["transnetpayment__sum"]

    Arrears_Term = 0
    n = 0
    for transaction in account_summary_01:

        val_payment_status = ''
        if wip_receipts_total > 0:
            wip_receipts_total = wip_receipts_total - transaction.transnetpayment
            if wip_receipts_total >= 0:
                received_value = transaction.transnetpayment
                val_payment_status = 'Received'
            else:
                received_value = transaction.transnetpayment + wip_receipts_total
                val_payment_status = 'Part Paid'
                n = n + 1
            #    Arrears_Term = Arrears_Term + wip_receipts_total
        else:
            received_value = 0
            if str(transaction.transactiondate) >= str(today):
                val_payment_status = 'Not Yet Due'
            else:
                if str(transaction.transactiondate) < str(today):
                    val_payment_status = 'Not Received'
                    n = n + 1
                    Arrears_Term = Arrears_Term + transaction.transnetpayment
                else:
                    val_payment_status = 'Expected'

    Arrear_Fees = decimal.Decimal(1280.00 + (n * 360.00))

    Termination_Figure = Future_Rentals_vat + Notice_Rentals_vat + Arrear_Fees + Arrears_Arrears_vat

    # = Paragraph(str(today.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])

    a1 = Paragraph("Agreement Number:", sample_style_sheet['BodyText'])
    b1 = Paragraph(agreement_id, sample_style_sheet['BodyText'])
    c1 = Paragraph("Debt Inc fees:", sample_style_sheet['BodyText'])
    d1 = "£" + str(format(round(Arrears_Arrears_vat, 2), ','))
    e1 = Paragraph("Security:", sample_style_sheet['BodyText'])
    f1 = Paragraph(str("Property 1 Name To Add in Later"), sample_style_sheet['BodyText']) #TODO Property Name
    f2 = Paragraph(str("property 2 name"), sample_style_sheet['BodyText'])
    f3 = Paragraph(str("property 3 name"), sample_style_sheet['BodyText'])
    g1 = str("(the “Agreement”)")
    h1 = str("(the “Arrears”)", )
    i1 = str("(the “Charged Property”)", )
    j1 = str(today.strftime("%d/%m/%Y"))
    k1 = str("Cc: Berman's Solicitors", )
    l1 = str("Cc: Brightwell Repossessions & Property Auctioneers", )
    m1 = Paragraph("Agreement Name:", sample_style_sheet['BodyText'])
    n1 = Paragraph(agreement_customer.customercompany, sample_style_sheet['BodyText'])
    o1 = str("(the “Hirer”)")
    p1 = Paragraph("Guarantor:", sample_style_sheet['BodyText'])
    q1 = Paragraph(str("Guarantor Name To Add in Later"), sample_style_sheet['BodyText']) #TODO Guarantor Addition
    r1 = str("(the “Personal Guarantor”)")

    data5 = [["", "", j1],
             [k1, "", ""],
             [l1, "", ""],
             ["", "", ""],
             [m1, n1, o1],
             [a1, b1, g1],
             [c1, d1, h1],
             [p1, q1, r1],
             [e1, f1, i1]

             # if property 2: #TODO Multiple Property
             #          ,[e1,f2,i1]
             #  else ,["","",""]
             #  if property 3:
             #  ,[e1,f3,i1]
             #  else: end ,["","",""]
             ]

    paragraph_4 = Paragraph(
        "Dear Sirs,"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(
        "We formally write to you with regard to the Agreement made between "
        "Bluerock Secured Finance Ltd (BSF) and " + agreement_customer.customercompany \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(

        "The Agreement has been terminated and you will have received a copy the termination notice. "
        "Under the terms of the Agreement " + agreement_customer.customercompany + " is now indebted to BSF in a total "
        "sum of £" + str(format(round(Arrears_Arrears_vat, 2), ',')) + " as specified above and in the termination notice." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_7 = Paragraph(
        "In consideration for BSF entering into the Agreement you provided BSF with your personal "
        "guarantee and indemnity supported by a Legal Charge over your property at:" + " Property 1 Name To Add in Later " + " (the “Charged Property”)"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_8 = Paragraph(
        "You are also liable for BSF’s legal costs on an indemnity basis pursuant to the terms of your "
        "guarantee and indemnity and which continue to accrue until the full amount due is settled." \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_9 = Paragraph(
        "Unless we now receive your remittance for the said sum of £"+ str(format(round(Arrears_Arrears_vat, 2), ',')) +  " and by no later than 4pm "
        " on "+ str((today+ + timedelta(days=5) ).strftime("%d/%m/%Y")) + ", "
        "we have given advanced instruction to appoint a Receiver to enforce all of our rights under the Legal "
        "Charge against the Charged Property including the right to seek possession and sale of that property and without further notice."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_10 = Paragraph(

        "If you have tenants in the property or any other person over the age of 18, you should put them on notice "
        "now of the pending possession and intended sale of the property, as they are immediately required to find an alternative place to reside."
        ,
        sample_style_sheet['BodyText']
    )
    z = Paragraph("Enforce the Debenture held over the assets of your company by "
                  "the appointment of an administrator; and/or", sample_style_sheet['BodyText'])
    y = str(format(round(Arrears_Arrears_vat, 2), ','))
    x = Paragraph("Notify your bankers that any consent to the operation of your Bank account "
                  "free from our debenture and which we may previously have given, is now withdrawn "
                  "which will result in your Bank account being frozen and/or", sample_style_sheet['BodyText'])
    w = Paragraph("Appoint a Receiver over the Property or issue Court proceedings to enforce our right to "
                  "possession and sale of the Property under the terms of the Charge provided by you and/or",
                  sample_style_sheet['BodyText'])
    v = Paragraph("Your default is automatically flagged on both your personal and business credit file which "
                  "may prohibit you from obtaining credit of any type for a period of time and/or",
                  sample_style_sheet['BodyText'])
    u = Paragraph("Instruct repossession agents to collect and sell the assets listed on the Agreement.",
                  sample_style_sheet['BodyText'])

    data4 = [["", "1.", z], \
             ["", "2.", x], \
             ["", "3.", w], \
             ["", "4.", v], \
             ["", "5.", u]]

    t456 = Table(data4, colWidths=200, rowHeights=40, style=[('VALIGN', (0, 0), (-1, -1), 'TOP')
                                                             ])
    t456._argW[0] = -.50 * inch
    t456._argW[1] = 0.5 * inch
    t456._argW[2] = 5.25 * inch

    j = Paragraph("Bank Name:", sample_style_sheet['BodyText'])
    k = Paragraph("Coutts & Co", sample_style_sheet['BodyText'])
    l = Paragraph("Account No & Sort Code:", sample_style_sheet['BodyText'])
    m = Paragraph("0576 9981   18-00-02", sample_style_sheet['BodyText'])

    n = Paragraph("Amount:", sample_style_sheet['BodyText'])
    o = Paragraph("£" + y, sample_style_sheet['BodyText'])
    p = Paragraph("Reference:", sample_style_sheet['BodyText'])
    q = Paragraph(agreement_id, sample_style_sheet['BodyText'])

    table123 = [j, k, l, m], \
               [p, q, n, o]

    t123 = Table(table123, colWidths=118, rowHeights=15, style=[])
    t123._argW[0] = 1.12 * inch
    t123._argW[1] = 1.95 * inch
    t123._argW[2] = 1.72 * inch
    t123._argW[3] = 1.46 * inch

    paragraph_11 = Paragraph(

        "Attached are updated Land Registry searches of your property, showing BSF's Legal Charge clearly noted against your title number."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_13 = Paragraph(
        "You will not receive any further warning and the Intended Action will be commenced unless the debt has been paid in full before the above deadline." \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_14 = Paragraph(
        "You can pay by Bank transfer using the details below;" \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_15 = Paragraph(
        "<b>Receivers have the power to legally take possession of property and will attend "
        "the above property without notice once the above deadline passes.</b>" \
        ,
        sample_style_sheet['BodyText']
    )

    paragraph_16 = Paragraph(
        "Yours faithfully, " \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_17 = Paragraph(
        "Alan Richards" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_18 = Paragraph(
        "Head of Property Repossessions and Bankruptcy" \
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_19 = Paragraph(
        "alan.richards@bluerockfinance.co.uk",
        sample_style_sheet['BodyText']
    )
    paragraph_20 = Paragraph(
        "",
        sample_style_sheet['BodyText']
    )

    paragraph_41 = Paragraph(

        "VAT Reg No. 974 5940 73 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No: 729205 | Company Reg No. 06944649.",

        sample_style_sheet['BodyText']
    )


    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t5 = Table(data5, colWidths=175, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                           ])
    t5._argW[0] = 1.9 * inch
    t5._argW[1] = 3.0 * inch
    t5._argW[2] = 1.4 * inch
    t2 = Table(data2, colWidths=225, rowHeights=15)

    flowables.append(t2)
    flowables.append(t5)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)
    flowables.append(paragraph_6)
    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(paragraph_9)
    flowables.append(paragraph_10)
   # flowables.append(t456)
    flowables.append(paragraph_11)
   # flowables.append(paragraph_20)
   # flowables.append(paragraph_20)
   # flowables.append(paragraph_20)

    flowables.append(paragraph_14)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(t123)
    flowables.append(paragraph_13)
    flowables.append(paragraph_15)
    flowables.append(paragraph_16)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_20)
    flowables.append(paragraph_17)
    flowables.append(paragraph_18)
    flowables.append(paragraph_19)
    flowables.append(paragraph_41)

    doc.build(Elements)
    my_doc.build(flowables)

    pdf_ARREARS_RECEIVER_LETTER_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'GO ' + agreement_id + " Arrears Receiver Letter"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_ARREARS_RECEIVER_LETTER_value)
    return response