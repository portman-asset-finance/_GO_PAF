
from dateutil.relativedelta import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
import io
import pytz
import uuid
# TODO: PAF Changes - Start
import json, requests
import math
# TODO: PAF Changes - End
import numpy
import decimal
import datetime
import traceback
from numpy import pmt

wip_utc = pytz.UTC

from django.db.models import Sum, Q

from decimal import Decimal

from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# TODO: PAF Changes - Start
from .models import go_customers, go_agreement_querydetail, go_agreements, go_broker, go_account_transaction_detail, go_account_transaction_summary, \
    go_agreement_definitions, go_profile_types, go_agreement_index, go_sales_authority, transition_log, go_funder, go_selectable_functionality , go_collection_schedule, go_payment_method
# TODO: PAF Changes - End
from core_agreement_editor.models import go_editor_history

from core.models import ncf_applicationwide_text, \
                        go_extensions, \
                        ncf_dd_schedule, \
                        ncf_datacash_drawdowns, \
                        ncf_dd_audit_log, \
                        ncf_regulated_agreements

from core_direct_debits.models import DDHistory

from .functions import validate_agreement_number, validate_tab1, generate_customer_number, validate_date, get_holidays, get_next_due_date, consolidation_function, archive_agreement_function, unarchive_agreement_function, refund_function

from core_direct_debits.functions import generate_dd_reference, update_ddi_status, cancel_ddi_with_datacash

from .filters import agreement_querydetail_Filter, \
                     accounttransactionsummary_Filter, \
                     ncf_arrears_summary_Filter, ncf_ddic_advices_Filter, customers_Filter, go_editor_history_Filter

from core_direct_debits.functions import generate_dd_reference, create_ddi_with_datacash, create_ddi_with_eazycollect

from core.functions_go_id_selector import requiredtabs, client_configuration, riskfeenetamount, daysbeforecalldd, daysbeforeddsetup,  pmt_commission, pmt_yield
# TODO: PAF Changes - Start
from core_agreement_crud.functions import recalculate_function, reopen_function, functionality_function
# TODO: PAF Changes - End
from core_dd_drawdowns.models import DrawDown, StatusDefinition

from core_arrears.models import arrears_summary_agreement_level
from core_arrears.functions_shared import app_process_non_dd_arrears

import datetime
from datetime import timedelta


@login_required(login_url='signin')
def auto_complete(request):
    """
    Searches the customer table with values that contains a given search string.
    :return:
    """

    search_value = request.GET['search_value']

    context = {
        'data': []
    }

    if len(search_value) > 2:
        for row in go_customers.objects.filter(customercompany__contains=search_value)[:10]:
            context['data'].append('{} ({})'.format(row.customercompany, row.customernumber))

    return JsonResponse(context)


@login_required(login_url='signin')
def get_customer(request, customer_number):

    data = {}

    fields = ('customercompany', 'customername', 'customercontact', 'customeraddress1', 'customeraddress2',
              'customeraddress3', 'customeraddress4', 'customeraddress5', 'customerpostcode', 'customeremail',
              'customermobilenumber', 'customerphonenumber', 'customernumber', 'customerfirstname', 'customersurname')

    customer_rec = go_customers.objects.get(customernumber=customer_number)

    for k in fields:
        data[k] = getattr(customer_rec, k)

    return JsonResponse({'data': data})


@login_required(login_url="signin")
def AgreementEnquiryList(request):

    agreement_extract = go_agreement_querydetail.objects.filter()
    if not request.GET.get('agreement_closed_reason'):
        agreement_extract = agreement_extract.exclude(agreement_closed_reason='Archived')
    agreement_list = agreement_querydetail_Filter(request.GET, queryset=agreement_extract)
    paginator = Paginator(agreement_list.qs, 9)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') or request.GET.get('customercompany') \
                 or request.GET.get('agreementclosedflag_id') or request.GET.get('agreementddstatus_id') \
                 or request.GET.get('agreement_status')

    request.session['arrears_by_arrears_return_querystring'] = {}
    request.session['arrears_by_arrears_return_querystring'] = request.get_full_path()

    return render(request, 'core_agreement_crud/agreement_management.html', {'agreement_list': agreement_list,
                                                           'agreement_list_qs': pub,
                                                           'requiredtabs': str(requiredtabs()),
                                                           'has_filter': has_filter,
                                                           'agreement_closed_reason': request.GET.get('agreement_closed_reason')
                                                           })


def active(request):
    return JsonResponse({
        'count': go_agreement_querydetail.objects.filter(agreement_stage='3', agreementclosedflag_id='901').count()
    })


@login_required(login_url="signin")
def scapegoat(request):
    # agreement_extract = go_agreement_querydetail.objects.all()
    # agreement_list = agreement_querydetail_Filter(request.GET, queryset=agreement_extract)

    scapegoat_extract = go_editor_history.objects.all()
    scapegoat_list = go_editor_history_Filter(request.GET, queryset=scapegoat_extract)

    paginator = Paginator(scapegoat_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreement_id') \
                or request.GET.get('user_id') or request.GET.get('action') \
                or request.GET.get('updated')
                # or request.GET.get('customercompany') \

    return render(request, 'core_agreement_crud/scapegoat.html', {'scapegoat_list': scapegoat_list,
                                                                  'scapegoat_list_qs': pub,
                                                                  'requiredtabs': str(requiredtabs()),
                                                                  'has_filter': has_filter
                                                                  })


@login_required(login_url="signin")
def AgreementManagementDetail(request, agreement_id):

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)\
                        .order_by('transtypedesc',)
    config = client_configuration.objects.get(client_id="NWCF")
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)

    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid='GO1',
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
        sales_tax_rate = config.other_sales_tax
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
    if settlement_figure is None:
        settlement_figure_vat = 0
    else:
        if agreement_type == 'Lease':
            settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
        else:
            settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid='GO1',
                                                                            transactiondate__lt=first_rental_date) \
                                                                            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                          transactionsourceid='GO1',
                                                                          transtypeid__isnull=True,
                                                                          transactiondate__gte=first_rental_date)\
                                                                          .count()
    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['GO2', 'GO3']).count()
    except:
        secondary_count = 0


    # Add Gross of Vat to account summary queryset
    row_index = 0
    for row in account_summary:
        if row.transactionsourceid in ['GO8','GO9'] and row.transvatpayment is not None:
            row.transgrosspayment = row.transnetpayment + row.transvatpayment

        else:
            row.transgrosspayment = row.transnetpayment * decimal.Decimal(sales_tax_rate)
        if row.transactionsourceid in ['GO1', 'GO2', 'GO3']:
            if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
                row_index += 1
        row.row_index = row_index

    # Add Gross of Vat to account detail queryset
    for row in account_detail:

        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    # Return to Template
    return render(request, 'core_agreement_crud/agreement_management_detail.html',
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
                 'go_id':go_id
                 })


@login_required(login_url="signin")
def agreement_management_tab1(request):

    errors = {}
    context = {}

    template = 'core_agreement_crud/agreement_management_tab1.html'

    context['username'] = request.user

    # TODO: PAF Changes - Start
    customer = 'PAF'
    Agreement_Type_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Agreement Type')
    Funder_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Funder')
    Broker_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Broker')

    context['Agreement_Type_Select'] = Agreement_Type_Selectable.selectable
    context['Funder_Select'] = Funder_Selectable.selectable
    context['Broker_Select'] = Broker_Selectable.selectable

    Broker_Selectable = 0

    # Just A Test
    Selectable = go_selectable_functionality.objects.filter(agreement_type=Agreement_Type_Selectable.selectable,
                                                            funder=Funder_Selectable.selectable, broker=Broker_Selectable)

    Risk_Fee_Info = Selectable.get(customer=customer, function='Risk Fee')
    Bamf_Fee_Info = Selectable.get(customer=customer, function='Bamf Fee')
    Secondaries_Info = Selectable.get(customer=customer, function='Secondaries')
    Title_Info = Selectable.get(customer=customer, function='Title')
    Security_Info = Selectable.get(customer=customer, function='Security')
    Amf_Fee_Info = Selectable.get(customer=customer, function='Amf Fee')
    Doc_Fee_Info = Selectable.get(customer=customer, function='Doc Fee')

    context['Risk_Fee_Visible'] = Risk_Fee_Info.visible
    context['Bamf_Fee_Visible'] = Bamf_Fee_Info.visible
    context['Secondaries_Visible'] = Secondaries_Info.visible
    context['Title_Visible'] = Title_Info.visible
    context['Security_Visible'] = Security_Info.visible
    context['Amf_Fee_Visible'] = Amf_Fee_Info.visible
    context['Doc_Fee_Visible'] = Doc_Fee_Info.visible

    context['Risk_Fee_Info_Selectable'] = Risk_Fee_Info.selectable
    context['Bamf_Fee_Info_Selectable'] = Bamf_Fee_Info.selectable
    context['Secondaries_Info_Selectable'] = Secondaries_Info.selectable
    context['Title_Info_Selectable'] = Title_Info.selectable
    context['Security_Info_Selectable'] = Security_Info.selectable
    context['Amf_Fee_Info_Selectable'] = Amf_Fee_Info.selectable
    context['Doc_Fee_Info_Selectable'] = Doc_Fee_Info.selectable

    # Just a Test

    doc_flag = True
    # TODO: PAF Changes - End
    risk_flag = True
    bamf_flag = True
    secondary_flag = True
    title_flag = True
    security_flag = True
    amf_flag = True

    if request.method == 'POST':

        try:

            a_id = re.sub('\\s+', '', request.POST['agreement_id'])
            a_type = request.POST['agreement_type']
            broker = request.POST['broker_type']
            funder = request.POST['funder_code']
            company = request.POST['company_name']
            # TODO: PAF Changes - Start
            doc_flag = request.POST['doc_flag'] or 0
            if Risk_Fee_Info.visible == 1:
                risk_flag = request.POST['risk_flag'] or 0
            else:
                risk_flag = 0
            if Bamf_Fee_Info.visible == 1:
                bamf_flag = request.POST['bamf_flag'] or 0
            else:
                bamf_flag = 0
            secondary_flag = request.POST['secondary_flag'] or 0
            title_flag = request.POST['title_flag'] or 0
            security_flag = request.POST['security_flag'] or 0
            amf_flag = request.POST['amf_flag'] or 0

            if broker == 'Broker':
                doc_flag = 0
            # TODO: PAF Changes - End
                risk_flag = 0
                bamf_flag = 0
                secondary_flag = 1
                title_flag = 1
                security_flag = 1
                amf_flag = 1

            customer_number = False

            addressline1 = request.POST['customeraddress1']
            addressline2 = request.POST['customeraddress2']
            addressline3 = request.POST['customeraddress3']
            addressline4 = request.POST['customeraddress4']
            addressline5 = request.POST['customeraddress5']
            addresspostcode = request.POST['customerpostcode']
            salesauthority = request.POST['agreementauthority']
            # contactname = request.POST['customercontact']
            firstname = request.POST['customerfirstname']
            surname = request.POST['customersurname']
            mobilephonenumber = request.POST['customermobilenumber']
            phonenumber = request.POST['customerphonenumber']
            email = request.POST['customeremail']
            company_ref_no = request.POST['company_ref_no']
            socialmedia1 = request.POST['social_media1']
            socialmedia2 = request.POST['social_media2']
            socialmedia3 = request.POST['social_media3']
            agreement_origin_flag = "GO"
            stage = "1"

            if validate_tab1(request.POST, errors):
                print('10:22')
                if request.POST.get('customernumber'):
                    customer_number = request.POST['customernumber']
                    print('10:23')
                # TODO: PAF Changes - Start
                broker_rec = go_broker.objects.get(broker_type=broker)
                funder_rec = go_funder.objects.get(id=funder)
                # profile_rec = go_profile_types.objects.get(profile_description=p_type)
                a_type_wip = go_agreement_definitions.objects.get(agreementdefname=a_type)
                agreement_def = go_agreement_definitions.objects.get(agreementdefid=a_type_wip.agreementdefid)

                # TODO: PAF Changes - End

                # val_rec = go_agreement_id_definitions.objects.get(broker=broker_rec, profile_type=profile_rec,
                #                                                agreement_definitions=agreement_def)

                if validate_agreement_number(a_id, errors, 'agreement_id', broker):

                    go_id = uuid.uuid1()

                    # Step 1: Create go_id record
                    go_id_obj = go_agreement_index(go_id=go_id, agreement_id=a_id, user=request.user,
                                                   broker=broker_rec, company_ref_no=company_ref_no,
                                                   social_media1=socialmedia1, social_media2=socialmedia2,
                                                   social_media3=socialmedia3,
                                                   # TODO: PAF Changes - Start
                                                   # agreement_type=a_type,
                                                   agreement_origin_flag=agreement_origin_flag, doc_flag = doc_flag,
                                                   # TODO: PAF Changes - Start
                                                   risk_flag=risk_flag, bamf_flag=bamf_flag,
                                                   secondary_flag=secondary_flag, amf_flag=amf_flag,
                                                   title_flag=title_flag, security_flag=security_flag, funder=funder_rec)
                    go_id_obj.save()

                    new_rec = {
                        'go_id': go_id_obj,
                        'agreementnumber': a_id,
                        'agreementagreementtypeid': agreement_def
                    }

                    customer_rec = {
                        'customercompany': company,
                        'customeraddress1': addressline1,
                        'customeraddress2': addressline2,
                        'customeraddress3': addressline3,
                        'customeraddress4': addressline4,
                        'customeraddress5': addressline5,
                        'customerpostcode': addresspostcode,
                        'customercontact': firstname + ' ' + surname,
                        'customerfirstname': firstname,
                        'customersurname': surname,
                        'customermobilenumber': mobilephonenumber,
                        'customerphonenumber': phonenumber,
                        'customeremail': email
                    }

                    customer_action = None

                    if customer_number:
                        cust_obj = go_customers.objects.get(customernumber=customer_number)
                        for k in customer_rec:
                            setattr(cust_obj, k, customer_rec[k])
                        cust_obj.save()
                        if request.POST['customerchanges'] not in (0, "0"):
                            customer_action = 'update'

                    else:
                        customer_action = 'create'
                        customer_rec['customernumber'] = generate_customer_number()
                        cust_obj = go_customers(**customer_rec)
                        cust_obj.save()

                    go_agreement_1 = go_agreements(agreementcreator=request.user,
                                                   agreementauthority=salesauthority,
                                                   # agreement_stage=stage,
                                                   **new_rec)

                    go_agreement_2 = go_agreement_querydetail(customercompany=company,
                                                              agreementcustomernumber=cust_obj,
                                                              agreementcreator=request.user,
                                                              agreementauthority=salesauthority,
                                                              agreementdefname=agreement_def.agreementdefname,
                                                              agreement_stage=stage, **new_rec)
                    failed = 0
                    try:
                        go_id_obj.save()
                        failed = 1
                        go_agreement_1.save()
                        failed = 2
                        go_agreement_2.save()
                    except Exception as e:
                        if failed > 1:
                            go_agreement_1.delete()
                        if failed > 0:
                            go_id_obj.delete()

                    # agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage)

                    url = reverse('core_agreement_crud:agreement_management_tab2', args=[a_id])
                    if customer_action:
                        url += '?customer_action={}'.format(customer_action)

                    return redirect(url)

        except Exception as e:
            context['error'] = e
            context['error'] = '{} {}'.format(e, traceback.format_exc())

    context['profile_types'] = go_profile_types.objects.filter(selectable=True)
    context['sales_authorities'] = go_sales_authority.objects.filter(selectable=True)
    context['brokers'] = go_broker.objects.filter(selectable=True)
    context['funders'] = go_funder.objects.filter(selectable=True).order_by('funder_description')
    context['types'] = go_agreement_definitions.objects.filter(selectable=True)

    context['errors'] = errors

    context['values'] = request.POST.copy()
    if context['values'].get('funder_code'):
        context['values']['funder_code'] = int(context['values']['funder_code'])
    # TODO: PAF Changes - Start
    # if context['values'].get('agreement_type'):
    #     context['values']['agreement_type'] = int(context['values']['agreement_type'])
    #
    #     print('14:16')
    #     print(context['values']['agreement_type'])

    # Configure profile switches
    if context['errors'] or context['errors']:

        if request.POST.get('doc_flag', 0) == "1":
            context['doc_flag_on'] = True
    # TODO: PAF Changes - End
        if request.POST.get('risk_flag', 0) == "1":
            context['risk_flag_on'] = True
        if request.POST.get('bamf_flag', 0) == "1":
            context['bamf_flag_on'] = True
        if request.POST.get('security_flag', 0) == "1":
            context['security_flag_on'] = True
        if request.POST.get('secondary_flag', 0) == "1":
            context['secondary_flag_on'] = True
        if request.POST.get('title_flag', 0) == "1":
            context['title_flag_on'] = True
        if request.POST.get('amf_flag', 0) == "1":
            context['amf_flag_on'] = True
    else:
        # TODO: PAF Changes - Start
        context['doc_flag_on'] = doc_flag
        # TODO: PAF Changes - End
        context['risk_flag_on'] = risk_flag
        context['bamf_flag_on'] = bamf_flag
        context['security_flag_on'] = security_flag
        context['secondary_flag_on'] = secondary_flag
        context['title_flag_on'] = title_flag
        context['amf_flag_on'] = amf_flag

    if (context.get('errors') or context.get('error')) and not request.POST.get('customernumber'):
        context['new_customer'] = True

    # print("errors")
    # print(errors)

    return render(request, template, context)


@login_required(login_url='signin')
def agreement_management_tab1_1(request, current_agreement_id):

    errors = {}
    error = None  # Global error
    context = {}

    try:
        transaction_summary_extract = go_account_transaction_summary.objects.filter(agreementnumber=current_agreement_id,
                                                                                    transactionbatch_id__contains='GO')
        context['transaction_summary_extract_count'] = transaction_summary_extract.count()
        transition = transition_log.objects.filter(agreementnumber=current_agreement_id)
        context['transition_count'] = transition.count()

    except:
        error = None

    template = 'core_agreement_crud/agreement_management_tab1.html'
    # TODO : PAF Changes - Start
    customer = 'PAF'
    Agreement_Type_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Agreement Type')
    Funder_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Funder')
    Broker_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Broker')

    context['Agreement_Type_Select'] = Agreement_Type_Selectable.selectable
    context['Funder_Select'] = Funder_Selectable.selectable
    context['Broker_Select'] = Broker_Selectable.selectable

    Agreement_Type_Selectable = 1
    Funder_Selectable = 1
    Broker_Selectable = 0

    # Just A Test
    Selectable = go_selectable_functionality.objects.filter(agreement_type=Agreement_Type_Selectable,
                                                            funder=Funder_Selectable, broker=Broker_Selectable)

    Risk_Fee_Info = Selectable.get(customer=customer, function='Risk Fee')
    Bamf_Fee_Info = Selectable.get(customer=customer, function='Bamf Fee')
    Secondaries_Info = Selectable.get(customer=customer, function='Secondaries')
    Title_Info = Selectable.get(customer=customer, function='Title')
    Security_Info = Selectable.get(customer=customer, function='Security')
    Amf_Fee_Info = Selectable.get(customer=customer, function='Amf Fee')
    Doc_Fee_Info = Selectable.get(customer=customer, function='Doc Fee')

    context['Risk_Fee_Visible'] = Risk_Fee_Info.visible
    context['Bamf_Fee_Visible'] = Bamf_Fee_Info.visible
    context['Secondaries_Visible'] = Secondaries_Info.visible
    context['Title_Visible'] = Title_Info.visible
    context['Security_Visible'] = Security_Info.visible
    context['Amf_Fee_Visible'] = Amf_Fee_Info.visible
    context['Doc_Fee_Visible'] = Doc_Fee_Info.visible

    context['Risk_Fee_Info_Selectable'] = Risk_Fee_Info.selectable
    context['Bamf_Fee_Info_Selectable'] = Bamf_Fee_Info.selectable
    context['Secondaries_Info_Selectable'] = Secondaries_Info.selectable
    context['Title_Info_Selectable'] = Title_Info.selectable
    context['Security_Info_Selectable'] = Security_Info.selectable
    context['Amf_Fee_Info_Selectable'] = Amf_Fee_Info.selectable
    context['Doc_Fee_Info_Selectable'] = Doc_Fee_Info.selectable
    # TODO : PAF Changes - End


    go_id_detail = None
    customer_detail = None
    agreement_detail = None

    bamf_flag = None
    risk_flag = None
    # TODO : PAF Changes - Start
    doc_flag = None
    # TODO : PAF Changes - End
    amf_flag = None
    security_flag = None
    title_flag = None
    secondary_flag = None

    values = request.POST.copy()

    context['username'] = request.user
    values['agreement_id'] = current_agreement_id

    try:
        go_id_detail = go_agreement_index.objects.get(agreement_id=current_agreement_id)
        agreement = go_agreements.objects.get(agreementnumber=current_agreement_id)
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=current_agreement_id)
        context['agreement_detail'] = agreement_detail
    except:
        print('failed')
        # TODO : PAF Changes - Start
        values['agreement_type'] = agreement_detail.agreementdefname
        # values[''] = agreement_detail.agreementdefname
        # TODO : PAF Changes - End
        error = 'Agreement Number Not Found'

    if not error:
        try:
            customer_detail = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
            context['agreement_customer'] = customer_detail
            context['agreement_customer_name'] = customer_detail.customercompany
        except:
            error = 'Customer Record Not Found'
            # error = None

    customer_fields = ('customeraddress1', 'customeraddress2', 'customeraddress3', 'customeraddress4',
                       'customeraddress5', 'customerpostcode', 'customermobilenumber',
                       'customerphonenumber', 'customeremail', 'customernumber', 'customerfirstname', 'customersurname')

    if not error:

        bamf_flag = go_id_detail.bamf_flag
        risk_flag = go_id_detail.risk_flag
        # TODO: PAF Changes - Start
        doc_flag = go_id_detail.doc_flag
        # TODO: PAF Changes - End
        amf_flag = go_id_detail.amf_flag
        security_flag = go_id_detail.security_flag
        title_flag = go_id_detail.title_flag
        secondary_flag = go_id_detail.secondary_flag

        try:

            if request.method == 'GET':

                go_id_fields = (
                'broker', 'profile', 'company_ref_no', 'social_media1', 'social_media2', 'social_media3',
                'agreement_origin_flag',)

                agreement_fields = ('agreementauthority', 'agreementcustomernumber')

                for f in go_id_fields:
                    values[f] = getattr(go_id_detail, f) or ''

                for f in customer_fields:
                    values[f] = getattr(customer_detail, f) or ''

                for f in agreement_fields:
                    values[f] = getattr(agreement_detail, f) or ''

                values['agreement_type'] = agreement_detail.agreementdefname
                values['company_name'] = agreement_detail.customercompany
                values['broker_type'] = go_id_detail.broker.broker_description
                values['funder_code'] = go_id_detail.funder.id

                print( values['funder_code'] )
                # print(go_id_detail.agreement_type)
                # print('go_id_detail.agreement_type')
                # Agreement_type_wip = go_agreement_definitions.objects.get(agreementdefid=go_id_detail.agreement_type)
                # print(Agreement_type_wip)
                # values['agreement_type'] = go_id_detail.agreement_type
                # print(values['agreement_type'])
            print('10:42')
            if request.method == 'POST':

                if validate_tab1(request.POST, errors):
                    print('10:43')
                    if request.POST.get('customernumber'):
                        customer_number = request.POST['customernumber']
                    # TODO : PAF Changes - Start
                    broker_rec = go_broker.objects.get(broker_type=request.POST['broker_type'])  # PAF Changes
                    if request.POST.get('funder_code'):
                        funder_rec = go_funder.objects.get(id=request.POST['funder_code'])
                    # profile_rec = go_profile_types.objects.get(profile_description=p_type)

                    a_type_wip = go_agreement_definitions.objects.get(agreementdefname=request.POST['agreement_type'])
                    agreement_def = go_agreement_definitions.objects.get(agreementdefid=a_type_wip.agreementdefid)

                    # agreement_def = go_agreement_definitions.objects.get(agreementdefid=request.POST['agreement_type'])
                    # TODO : PAF Changes - End

                    # val_rec = go_agreement_id_definitions.objects.get(broker=broker_rec, profile_type=profile_rec,
                    #                                                agreement_definitions=agreement_def)

                    print('funder_rec')
                    print(funder_rec)

                    a_id = request.POST['agreement_id']
                    agreement_origin_flag = "GO"

                    process = False

                    validate_args = (a_id, errors, 'agreement_id', request.POST['broker_type'])
                    if validate_agreement_number(*validate_args, current_agreement_id=current_agreement_id):
                        process = True

                    if process:

                        new_go_id_detail = go_agreement_index.objects.get(agreement_id=current_agreement_id)

                        # Update go_id table
                        new_go_id_detail.user = request.user
                        new_go_id_detail.agreement_id = a_id
                        new_go_id_detail.broker = broker_rec
                        if request.POST.get('funder_code'):
                            new_go_id_detail.funder = funder_rec
                        # TODO: PAF Changes - Start
                        doc_flag = request.POST.get('doc_flag')
                        if Risk_Fee_Info.visible == 1:
                            risk_flag = request.POST['risk_flag'] or 0
                        else:
                            risk_flag = 0
                        if Bamf_Fee_Info.visible == 1:
                            bamf_flag = request.POST['bamf_flag'] or 0
                        else:
                            bamf_flag = 0
                        # TODO: PAF Changes - End
                        secondary_flag = request.POST.get('secondary_flag')
                        security_flag = request.POST.get('security_flag')
                        title_flag = request.POST.get('title_flag')
                        # TODO: PAF Changes - Start
                        amf_flag = request.POST.get('amf_flag')

                        # if request.POST['broker_type'] == 'Broker':
                        #     risk_flag = 0
                        #     bamf_flag = 0
                        #     secondary_flag = 1
                        #     security_flag = 1
                        #     title_flag = 1
                        #     amf_flag = 1
                        # else:
                        #     amf_flag = 0
                        # TODO: PAF Changes - End

                        new_go_id_detail.social_media1 = request.POST['social_media1']
                        new_go_id_detail.social_media2 = request.POST['social_media2' ]
                        new_go_id_detail.social_media3 = request.POST['social_media3']
                        new_go_id_detail.company_ref_no = request.POST['company_ref_no']
                        new_go_id_detail.agreement_origin_flag = agreement_origin_flag
                        new_go_id_detail.risk_flag = risk_flag or 0
                        # TODO: PAF Changes - Start
                        new_go_id_detail.doc_flag = doc_flag or 0
                        # TODO: PAF Changes - End
                        new_go_id_detail.bamf_flag = bamf_flag or 0
                        new_go_id_detail.secondary_flag = secondary_flag or 0
                        new_go_id_detail.title_flag = title_flag or 0
                        new_go_id_detail.security_flag = security_flag or 0
                        new_go_id_detail.amf_flag = amf_flag or 0
                        new_go_id_detail.save()

                        # Create/update customer table

                        customer_action = None

                        if request.POST['customernumber']:
                            cust_obj = go_customers.objects.get(customernumber=request.POST['customernumber'])
                            if request.POST['customerchanges'] not in (0, "0"):
                                customer_action = 'update'
                        else:
                            cust_obj = go_customers(customernumber=generate_customer_number())
                            customer_action = 'create'

                        for k in customer_fields:
                            if k != 'customernumber':
                                setattr(cust_obj, k, request.POST[k])

                        cust_obj.customercompany = request.POST['company_name']

                        cust_obj.save()

                        # Update agreement tables

                        update_values = {
                            'go_id': new_go_id_detail,
                            'agreementnumber': a_id,
                            'agreementagreementtypeid': agreement_def,
                            'agreementauthority': request.POST['agreementauthority'],
                            'agreementcustomernumber': cust_obj,
                            'customercompany': request.POST['company_name']
                        }
                        for k in update_values:
                            setattr(agreement, k, update_values[k])
                            setattr(agreement_detail, k, update_values[k])

                        # agreements(agreement_stage=stage).save()

                        agreement.save()

                        agreement_detail.agreementdefname = agreement_def.agreementdefname

                        agreement_detail.save()
                        if go_account_transaction_summary.objects.filter(go_id=new_go_id_detail).exclude(transactionbatch_id='').exclude(transactionbatch_id__isnull=True).count() == 0:
                            recalculate_function(a_id)


                        url = reverse('core_agreement_crud:agreement_management_tab2', args=[a_id])
                        if customer_action:
                            url += '?customer_action={}'.format(customer_action)

                        return redirect(url)

                values = request.POST

        except Exception as e:
            error = '{} {}'.format(e, traceback.format_exc())

    if (error or error) and not request.POST.get('customernumber'):
        context['new_customer'] = True

    # Template vars

    context['error'] = error
    context['errors'] = errors
    context['values'] = values
    context['go_id_detail'] = go_id_detail

    # # TODO : PAF Changes - Start
    # if context['values'].get('funder_code'):
    #     print(context['values']['funder_code'])
    #     context['funder_code'] = go_id_detail.funder.id
    #     context['values']['funder_code'] == (context['funder_code'])
    #     print(context['funder_code'])
    # # TODO : PAF Changes - End

    # context['profile_types'] = go_profile_types.objects.filter(selectable=True)
    context['sales_authorities'] = go_sales_authority.objects.filter(selectable=True)
    context['brokers'] = go_broker.objects.filter(selectable=True)
    context['types'] = go_agreement_definitions.objects.filter(selectable=True)
    context['funders'] = go_funder.objects.filter(selectable=True).order_by('funder_description')

    context['update'] = True

    context['agreement_id'] = current_agreement_id

    # print('go_id.funder:', go_id_detail.funder)
    # print('values.funder_code:', values.get('funder_code'))
    # print('values.broker_type:', values.get('broker_type'))

    # Configure profile switches
    if context['errors'] or context['errors']:
        # TODO: PAF Changes - Start
        if request.POST.get('doc_flag', 0) == "1":
            context['doc_flag_on'] = True
        # TODO: PAF Changes - End
        if request.POST.get('risk_flag', 0) == "1":
            context['risk_flag_on'] = True
        if request.POST.get('bamf_flag', 0) == "1":
            context['bamf_flag_on'] = True
        if request.POST.get('security_flag', 0) == "1":
            context['security_flag_on'] = True
        if request.POST.get('secondary_flag', 0) == "1":
            context['secondary_flag_on'] = True
        if request.POST.get('title_flag', 0) == "1":
            context['title_flag_on'] = True
        if request.POST.get('amf_flag', 0) == "1":
            context['amf_flag_on'] = True
    else:
        # TODO: PAF Changes - Start
        context['doc_flag_on'] = doc_flag
        # TODO: PAF Changes - End
        context['risk_flag_on'] = risk_flag
        context['bamf_flag_on'] = bamf_flag
        context['security_flag_on'] = security_flag
        context['secondary_flag_on'] = secondary_flag
        context['title_flag_on'] = title_flag
        context['amf_flag_on'] = amf_flag

    return render(request, template, context)


@login_required(login_url='signin')
def agreement_management_tab2(request, agreement_id):

    error = None
    errors = {}
    values = {}
    context = {'agreement_id': agreement_id}
    template = 'core_agreement_crud/agreement_management_tab2.html'

    go_id = None
    agreement_detail = None

    # TODO: PAF Changes - Start
    customer = 'PAF'
    Payment_Method_Selectable = go_selectable_functionality.objects.get(customer=customer, function='Payment Method')

    context['Payment_Method_Select'] = Payment_Method_Selectable.selectable
    # TODO: PAF Changes - End

    try:
        transaction_summary_extract = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                                    transactionbatch_id__contains='GO')
        context['transaction_summary_extract_count'] = transaction_summary_extract.count()
        transition = transition_log.objects.filter(agreementnumber=agreement_id)
        context['transition_count'] = transition.count()
    except:
        error = None
    # TODO: PAF Changes - Start
    from .models import go_collection_schedule
    # TODO: PAF Changes - End
    try:
        go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
        context['agreement_detail'] = agreement_detail
        agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
        context['agreement_customer'] = agreement_customer
        context['username'] = request.user
        context['batches'] = []
        for row in DrawDown.objects.filter(due_date__gte=datetime.datetime.now(), status='OPEN', agreement_id=agreement_id):
            context['batches'].append(json.dumps({'batch_header': row.batch_header.reference,
                                                  'created': row.created.strftime("%d/%m/%Y"),
                                                  'user': row.user.username if row.user else None}))
        context['batches'] = json.dumps(context['batches'])
    except Exception as e:
        error = str(e)
        print(e)

    if not error:

        if request.method == 'GET':

            try:

                agreement_date_fields = ('agreementagreementdate', 'agreementupfrontdate', 'agreementfirstpaymentdate')

                agreement_fields = ('agreementbankreference', 'agreementbanksortcode', 'agreementresidualdate',
                                    'agreementbankaccountnumber', 'agreementbankaccountname')

                for f in agreement_date_fields:
                    dt = getattr(agreement_detail, f)
                    if dt and isinstance(dt, datetime.datetime):
                        values[f] = dt.strftime("%Y-%m-%d")

                for f in agreement_fields:
                    if go_id.manual_payments:
                        values[f] = ''
                    else:
                        values[f] = getattr(agreement_detail, f)

                values['agreementresidualdate'] = agreement_detail.agreementresidualdate
                values['term'] = go_id.term
                # TODO: PAF Changes - Start
                values['collection_schedule'] = agreement_detail.agreementcollectiontype
                values['payment_method'] = agreement_detail.agreementpaymentmethod
                # TODO: PAF Changes - End
                if values['agreementresidualdate'] and isinstance(values['agreementresidualdate'], datetime.datetime):
                    values['agreementresidualdate'] = values['agreementresidualdate'].strftime("%d/%m/%Y")

                if not values['agreementbankreference']:
                    values['agreementbankreference'] = generate_dd_reference(agreement_id)

                for k in values.keys():
                    if values[k] is None:
                        values[k] = ''

            except Exception as e:
                tb = traceback.format_exc()
                error = '{} {}'.format(e, tb)

        if request.method == 'POST':

            values = request.POST

            try:

                agreementdate = request.POST.get('agreementagreementdate')

                termlength = request.POST.get('term')

                upfrontdate =request.POST.get('agreementupfrontdate')

                firstpaydate =request.POST.get('agreementfirstpaymentdate')

                residualdate = request.POST.get('agreementresidualdate')
                # TODO: PAF Changes - Start
                upfront_payments = request.POST['upfront_payments_input']
                rental_payments = request.POST['rental_payments_input']
                VAT_Payment = request.POST['VAT_Payment_input']
                go_collection_schedule_option = request.POST.get('go_collection_schedule')
                go_payment_method_option = request.POST.get('go_payment_method')

                # TODO: PAF Changes - End
                ddiref = request.POST.get('agreementbankreference')

                accountname = request.POST.get('agreementbankaccountname')

                sortcode = request.POST.get('agreementbanksortcode')

                accountnumber = request.POST.get('agreementbankaccountnumber')
                # TODO: PAF Changes - Start
                # if request.POST.get('manual_payments'):
                #     if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
                #         raise Exception("This agreement has a transaction that is currently in an open batch.")
                #     try:
                #         manual_payments = int(request.POST.get('manual_payments', 0)) or 0
                #     except:
                #         manual_payments = 0
                # else :
                #     manual_payments = 0

                if request.POST.get('go_payment_method_option'):
                    if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
                        raise Exception("This agreement has a transaction that is currently in an open batch.")
                    try:
                        manual_payments = int(request.POST.get('go_payment_method_option', 0)) or 0
                    except:
                        manual_payments = 0
                else :
                    manual_payments = 0

                # TODO: PAF Changes - End

                stage = "2"
                if agreement_detail.agreement_stage < str(requiredtabs()):
                    go_agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage)

                if not agreementdate:
                    errors['agreementagreementdate'] = 'Agreement Date Required'
                elif not validate_date(agreementdate):
                    errors['agreementagreementdate'] = 'Agreement Date Invalid'

                if not termlength:
                    errors['term'] = 'Term Length Required'
                # TODO : PAF Changes - Start
                if not go_collection_schedule_option:
                    errors['go_collection_schedule'] = 'Collection Schedule Required'
                if not go_payment_method_option:
                    errors['go_payment_method'] = 'Payment Method Required'

                if not firstpaydate:
                    errors['agreementfirstpaymentdate'] = 'First Due Date Required'
                elif not validate_date(firstpaydate):
                    errors['agreementfirstpaymentdate'] = 'First Due Date Invalid'
                else:
                    firstpaydate_dt = datetime.datetime.strptime(firstpaydate, "%Y-%m-%d")
                    # if int(firstpaydate_dt.strftime("%d")) > 28:
                    #     errors['agreementfirstpaymentdate'] = 'First Due Date Must Not Exceed 28th'
                # TODO : PAF Changes - End
                if not residualdate:
                    errors['agreementresidualdate'] = 'Invalid Term Length / First Due Date'
                elif not validate_date(residualdate, format="%d/%m/%Y"):
                    errors['agreementresidualdate'] = 'Last Primary Date Invalid'

                if not upfrontdate:
                    errors['agreementupfrontdate'] = 'Upfront Date Required'
                elif not validate_date(upfrontdate):
                    errors['agreementupfrontdate'] = 'Upfront Date Invalid'

                print('go_payment_method_option')
                print(go_payment_method_option)
                print(manual_payments)
                if manual_payments:
                # if manual_payments:
                    if not ddiref:
                        errors['agreementbankreference'] = 'Direct Debit Instruction Reference Required'

                    if not accountname:
                        errors['agreementbankaccountname'] = 'Account Name Required'

                    if not sortcode:
                        errors['agreementbanksortcode'] = 'Sort Code Required'

                    if not accountnumber:
                        errors['agreementbankaccountnumber'] = 'Account Number Required'

                    if accountnumber:
                        if len(accountnumber) != 8:
                            errors['agreementbankaccountnumber'] = 'Account Number must be 8 digits'
                        elif not re.search(r'^\d+$', accountnumber):
                            errors['agreementbankaccountnumber'] = 'Account Number must contain digits only'

                    if sortcode:
                        if len(sortcode) != 6:
                            errors['agreementbanksortcode'] = 'Sort Code must be 6 digits'
                        elif not re.search(r'^\d+$', sortcode):
                            errors['agreementbanksortcode'] = 'Sort Code must contain digits only'



                create_ddi = True

                if not errors:

                    residualdate = datetime.datetime.strptime(residualdate, "%d/%m/%Y")

                    if manual_payments != 1:
                        if go_id.funder.provider == 'datacash':
                            cancel_ddi_with_datacash(agreement_id)
                            create_ddi = False
                        # elif go_id.funder.provider == 'eazycollect':
                        #     cancel_contract(agreement_id)
                        #     create_ddi = False

                    if ddiref == agreement_detail.agreementbankreference and accountname == agreement_detail.agreementbankaccountname and accountnumber == agreement_detail.agreementbankaccountnumber and sortcode == agreement_detail.agreementbanksortcode:
                        create_ddi = False
                        print(ddiref)
                        print(agreement_detail.agreementbankreference)
                    else:
                        create_ddi = True
                    print(accountnumber)
                    print(agreement_detail.agreementbankaccountnumber)
                    if create_ddi:
                        search_args = {
                            'reference': ddiref,
                            'sequence': 9999,
                            'agreement_no': agreement_id,
                            'account_number': accountnumber,
                            'sort_code': sortcode,
                            'account_name': accountname,
                            'provider': go_id.funder.provider

                        }
                        if DDHistory.objects.filter(**search_args).exists():
                            # They're just tabbing through. Don't process.
                            create_ddi = False

                    if create_ddi:
                        if DDHistory.objects.filter(reference=ddiref).exists():
                            errors['agreementbankreference'] = 'This Direct Debit Instruction Reference has been used previously.'

                if not errors:

                    if create_ddi:

                        try:
                            if go_id.funder.provider == 'datacash':
                                context['reference'] = create_ddi_with_datacash(
                                    agreement_id,
                                    request.POST['agreementbankreference'],
                                    request.POST['agreementbankaccountname'],
                                    request.POST['agreementbankaccountnumber'],
                                    request.POST['agreementbanksortcode'],
                                    request.user
                                )
                            elif go_id.funder.provider == 'eazycollect':
                                create_ddi_with_eazycollect(agreement_id,
                                                            request.POST['agreementbankreference'],
                                                            request.POST['agreementbankaccountname'],
                                                            request.POST['agreementbankaccountnumber'],
                                                            request.POST['agreementbanksortcode'],
                                                            user=request.user)
                            else:
                                raise Exception("FATAL: Unknown Provider.")
                            # TODO: Cater for Eazycollect
                        except Exception as e:
                            context['datacash_failed'] = True
                            if str(e) == 'Invalid CLIENT/PASS':
                                context['datacash_failed_fatal'] = True
                            elif str(e) == 'FATAL: Unknown Provider.':
                                context['datacash_failed_fatal'] = True
                            elif str(e) == 'Datacash Service Unavailable':
                                context['datacash_failed_fatal'] = True

                        if context.get('reference'):
                            update_ddi_status(agreement_id, 'Active DD')
                        else:
                            update_ddi_status(agreement_id, 'Inactive DD')

                    agreement_rec = {
                        # 'agreement_stage' = stage,
                        'agreementagreementdate': agreementdate,
                        'agreementupfrontdate': upfrontdate,
                        'agreementfirstpaymentdate': firstpaydate,
                        'agreementresidualdate': residualdate,
                        # TODO : PAF Changes - Start
                        'agreementpaymentmethod': go_payment_method_option,
                        'agreementcollectiontype': go_collection_schedule_option,
                        # TODO : PAF Changes - End
                        'agreementbankreference': ddiref,
                        'agreementbankaccountname': accountname,
                        'agreementbanksortcode': sortcode,
                        'agreementbankaccountnumber': accountnumber,
                        'agreementcreatedate' : datetime.datetime.now(),
                    }

                    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
                    go_agreements.objects.filter(go_id=go_id).update(**agreement_rec)
                    go_agreement_querydetail.objects.filter(go_id=go_id).update(**agreement_rec)

                    # apellio_extension_code = go_extensions.objects.filter(ap_extension_sequence=1)
                    # client_configuration.objects.filter(client_id=apellio_extension_code)
                    # TODO: PAF Changes - Start
                    go_id.agreement_structure_upfront = upfront_payments
                    go_id.agreement_structure_rentals = rental_payments
                    go_id.agreement_delay_vat_until = VAT_Payment
                    # TODO: PAF Changes - End
                    go_id.term = termlength
                    # TODO: PAF Changes - Start
                    # go_id.manual_payments = go_payment_method_option
                    go_id.manual_payments = manual_payments
                    # TODO: PAF Changes - End
                    go_id.save()

                    context['term'] = termlength
                    context['agreementfirstpaymentdate'] = firstpaydate
                    if go_account_transaction_summary.objects.filter(go_id=go_id).exclude(transactionbatch_id='').exclude(transactionbatch_id__isnull=True).count() == 0:
                        recalculate_function(agreement_id)

                    if not context.get('datacash_failed'):
                        url = reverse('core_agreement_crud:agreement_management_tab3', args=[agreement_id])
                        if create_ddi and go_payment_method_option == 1:
                            url += '?datacash_request=1'
                        return redirect(url)

            except Exception as e:
                error = str(e)
                print('{} {}'.format(e, traceback.format_exc()))
                # error = '{} {}'.format(e, traceback.format_exc())

    context['error'] = error
    context['errors'] = errors
    context['values'] = values
    context['go_id'] = go_id
    # TODO : PAF Changes - Start
    if go_id.agreement_delay_vat_until:
        context['VAT_Payment_input'] = go_id.agreement_delay_vat_until
        context['rental_payments_input'] = go_id.agreement_structure_rentals
        context['upfront_payments_input'] = go_id.agreement_structure_upfront
    context['go_collection_schedule'] = go_collection_schedule.objects.filter(selectable=True)
    context['go_payment_method'] = go_payment_method.objects.filter(selectable=True).order_by('payment_method')

    # TODO : PAF Changes - End
    context['customer_action'] = request.GET.get('customer_action')

    holidays = get_holidays()
    context['holidays'] = holidays

    days_before_dd_call = daysbeforecalldd()
    context['days_before_dd_call'] = days_before_dd_call

    days_before_setup_active = daysbeforeddsetup()
    if agreement_detail:
        if not agreement_detail.agreement_stage < str(requiredtabs()):
            context['next_due_date'] = get_next_due_date(agreement_id) or '2999-12-31'

    context['setup_active_date'] = numpy.busday_offset(datetime.datetime.today(), days_before_setup_active,
                                                       roll='forward', holidays=holidays).astype(datetime.date)

    context['call_active_date'] = numpy.busday_offset(datetime.datetime.today(),
                                                      days_before_dd_call + days_before_setup_active,
                                                      roll='forward', holidays=holidays).astype(datetime.date)

    context['days_before_setup_active'] = days_before_setup_active
    # # TODO : PAF Changes - Start
    # if go_id.manual_payments != 1:
    #     context['manual_payments_display'] = go_id.manual_payments
    #     print(context['manual_payments_display'])
    #     if errors:
    #         context['manual_payments_display'] = int(request.POST.get('manual_payments'))
    # # TODO : PAF Changes - End

    context['manual_payments_display'] = go_id.manual_payments
    if errors:
        context['manual_payments_display'] = (request.POST.get('manual_payments'))
    return render(request, template, context)


@login_required(login_url='signin')
def agreement_management_tab3(request, agreement_id):

    error = None
    errors = {}
    values = {}
    context = {'agreement_id': agreement_id}
    template = 'core_agreement_crud/agreement_management_tab3.html'

    context['agreementfirstpaymentdate'] = go_agreements.agreementfirstpaymentdate
    context['agreementupfrontdate'] = go_agreements.agreementupfrontdate
    context['agreementfirstpaymentdate'] = go_agreements.agreementfirstpaymentdate
    context['agreementresidualdate'] = go_agreements.agreementresidualdate
    context['agreementagreementdate'] = go_agreements.agreementagreementdate
    # context['agreementcreatedate'] = go_agreements.agreementcreatedate
    context['agreementauthority'] = go_agreements.agreementauthority
    context['agreement_customer'] = go_agreements.agreementcustomernumber
    # context['agreementdefname'] = agreements.agreementdefname
    # TODO : PAF Changes - Start
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    context['go_collection_schedule'] = agreement_detail.agreementcollectiontype
    config = client_configuration.objects.get(client_id="PAF")
    # TODO : PAF Changes - End
    context['agreement_detail'] = agreement_detail

    # agreement_customer = customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    context['agreement_customer'] = go_customers.customernumber

    account_detail = go_account_transaction_detail
    context['account_detail'] = account_detail

    context['username'] = request.user

    go_id = None
    agreement_detail = None
    account_detail = None

    try:
        transaction_summary_extract = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                                    transactionbatch_id__contains='GO')
        context['transaction_summary_extract_count'] = transaction_summary_extract.count()
        transition = transition_log.objects.filter(agreementnumber=agreement_id)
        context['transition_count'] = transition.count()

    except:
        error = None

    try:
        # TODO : PAF Changes - Start
        go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
        doc_fee = go_selectable_functionality.objects.get(customer='PAF', function='Doc Fee')
        context['agreement_detail'] = agreement_detail
        context['term'] = go_id.term
        context['amf_amount'] = config.bamf_fee_amount_net
        # TODO : PAF Changes - End
        # context['pro#file'] = go_id.pro#file_id
        context['broker'] = go_id.broker_id

        context['agreementfirstpaymentdate'] = go_agreement_querydetail.agreementfirstpaymentdate

    except:
        error = 'Agreement Number Not Found'

    wip_context_button_status = 'ACTIVE'
    if not error:
        if go_id.consolidation_info:
            if "::" in go_id.consolidation_info:
                context['consolidations'] = 'Consolidation of ' + ', '.join(go_id.consolidation_info.split("::"))
            else:
                context['consolidations'] = go_id.consolidation_info
                wip_context_button_status = 'INACTIVE'
            context['consolidation_button_status'] = wip_context_button_status

    if request.method == 'GET' and not error:

        try:

            go_fields = ('agreement_instalment_gross', 'agreement_total_fees',
                         'agreement_payable_net', 'agreement_payable_gross')

            agreement_fields = ('agreementinstalmentnet', 'agreementinstalmentvat', 'agreementoriginalprincipal',
                                'agreementcharges')

            for f in go_fields:
                values[f] = getattr(go_id, f)

            for f in agreement_fields:
                values[f] = getattr(agreement_detail, f)

            # TODO : PAF Changes - Start
            doc_flag = go_id.doc_flag
            if doc_flag == 1:
                if go_id.agreement_doc_fee:
                    values['doc_fee'] = go_id.agreement_doc_fee
                else:
                    values['doc_fee'] = doc_fee.selectable_value
            else:
                values['doc_fee'] = go_id.agreement_doc_fee
            # TODO : PAF Changes - End
            values['risk_fee'] = go_id.agreement_risk_fee
            # values['bamf_fee'] = go_id.agreement_bamf_fee

            for k in values.keys():
                if values[k] is None:
                    values[k] = ''
                if values[k] and isinstance(values[k], Decimal):
                    values[k] = '{0:0,.2f}'.format(values[k])

            values['DateImplemented'] = datetime.date.today().strftime("%d/%m/%Y")

        except Exception as e:
            error = e

    if request.method == 'POST' and not error:

        values = request.POST

        try:

            docfee = request.POST['doc_fee']
            instalmentnet = request.POST['agreementinstalmentnet']
            instalmentvat = request.POST['agreementinstalmentvat']
            instalmentgross = request.POST['agreement_instalment_gross']
            principal = request.POST['agreementoriginalprincipal']
            charges = request.POST['agreementcharges']
            totalfees = request.POST['agreement_total_fees']
            payablenet = request.POST['agreement_payable_net']
            payablegross = request.POST['agreement_payable_gross']

            if go_id.broker_id == 1:
                riskfee = request.POST['risk_fee']
            else:
                riskfee = '0.00'
            # bamffee = request.POST['bamf_fee']
            date_implemented = request.POST['DateImplemented']

            if not docfee:
                errors['doc_fee'] = 'Doc Fee Required'

            if not instalmentnet:
                errors['agreementinstalmentnet'] = 'Instalment Amount Required'

            if not principal:
                errors['agreementoriginalprincipal'] = 'Principal Amount Required'

            # if principal < instalmentnet:
            #     errors['agreementoriginalprincipal'] = 'Principal should be greater than Instalments'

            # if charges:
            #     if float(re.sub(',', '', charges)) < float(0):
            #         errors['agreementcharges'] = 'Negative Charges'

            # if float(charges) /float(principal) > 5:
            #     errors['agreementoriginalprincipal'] = 'Charges Too High'


            # Decimal(re.sub(',', '', principal)

            #1.08 = commission

            # if principal+charges
            # 0.0125 = 0.15/12 = yield (15000*1.08)

            # a = (Decimal(re.sub(',', '', principal))) * Decimal(1.08)
            #
            if instalmentnet and charges:
                pmt_validation = -pmt(float(pmt_yield()), go_id.term, (float(re.sub(',', '', principal)))*float(pmt_commission()))
                if pmt_validation > (float(re.sub(',', '', instalmentnet))) and not request.POST.get('pmt_failed_but_continue'):
                    # print(pmt_validation)
                    errors['agreementoriginalprincipal'] = 'Please Check Principal and Instalments'
                    errors['agreementinstalmentnet'] = 'Please Check Principal and Instalments'
                    context['pmt_failed'] = True

            # if not context.get('pmt_failed'):
            #     url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
            #     url += '?pmt_request=1'
            #     return redirect(url)

            # c = b*go_id.term
            transactions = go_account_transaction_summary.objects.filter(go_id=go_id).exclude(transactionbatch_id='').exclude(transactionbatch_id__isnull=True).count()
            if not context.get('pmt_failed') and transactions == 0:
                if not errors:
                    go_account_transaction_summary.objects.filter(go_id=go_id, transactionsourceid='GO1').delete()
                    go_account_transaction_summary.objects.filter(go_id=go_id, transactionsourceid='GO3').delete()
                    go_account_transaction_detail.objects.filter(go_id=go_id, transactionsourceid='GO1').delete()
                    go_account_transaction_detail.objects.filter(go_id=go_id, transactionsourceid='GO3').delete()
                    agreement_rec = {
                        'agreementinstalmentnet': Decimal(re.sub(',', '', instalmentnet)),
                        'agreementinstalmentvat': Decimal(re.sub(',', '', instalmentvat)),
                        'agreementoriginalprincipal': Decimal(re.sub(',', '', principal)),
                        'agreementcharges': Decimal(re.sub(',', '', charges))
                    }
                    go_agreements.objects.filter(go_id=go_id).update(**agreement_rec)
                    go_agreement_querydetail.objects.filter(go_id=go_id).update(**agreement_rec)

                    go_id.agreement_doc_fee = Decimal(re.sub(',', '', docfee))
                    go_id.agreement_instalment_gross = Decimal(re.sub(',', '', instalmentgross))
                    go_id.agreement_total_fees = Decimal(re.sub(',', '', totalfees))
                    go_id.agreement_payable_net = Decimal(re.sub(',', '', payablenet))
                    go_id.agreement_payable_gross = Decimal(re.sub(',', '', payablegross))

                    go_id.agreement_risk_fee = Decimal(re.sub(',', '', riskfee))

                    # go_id.agreement_bamf_fee = Decimal(re.sub(',', '', bamffee))
                    # go_id.agreement_stage= stage
                    go_id.save()
                    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
                    stage = "3"
                    if agreement_detail.agreement_stage < str(requiredtabs()):
                        go_agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage, agreementclosedflag = '901')
                    unique_id = 1
                    docfee_rec = {'go_id': go_id,
                                  'agreementnumber': go_id,
                                  'transtypeid' : '1',
                                  'transactiondate': agreement_detail.agreementupfrontdate,
                                  'transactionsourceid' : 'GO1',
                                  'transtypedesc' : 'Documentation Fee',
                                  'transflag' : 'Fee',
                                  'transfallendue' : '1',
                                  'transnetpayment': Decimal(re.sub(',', '', docfee)),
                                  'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                  'transpayprointerest': Decimal(re.sub(',', '', docfee)),
                                  'transgrosspayment': round(Decimal(re.sub(',', '', docfee))*Decimal(config.other_sales_tax),2),
                                  'transvatpayment': round(Decimal(re.sub(',', '', docfee))*Decimal(config.sales_tax),2),
                                  'transaction_detail_unique' : unique_id,
                                  }
                    # TODO: GO#110 - Start
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        docfee_rec['transgrosspayment'] = Decimal(re.sub(',', '', docfee))
                        docfee_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                    # TODO: GO#110 - End
                    ats_docfee_rec = {'go_id': go_id,
                                      'agreementnumber': go_id,
                                      'transtypeid': '1',
                                      'transactiondate': agreement_detail.agreementupfrontdate,
                                      'transactionsourceid': 'GO1',
                                      'transtypedesc': '',
                                      'transflag': '',
                                      'transfallendue': '1',
                                      'transnetpayment': Decimal(re.sub(',', '', docfee)),
                                      'transgrosspayment': round(Decimal(re.sub(',', '', docfee))*Decimal(config.other_sales_tax),2),
                                      'transactionsourcedesc' : 'Primary',
                                      'transagreementagreementdate' : agreement_detail.agreementagreementdate,
                                      'transagreementauthority' : agreement_detail.agreementauthority,
                                      'transagreementclosedflag_id': '901',
                                      'transactionstatus':'905',
                                      'transagreementcustomernumber' : agreement_detail.agreementcustomernumber,
                                      # 'transagreementcustomernumber' : agreement_detail.agreementcustomernumber,
                                      'transcustomercompany': agreement_detail.customercompany,
                                      'transagreementddstatus_id' : agreement_detail.agreementddstatus_id,
                                      'transagreementdefname' : 'Lease Agreement',
                                      # 'transcustomercompany': customers.customernumber,
                                      'transddpayment' : '0' ,
                                      # 'transgrosspayment':,
                                      'transnetpaymentcapital': Decimal(re.sub(',', '', '0.00')),
                                      'transnetpaymentinterest': Decimal(re.sub(',', '', docfee)),
                                      'transaction_summary_unique': unique_id,
                                      }

                    # TODO: GO#110 - Start
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        ats_docfee_rec['transagreementdefname'] = 'Hire Purchase'
                        ats_docfee_rec['transgrosspayment'] = Decimal(re.sub(',', '', docfee))
                    # TODO: GO#110 - End

                    go_account_transaction_detail(**docfee_rec).save()
                    go_account_transaction_summary(**ats_docfee_rec).save()

                    if go_id.broker_id == 2 :
                        # unique_id = unique_id +1
                        docfee2_rec = {'go_id': go_id,
                                       'agreementnumber': go_id,
                                       'transtypeid': '4',
                                       'transactiondate': agreement_detail.agreementupfrontdate + timedelta(seconds=1),
                                       'transactionsourceid': 'GO1',
                                       'transtypedesc': 'Documentation Fee 2',
                                       'transflag': 'Fee',
                                       'transfallendue': '1',
                                       'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                                       'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                       'transpayprointerest': Decimal(re.sub(',', '', instalmentnet)),
                                       'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                                       'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                                       'transaction_detail_unique': unique_id,
                                       }
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            docfee2_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                            docfee2_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))


                        ats_docfee2_rec = {'go_id': go_id,
                                          'agreementnumber': go_id,
                                          'transtypeid': '4',
                                          'transactiondate': agreement_detail.agreementupfrontdate + timedelta(seconds=1),
                                          'transactionsourceid': 'GO1',
                                          'transtypedesc': '',
                                          'transflag': '',
                                          'transfallendue': '0',
                                          'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                                          'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet))*Decimal(config.other_sales_tax),2),
                                          'transactionsourcedesc': 'Primary',
                                          'transagreementagreementdate': agreement_detail.agreementagreementdate,
                                          'transagreementauthority': agreement_detail.agreementauthority,
                                          'transagreementclosedflag_id': '901',
                                          'transactionstatus': '905',
                                          'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                                          'transcustomercompany': agreement_detail.customercompany,
                                          'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                                          'transagreementdefname': 'Lease Agreement',
                                          # 'transcustomercompany': customers.customernumber,
                                          'transddpayment': '0',
                                          # 'transgrosspayment':,
                                          'transnetpaymentcapital': Decimal(re.sub(',', '', '0.00')),
                                          'transnetpaymentinterest': Decimal(re.sub(',', '', instalmentnet)),
                                          'transaction_summary_unique': unique_id,
                                          }
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            ats_docfee2_rec['transagreementdefname'] = 'Hire Purchase'
                            ats_docfee2_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))

                        go_account_transaction_detail(**docfee2_rec).save()
                        go_account_transaction_summary(**ats_docfee2_rec).save()

                    Interest = go_id.term* Decimal(re.sub(',', '', instalmentnet)) -  Decimal(re.sub(',', '', principal))

                    multiplier=(go_id.term)*(go_id.term+1)/2
                    multiplier2= Decimal(Interest)/Decimal(multiplier)
                    # TODO : PAF Changes - Start
                    collection_schedule = str(agreement_detail.agreementcollectiontype)

                    for i in range(go_id.agreement_structure_rentals):
                        if collection_schedule != '3':
                            i = i * 3
                    # TODO : PAF Changes - End
                        ats_rentals_rec = {'go_id': go_id,
                                           'agreementnumber': agreement_id,
                                           'transtypeid': '0',
                                           'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                           'transactionsourceid': 'GO1',
                                           'transtypedesc': '',
                                           'transflag': '',
                                           'transfallendue': '0',
                                           'transnetpayment': Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)),
                                           'transgrosspayment': round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)))*Decimal(config.other_sales_tax),2),
                                           'transactionsourcedesc' : 'Primary',
                                           'transagreementagreementdate': agreement_detail.agreementagreementdate,
                                           'transagreementauthority': agreement_detail.agreementauthority,
                                           'transagreementclosedflag_id': '901',
                                           'transactionstatus': '905',
                                           'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                                           'transcustomercompany': agreement_detail.customercompany,
                                           'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                                           'transagreementdefname': 'Lease Agreement',
                                           # 'transcustomercompany': customers.customernumber,
                                           'transddpayment': '1',
                                           # 'transgrosspayment':,
                                           # TODO : PAF Changes - Start
                                           'transnetpaymentinterest': round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', riskfee)),2),
                                           'transnetpaymentcapital': round(Decimal(re.sub(',', '', instalmentnet))-(go_id.agreement_structure_rentals - i) * Decimal(multiplier2),2),
                                           'transaction_summary_unique': unique_id,
                                           # TODO : PAF Changes - End

                                           }
                        # TODO: PAF Changes - Start
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            ats_rentals_rec['transagreementdefname'] = 'Hire Purchase'
                            ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2)
                        if agreement_detail.agreementpaymentmethod == '1':
                            ats_rentals_rec['transagreementdefname'] = 'Hire Purchase'

                        # TODO: PAF Changes - End

                        if go_id.broker_id == 1:
                            if i > 0 and (i+1) % 6 == 0 and go_id.risk_flag == 1 and go_id.bamf_flag == 1:
                                ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                                    re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                # TODO: PAF Changes - Start
                                ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', riskfee)) + Decimal(
                                # TODO: PAF Changes - End
                                    re.sub(',', '', str(config.bamf_fee_amount_net))),2)
                                ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                                    re.sub(',', '', riskfee)))*Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))),2)
                        # TODO: GO#110 - Start
                                if agreement_detail.agreementdefname == 'Hire Purchase':
                                    ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + (Decimal(re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))) * Decimal(config.other_sales_tax), 2)
                        # TODO: GO#110 - End
                        # TODO: PAF Changes - Start
                        if go_id.amf_flag == 1:
                        # TODO: PAF Changes - End
                            if i > 0 and (i+1) % 12 == 0:
                                ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                                    re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                # TODO: PAF Changes - Start
                                ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', riskfee)) + Decimal(
                                # TODO: PAF Changes - End
                                    re.sub(',', '', str(config.bamf_fee_amount_net))),2)
                                ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                                    re.sub(',', '', riskfee)))*Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))),2)
                        # TODO: GO#110 - Start
                                if agreement_detail.agreementdefname == 'Hire Purchase':
                                    ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + (Decimal(re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))), 2)
                        # TODO: GO#110 - End
                        if go_id.risk_flag == 1 and go_id.bamf_flag == 0:
                            ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee))
                            # TODO: PAF Changes - Start
                            ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', riskfee)),2)
                            # TODO: PAF Changes - End
                            ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet))*Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', riskfee))*Decimal(config.other_sales_tax)),2)
                            if agreement_detail.agreementdefname == 'Hire Purchase':
                                ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee))

                        # TODO: PAF Changes - Start
                        if collection_schedule != '3':
                            if i > 0 and (i + 3) % 12 == 0:
                                ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                # TODO: PAF Changes - Start
                                ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))), 2)
                                # TODO: PAF Changes - End
                                ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                                if agreement_detail.agreementdefname == 'Hire Purchase':
                                    ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                        else:
                            if go_id.broker_id == 1:
                                if i > 0 and (i+1) % 6 == 0 and go_id.risk_flag == 0 and go_id.bamf_flag == 1 :
                                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                    # TODO: PAF Changes - Start
                                    ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))),2)
                                    # TODO: PAF Changes - End
                                    ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)))*Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))),2)
                                    if agreement_detail.agreementdefname == 'Hire Purchase':
                                        ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                            else:
                                if i > 0 and (i + 1) % 12 == 0:
                                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                    # TODO: PAF Changes - Start
                                    ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))),2)
                                    # TODO: PAF Changes - End
                                    ats_rentals_rec['transgrosspayment'] = round(
                                        (Decimal(re.sub(',', '', instalmentnet))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                                    if agreement_detail.agreementdefname == 'Hire Purchase':
                                    # TODO: GO#110 - Start
                                        ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2)
                                    # TODO: GO#110 - End
                        if go_id.risk_flag == 0 and go_id.bamf_flag == 0 and go_id.broker_id == 1 and go_id.amf_flag ==0:
                        # TODO: PAF Changes - End
                            ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet))
                            # TODO: PAF Changes - Start
                            ats_rentals_rec['transnetpaymentinterest'] = round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2),2)
                            # TODO: PAF Changes - End
                            ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2)
                            if agreement_detail.agreementdefname == 'Hire Purchase':
                                ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))

                        # TODO: PAF Changes - Start
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            if go_id.agreement_delay_vat_until-1 == i:
                                if go_id.amf_flag == 1:
                                    # Vat_payment = math.floor(go_id.agreement_structure_rentals/12)* Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))*Decimal(re.sub(',', '', str(config.sales_tax)))
                                    Vat_payment = round(agreement_detail.agreementcharges * Decimal(config.sales_tax), 2)
                                    # ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) + Vat_payment + round(Decimal(re.sub(',', '', docfee))*Decimal(config.sales_tax),2)
                                    # ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) + Vat_payment + round(Decimal(re.sub(',', '', docfee))*Decimal(config.sales_tax),2)
                                    ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) + Vat_payment

                        go_account_transaction_summary(**ats_rentals_rec).save()

                        atd_rentals_rec = {'go_id': go_id,
                                           'agreementnumber': agreement_id,
                                           # 'transtypeid': '1',
                                           'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                           'transactionsourceid': 'GO1',
                                           # 'transtypedesc': 'Documentation Fee',
                                           'transflag': 'Pay',
                                           'transfallendue': '0',
                                           'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                                           # TODO: PAF Changes - Start
                                           'transpayproprincipal': round(Decimal(re.sub(',', '', instalmentnet)) - (go_id.agreement_structure_rentals - i) * Decimal(multiplier2), 2),
                                           'transpayprointerest': round((go_id.agreement_structure_rentals - i) * Decimal(multiplier2),2),
                                           # TODO: PAF Changes - End
                                           'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                                           'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                                           'transaction_detail_unique': unique_id,
                                           }
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            atd_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                            atd_rentals_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))


                        go_account_transaction_detail(**atd_rentals_rec).save()

                        atd_risk_rec = {'go_id': go_id,
                                        'agreementnumber': agreement_id,
                                        'transtypeid': '3',
                                        'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                        'transactionsourceid': 'GO1',
                                        'transtypedesc': 'Risk Fee',
                                        'transflag': 'Fee',
                                        'transfallendue': '0',
                                        'transnetpayment': Decimal(re.sub(',', '', riskfee)),
                                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                        'transpayprointerest': Decimal(re.sub(',', '', riskfee)),
                                        'transgrosspayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2),
                                        'transvatpayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.sales_tax), 2),
                                        'transaction_detail_unique': unique_id,
                                        }
                        # TODO: GO#110 - Start
                        # if agreement_detail.agreementdefname == 'Hire Purchase':
                        #     atd_risk_rec['transgrosspayment'] = Decimal(re.sub(',', '', riskfee))
                        #     atd_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                        # TODO: GO#110 - End
                        unique_id = unique_id + 1
                        if go_id.risk_flag == 1:
                            if go_id.broker_id == 1:
                                go_account_transaction_detail(**atd_risk_rec).save()

                    # TODO: PAF Changes - Start
                    if go_id.agreement_structure_upfront > 0:
                        upfront_rentals = go_id.agreement_structure_upfront * Decimal(
                            re.sub(',', '', instalmentnet))
                        atd_upfront_rental_rec = {'go_id': go_id,
                                                  'agreementnumber': go_id,
                                                  'transtypeid': '1',
                                                  'transactiondate': agreement_detail.agreementupfrontdate,
                                                  'transactionsourceid': 'GO1',
                                                  'transtypedesc': 'Upfront Rental',
                                                  'transflag': 'Pay',
                                                  'transfallendue': '1',
                                                  'transnetpayment': upfront_rentals,
                                                  'transpayproprincipal': upfront_rentals,
                                                  'transpayprointerest': Decimal(re.sub(',', '', '0.00')),
                                                  'transgrosspayment': round(upfront_rentals*Decimal(config.other_sales_tax), 2),
                                                  'transvatpayment': round(upfront_rentals*Decimal(config.sales_tax), 2),
                                                  'transaction_detail_unique': 1,
                                                  }

                        ats_upfront_rental_rec = {'go_id': go_id,
                                                  'agreementnumber': go_id,
                                                  'transtypeid': '1',
                                                  'transactiondate': agreement_detail.agreementupfrontdate,
                                                  'transactionsourceid': 'GO1',
                                                  'transtypedesc': '',
                                                  'transflag': '',
                                                  'transfallendue': '1',
                                                  'transnetpayment': upfront_rentals,
                                                  'transgrosspayment': round(upfront_rentals * Decimal(config.other_sales_tax), 2),
                                                  'transactionsourcedesc': 'Primary',
                                                  'transagreementagreementdate': agreement_detail.agreementagreementdate,
                                                  'transagreementauthority': agreement_detail.agreementauthority,
                                                  'transagreementclosedflag_id': '901',
                                                  'transactionstatus': '905',
                                                  'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                                                  # 'transagreementcustomernumber' : agreement_detail.agreementcustomernumber,
                                                  'transcustomercompany': agreement_detail.customercompany,
                                                  'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                                                  'transagreementdefname': 'Lease Agreement',
                                                  # 'transcustomercompany': customers.customernumber,
                                                  'transddpayment': '0',
                                                  # 'transgrosspayment':,
                                                  'transnetpaymentcapital': upfront_rentals,
                                                  'transnetpaymentinterest': Decimal(re.sub(',', '', '0.00')),
                                                  'transaction_summary_unique': 1,
                                                  }
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            atd_upfront_rental_rec['transgrosspayment'] = upfront_rentals
                            atd_upfront_rental_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                            ats_upfront_rental_rec['transagreementdefname'] = 'Hire Purchase'
                            ats_upfront_rental_rec['transgrosspayment'] = upfront_rentals

                        go_account_transaction_summary(**ats_upfront_rental_rec).save()
                        go_account_transaction_detail(**atd_upfront_rental_rec).save()
                    # TODO: PAF Changes - End
                    # TODO: PAF Changes - Start
                    if go_id.broker_id == 2:
                        unique_wip = 2
                    else:
                        unique_wip = 1
                    for i in range(go_id.agreement_structure_rentals):
                        if collection_schedule != '3':
                            i = i * 3
                        if i > 0 and (i + 3) % 12 == 0:
                            if go_id.bamf_flag == 1:
                                agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i)
                                atd_BAMF_rec = {'go_id': go_id,
                                                'agreementnumber': agreement_id,
                                                'transtypeid': '2',
                                                'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(
                                                    months=+i),
                                                'transactionsourceid': 'GO1',
                                                'transtypedesc': 'Annual Management Fee',
                                                'transflag': 'Fee',
                                                'transfallendue': '0',
                                                'transnetpayment': str(config.bamf_fee_amount_net),
                                                'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                'transpayprointerest': str(config.bamf_fee_amount_net),
                                                'transaction_detail_unique': i+unique_wip,
                                                }
                                print(agreement_detail.agreementfirstpaymentdate + relativedelta(
                                    months=+i))
                                go_account_transaction_detail(**atd_BAMF_rec).save()
                        else:
                            if go_id.bamf_flag == 1:
                                if i > 0 and (i+1) % 6 == 0:
                                    atd_BAMF_rec = {'go_id': go_id,
                                                    'agreementnumber': agreement_id,
                                                    'transtypeid': '5',
                                                    'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                                    'transactionsourceid': 'GO1',
                                                    'transtypedesc': 'Bi-Annual Management Fee',
                                                    'transflag': 'Fee',
                                                    'transfallendue': '0',
                                                    'transnetpayment' : str(config.bamf_fee_amount_net),
                                                    'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                    'transpayprointerest': str(config.bamf_fee_amount_net),
                                                    'transgrosspayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2),
                                                    'transvatpayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.sales_tax), 2),
                                                    'transaction_detail_unique': i+unique_wip,
                                                    }
                                    # TODO: GO#110 - Start
                                    if agreement_detail.agreementdefname == 'Hire Purchase':
                                        atd_BAMF_rec['transgrosspayment'] = Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                                        atd_BAMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                                    # TODO: GO#110 - End
                                    if go_id.bamf_flag == 1:
                                        go_account_transaction_detail(**atd_BAMF_rec).save()
                            if go_id.amf_flag == 1:
                                if go_id.amf_flag == 1:
                                    if i > 0 and (i + 1) % 12 == 0:
                                        atd_AMF_rec = {'go_id': go_id,
                                                        'agreementnumber': agreement_id,
                                                        'transtypeid': '2',
                                                        'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                                        'transactionsourceid': 'GO1',
                                                        'transtypedesc': 'Annual Management Fee',
                                                        'transflag': 'Fee',
                                                        'transfallendue': '0',
                                                        'transnetpayment': str(config.bamf_fee_amount_net),
                                                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                        'transpayprointerest': str(config.bamf_fee_amount_net),
                                                        'transgrosspayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2),
                                                        'transvatpayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.sales_tax), 2),
                                                        'transaction_detail_unique': i+unique_wip,
                                                        }
                                        if agreement_detail.agreementdefname == 'Hire Purchase':
                                            atd_AMF_rec['transgrosspayment'] = Decimal( re.sub(',', '', str(config.bamf_fee_amount_net)))
                                            atd_AMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                                        go_account_transaction_detail(**atd_AMF_rec).save()
                                        # TODO: PAF Changes - End

                    for i in range(3):
                        # TODO: PAF Changes - Start
                        if collection_schedule != '3':
                            i = i * 3
                        # TODO: PAF Changes - End
                        ats_secondary_rec = {'go_id': go_id,
                                             'agreementnumber': agreement_id,
                                             'transtypeid': '0',
                                             'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                             'transactionsourceid': 'GO3',
                                             'transtypedesc': '',
                                             'transflag': '',
                                             'transfallendue': '0',
                                             'transnetpayment': Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)),
                                             'transgrosspayment': round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)))*Decimal(config.other_sales_tax),2),
                                             'transactionsourcedesc': 'Secondary',
                                             'transagreementagreementdate': agreement_detail.agreementagreementdate ,
                                             'transagreementauthority': agreement_detail.agreementauthority,
                                             'transagreementclosedflag_id': '901',
                                             'transactionstatus': '905',
                                             'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                                             'transcustomercompany': agreement_detail.customercompany,
                                             'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                                             'transagreementdefname': 'Lease Agreement',
                                             # 'transcustomercompany': customers.customernumber,
                                             'transddpayment': '1',
                                             # 'transgrosspayment':,
                                             'transnetpaymentcapital' : Decimal(re.sub(',', '', '0.00')),
                                             'transnetpaymentinterest' : round(Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)),2),
                                             'transaction_summary_unique': unique_id,
                                             }
                        if agreement_detail.agreement_stage == 4:
                            go_account_transaction_summary.objects.filter(agreementnumber=agreement_id, transactionstatus='905').update(transactionstatus='901')

                        if go_id.secondary_flag == 1:
                            ats_secondary_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee))
                            # TODO: GO#110 - Start
                            if agreement_detail.agreementdefname == 'Hire Purchase':
                                ats_secondary_rec['transagreementdefname'] = 'Hire Purchase'
                                ats_secondary_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2)
                            # TODO: GO#110 - End
                            go_account_transaction_summary(**ats_secondary_rec).save()
                            atd_secondary_rentals_rec = {'go_id': go_id,
                                                         'agreementnumber': agreement_id,
                                                         # 'transtypeid': '0',
                                                         'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                                         'transactionsourceid': 'GO3',
                                                         # 'transtypedesc': 'Documentation Fee',
                                                         'transflag': 'Sec',
                                                         'transfallendue': '0',
                                                         'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                                                         'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                         'transpayprointerest': Decimal(re.sub(',', '', instalmentnet)),
                                                         'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                                                         'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                                                         'transaction_detail_unique': unique_id,
                                                         }
                            if agreement_detail.agreementdefname == 'Hire Purchase':
                                atd_secondary_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                                atd_secondary_rentals_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                            go_account_transaction_detail(**atd_secondary_rentals_rec).save()

                            atd_secondary_risk_rec = {'go_id': go_id,
                                                      'agreementnumber': agreement_id,
                                                      'transtypeid': '3',
                                                      'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                                      'transactionsourceid': 'GO3',
                                                      'transtypedesc': 'Risk Fee',
                                                      'transflag': 'SFn',
                                                      'transfallendue': '0',
                                                      'transnetpayment': Decimal(re.sub(',', '', riskfee)),
                                                      'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                      'transpayprointerest': Decimal(re.sub(',', '', riskfee)),
                                                      'transgrosspayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2),
                                                      'transvatpayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.sales_tax), 2),
                                                      'transaction_detail_unique': unique_id,
                                                      }
                        # TODO: GO  # 110 - Start
                            # if agreement_detail.agreementdefname == 'Hire Purchase':
                            #     atd_secondary_risk_rec['transgrosspayment'] = Decimal(re.sub(',', '', riskfee))
                            #     atd_secondary_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                            if go_id.risk_flag == 1:
                                go_account_transaction_detail(**atd_secondary_risk_rec).save()
                        # if go_id.broker_id == 2:
                        # go_account_transaction_detail(**atd_secondary_rentals_rec).save()
                        unique_id = unique_id + 1
                        # TODO: GO#110 - End

                    # TODO : PAF Changes - Start
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        # Vat_payment = math.floor(go_id.agreement_structure_rentals / 12) * Decimal(
                        #     re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(
                        #     re.sub(',', '', str(config.sales_tax)))
                        # Vat_payment = Vat_payment + round(Decimal(re.sub(',', '', docfee))*Decimal(config.sales_tax),2)
                        if agreement_detail.agreementcharges:
                            Vat_payment = round(agreement_detail.agreementcharges * Decimal(config.sales_tax), 2)

                            atd_deferred_vat_rec = {'go_id': go_id,
                                                    'agreementnumber': agreement_id,
                                                    'transtypeid': '3',
                                                    'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(
                                                        months=+(go_id.agreement_delay_vat_until - 1)),
                                                    'transactionsourceid': 'GO1',
                                                    'transtypedesc': 'Deferred VAT',
                                                    'transflag': 'Fee',
                                                    'transfallendue': '0',
                                                    'transnetpayment': Decimal(re.sub(',', '', '0.00')),
                                                    'transgrosspayment': Vat_payment,
                                                    'transvatpayment': Vat_payment,
                                                    # 'transnetpayment': Decimal(re.sub(',', '', VATvalue)),
                                                    # TODO: calculate principal and interest for VAT
                                                    'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                                    'transpayprointerest': Decimal(re.sub(',', '', '0.00')),
                                                    'transaction_detail_unique': go_id.agreement_delay_vat_until,
                                                    }

                            go_account_transaction_detail(**atd_deferred_vat_rec).save()

                    # grouping = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id)
                    # transaction_ids = []
                    # for a in grouping:
                    #     l = a.transaction_detail_unique
                    #     transaction_ids.append(l)
                    # # TODO : PAF Changes - End
                    # print(transaction_ids)
                    # duplicates = list({x for x in transaction_ids if transaction_ids.count(x)>1})
                    # print(duplicates)

                    grouping = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id, transaction_summary_unique='1')
                    grouping_wip_net = (grouping.aggregate(Sum('transnetpayment')))
                    grouping_wip_gross = (grouping.aggregate(Sum('transgrosspayment')))
                    grouping_wip_interest = (grouping.aggregate(Sum('transnetpaymentinterest')))
                    grouping_wip_capital = (grouping.aggregate(Sum('transnetpaymentcapital')))
                    group_net = grouping_wip_net["transnetpayment__sum"]
                    group_gross = grouping_wip_gross["transgrosspayment__sum"]
                    group_interest = grouping_wip_interest["transnetpaymentinterest__sum"]
                    group_capital = grouping_wip_capital["transnetpaymentcapital__sum"]

                    ats_grouped = {'go_id': go_id,
                                   'agreementnumber': go_id,
                                   'transtypeid': '1',
                                   'transactiondate': agreement_detail.agreementupfrontdate,
                                   'transactionsourceid': 'GO1',
                                   'transtypedesc': '',
                                   'transflag': '',
                                   'transfallendue': '1',
                                   'transnetpayment': group_net,
                                   'transgrosspayment': group_gross,
                                   'transactionsourcedesc' : 'Primary',
                                   'transagreementagreementdate' : agreement_detail.agreementagreementdate,
                                   'transagreementauthority' : agreement_detail.agreementauthority,
                                   'transagreementclosedflag_id': '901',
                                   'transactionstatus':'905',
                                   'transagreementcustomernumber' : agreement_detail.agreementcustomernumber,
                                   'transcustomercompany': agreement_detail.customercompany,
                                   'transagreementddstatus_id' : agreement_detail.agreementddstatus_id,
                                   'transagreementdefname' : 'Lease Agreement',
                                   'transddpayment' : '0' ,
                                   'transnetpaymentcapital': group_capital,
                                   'transnetpaymentinterest': group_interest,
                                   'transaction_summary_unique': 1,
                                   }

                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        ats_grouped['transagreementdefname'] = 'Hire Purchase'
                    grouping.delete()
                    go_account_transaction_summary(**ats_grouped).save()

                    return redirect('core_agreement_crud:agreement_management_tab4', agreement_id)

        except Exception as e:
            error = '{} {}'.format(e, traceback.format_exc())

    context['error'] = error
    context['errors'] = errors
    context['values'] = values
    context['go_id'] = go_id
    context['datacash_request'] = request.GET.get('datacash_request')

    return render(request, template, context)


@login_required(login_url='signin')
def agreement_management_tab4(request, agreement_id):

    stage = "4"
    errors = {}
    # context = {'agreement_id': agreement_id}
    template = 'core_agreement_crud/agreement_management_tab4.html'

    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    context['agreement_detail'] = agreement_detail

    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    config = client_configuration.objects.get(client_id="NWCF")
    context['agreement_customer'] = agreement_customer

    context['username'] = request.user.username

    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id) \
        .order_by('transtypedesc', )
    context['account_detail'] = account_detail
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id).order_by('transactiondate', 'transactionsourceid')
    context['account_summary'] = account_summary
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid='GO1',
                                                                              transtypeid__isnull=False) \
        .order_by('transtypedesc', )
    context['account_detail_fees'] = account_detail_fees

    try:
        transaction_summary_extract = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                                    transactionbatch_id__contains='GO')
        context['transaction_summary_extract_count'] = transaction_summary_extract.count()
        transition = transition_log.objects.filter(agreementnumber=agreement_id)
        context['transition_count'] = transition.count()

    except:
        error = None

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = config.other_sales_tax
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
    if agreement_detail.agreementinstalmentvat is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    # Sundry Items
    settlement_figure_queryset = account_summary.aggregate(Sum('transgrosspayment'))
    settlement_figure_vat  = settlement_figure_queryset['transgrosspayment__sum']

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure_net = settlement_figure_queryset['transnetpayment__sum']

    # if agreement_type == 'Lease':
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    # else:
    #     settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

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
        secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
    except:
        secondary_count = 0

    row_index = 0
    for row in account_summary:
        if row.transactionsourceid in ['GO1', 'GO2', 'GO3', 'SP1', 'SP2', 'SP3']:
            if row.transactiondate >= agreement_detail.agreementfirstpaymentdate:
                row_index += 1
        row.row_index = row_index

    # Add Gross of Vat to account detail queryset
    for row in account_detail:
        row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

    if request.method == 'POST':
        try:
            _process = True
            _redirect = True

            if request.POST.get('reopen') == 'true':
                reopen_function(request, agreement_id)
                _process = False

            # If we are consolidating, check than none of the
            # consolidating agreements are already in a batch.
            if (go_id.consolidation_info) and ("::" in go_id.consolidation_info):
                consol_agreements_in_batch = []
                consol_agreements = go_id.consolidation_info.split("::")
                for aid in consol_agreements:
                    dd_filter = DrawDown.objects.filter(status='OPEN', agreement_id=aid)
                    if dd_filter.exists():
                        _process = False
                        _redirect = False
                        for row in dd_filter:
                            consol_agreements_in_batch.append({'batch_header': row.batch_header.reference,
                                                               'due_date': row.due_date.strftime("%d/%m/%Y"),
                                                               'user': row.user.username, 'agreement_id': aid})
                if len(consol_agreements_in_batch):
                    context['console_batch_conflicts'] = consol_agreements_in_batch

            if _process:
                go_agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage, agreementclosedflag='901')
                go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                              transactionstatus='905').update(transactionstatus='901')
                # TODO : PAF Changes - Start
                if agreement_detail.agreementpaymentmethod != 1:
                    go_account_transaction_summary.objects.filter(agreementnumber=agreement_id).update(transactionpaymentmethod='0', transddpayment='0')
                    go_account_transaction_detail.objects.filter(agreementnumber=agreement_id).update(transactionpaymentmethod='0')
                else:
                    go_account_transaction_summary.objects.filter(agreementnumber=agreement_id).update(transactionpaymentmethod='1')
                    go_account_transaction_detail.objects.filter(agreementnumber=agreement_id).update(transactionpaymentmethod='1')
                # TODO : PAF Changes - End

                if (go_id.consolidation_info) and ("::" in go_id.consolidation_info):
                    for agreement in go_id.consolidation_info.split('::'):
                        go_agreement_index.objects.filter(agreement_id=agreement).update(consolidation_info='Consolidated into ' + str(go_id.agreement_id) + ' on ' + datetime.datetime.today().strftime('%Y-%m-%d'))
                        consolidation_function(request, agreement)

                    go_agreement_index.objects.filter(agreement_id=go_id).update(
                        consolidation_info='Consolidated from ' + go_id.consolidation_info.replace('::',',') + ' on ' + (datetime.datetime.today().strftime('%Y-%m-%d')))

                app_process_non_dd_arrears(agreement_id)

                return redirect("core_agreement_crud:AgreementEnquiryList")

            if _redirect:
                url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
                return redirect(url + '?change_profile=1')

        except Exception as e:
            context['error'] = e

    context['errors'] = errors
    context['values'] = request.POST

    context.update({
        'change_profile': request.GET.get('change_profile'),
        'batch_error': request.GET.get('batch_error'),
        'agreement_payable_net': agreement_payable_net,
        'agreement_payable_gross': agreement_payable_gross,
        'agreement_instalment_gross': agreement_instalment_gross,
        'agreement_fees_net': agreement_fees_net,
        # 'bacs_audit': bacs_audit,
        'account_detail': account_detail,
        'account_summary': account_summary,
        'settlement_figure_net': settlement_figure_net,
        'settlement_figure_vat': settlement_figure_vat,
        'agreement_type': agreement_type,
        'doc_fee_count': doc_fee_count,
        'primary_count': primary_count,
        'secondary_count': secondary_count,
        'go_id' : go_id,
        'show_sentinel_button': True,
        'today': datetime.datetime.now().strftime("%Y-%m-%d")
        # ,'agreement_regulated_flag': agreement_regulated_flag}
    })

    if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
        context['show_sentinel_button'] = False
        context['is_in_batch'] = True

    if arrears_summary_agreement_level.objects.filter(arr_agreement_id=agreement_id).exists():
        arrears_detail = arrears_summary_agreement_level.objects.get(arr_agreement_id=agreement_id)
        if arrears_detail.arr_balance_value_grossofvat >= 0:
            context['in_arrears'] = True
        else:
            context['in_arrears'] = False
    # Card 68 Settlement Work Package #
    if go_agreements.objects.filter(agreementnumber=agreement_id):
        sentinel_arrears_check = go_agreements.objects.get(agreementnumber=agreement_id)
        if sentinel_arrears_check.agreementresidualvat == 0.00:
            arrears_check = sentinel_arrears_check.agreementtotalarrearsnet + sentinel_arrears_check.agreementtotalarrearsnetfee + sentinel_arrears_check.agreementarrearsvat
            if arrears_check > 0:
                context['in_arrears'] = True
            else:
                context['in_arrears'] = False

    # Card 68 Settlement Work Package #
    return render(request, template, context)


@login_required(login_url='signin')
def agreement_management_tab5(request, agreement_id):

    stage = "5"
    errors = {}
    context = {'agreement_id': agreement_id}
    template = 'core_agreement_crud/agreement_management_tab5.html'

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    context['agreement_detail'] = agreement_detail

    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    config = client_configuration.objects.get(client_id="NWCF")
    context['agreement_customer'] = agreement_customer

    context['username'] = request.user.username

    account_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id) \
        .order_by('transtypedesc', )
    context['account_detail'] = account_detail
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    context['account_summary'] = account_summary
    account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid='GO1',
                                                                              transtypeid__isnull=False) \
        .order_by('transtypedesc', )
    context['account_detail_fees'] = account_detail_fees

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = config.other_sales_tax
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
    if agreement_detail.agreementinstalmentvat is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentvat
    if agreement_detail.agreementinstalmentins is not None:
        agreement_instalment_gross += agreement_detail.agreementinstalmentins

    # Sundry Items
    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    if settlement_figure is None: settlement_figure_vat = 0
    else:
        if agreement_type == 'Lease':
            settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
        else:
            settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    first_rental_date = agreement_detail.agreementfirstpaymentdate

    # get Number of Document Fees
    try:
        doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid='GO1',
                                                                            transactiondate__lt=first_rental_date) \
            .count()
    except:
        doc_fee_count = 0

    # get Number of Primaries
    try:
        primary_count = go_agreement_index.term

    except:
        primary_count = 0

    # get Number of Secondaries
    try:
        secondary_count = account_summary.filter(transactionsourceid__in=['GO2', 'GO3']).count()
    except:
        secondary_count = 0

    # Add Gross of Vat to account summary queryset
    row_index = 0
    for row in account_summary:
        # if row.transactionsourceid in ['GO8','GO9', 'SP9'] and row.transvatpayment is not None:
        if row.transactionsourceid in ['GO8', 'GO9', 'SP9']:
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

    if request.method == 'POST':
        try:

            request.method = 'GET'
            return agreement_management_tab5(request, agreement_id)

        except Exception as e:
            context['error'] = e

    context['errors'] = errors
    context['values'] = request.POST
    go_agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage)

    context.update({
        'agreement_payable_net': agreement_payable_net,
        'agreement_payable_gross': agreement_payable_gross,
        'agreement_instalment_gross': agreement_instalment_gross,
        'agreement_fees_net': agreement_fees_net,
        # 'bacs_audit': bacs_audit,
        'account_detail': account_detail,
        'account_summary': account_summary,
        'settlement_figure': settlement_figure,
        'settlement_figure_vat': settlement_figure_vat,
        'agreement_type': agreement_type,
        'doc_fee_count': doc_fee_count,
        'primary_count': primary_count,
        'secondary_count': secondary_count
        # ,'agreement_regulated_flag': agreement_regulated_flag}
    })

    return render(request, template, context)


@login_required(login_url='signin')
def archive_agreement(request, agreement_id):
    if request.method == 'POST':
        archive_agreement_function(request, agreement_id)
        cancel_ddi_with_datacash(agreement_id, user=request.user)
        # print('test')

    return redirect('core_agreement_crud:AgreementEnquiryList')


@login_required(login_url='signin')
def unarchive_agreement(request, agreement_id):
    if request.method == 'POST':
        unarchive_agreement_function(request, agreement_id)
        # cancel_ddi_with_datacash(agreement_id, user=None)

    return redirect('core_agreement_crud:AgreementEnquiryList')


@login_required(login_url='signin')
def refund(request, agreement_id):

    if request.method == 'POST':
        refund_function(request, agreement_id)

    return redirect('core_agreement_crud:agreement_management_tab4', agreement_id)

# TODO: PAF Changes - Start

@login_required(login_url='signin')
def go_agreement_button_selector(request):

    data = {
            # "token": request.POST['token'],
            "agreement_type": request.POST['agreement_type'],
            "funder_info": request.POST['funder_info'],
            "broker_info": request.POST['broker_info'],
            }

    context = {}

    Broker_Info = data['broker_info']
    print('Check')

    Funder_Info = data['funder_info']

    Agreement_Type_Info = data['agreement_type']

    print(Agreement_Type_Info)
    print(Funder_Info)
    print(Broker_Info)

    Agreement_Type_Info = 1
    Funder_Info = 1
    Broker_Info = 0

    print('1425')
    customer = 'PAF'

    Risk_Fee_Info = go_selectable_functionality.objects.get(customer=customer, function='Risk Fee', agreement_type=Agreement_Type_Info, funder=Funder_Info, broker=Broker_Info)
    Bamf_Fee_Info = go_selectable_functionality.objects.get(customer=customer, function='Bamf Fee', agreement_type=Agreement_Type_Info,
                                                               funder=Funder_Info, broker=Broker_Info)
    Secondaries_Info = go_selectable_functionality.objects.get(customer=customer, function='Secondaries', agreement_type=Agreement_Type_Info,
                                                                  funder=Funder_Info, broker=Broker_Info)
    Title_Info = go_selectable_functionality.objects.get(customer=customer, function='Title', agreement_type=Agreement_Type_Info,
                                                            funder=Funder_Info, broker=Broker_Info)
    Security_Info = go_selectable_functionality.objects.get(customer=customer, function='Security', agreement_type=Agreement_Type_Info,
                                                               funder=Funder_Info, broker=Broker_Info)
    Amf_Fee_Info = go_selectable_functionality.objects.get(customer=customer, function='Amf Fee', agreement_type=Agreement_Type_Info,
                                                              funder=Funder_Info, broker=Broker_Info)
    Doc_Fee_Info = go_selectable_functionality.objects.get(customer=customer, function='Doc Fee', agreement_type=Agreement_Type_Info,
                                                              funder=Funder_Info, broker=Broker_Info)

    Risk_Fee_Selectable = Risk_Fee_Info.selectable
    Bamf_Fee_Selectable = Bamf_Fee_Info.selectable
    Secondaries_Selectable = Secondaries_Info.selectable
    Title_Selectable = Title_Info.selectable
    Security_Selectable = Security_Info.selectable
    Amf_Fee_Selectable = Amf_Fee_Info.selectable
    Doc_Fee_Selectable = Doc_Fee_Info.selectable

    Risk_Fee_Visible = Risk_Fee_Info.visible
    Bamf_Fee_Visible = Bamf_Fee_Info.visible
    Secondaries_Visible = Secondaries_Info.visible
    Title_Visible = Title_Info.visible
    Security_Visible = Security_Info.visible
    Amf_Fee_Visible = Amf_Fee_Info.visible
    Doc_Fee_Visible = Doc_Fee_Info.visible


    return JsonResponse({"success": True,
                         "Risk_Fee_Selectable": Risk_Fee_Selectable,
                         "Bamf_Fee_Selectable" : Bamf_Fee_Selectable,
                         "Secondaries_Selectable" : Secondaries_Selectable,
                         "Title_Selectable" : Title_Selectable,
                         "Security_Selectable" : Security_Selectable,
                         "Amf_Fee_Selectable" : Amf_Fee_Selectable,
                         "Doc_Fee_Selectable" : Doc_Fee_Selectable,
                         "Risk_Fee_Visible" : Risk_Fee_Visible,
                         "Bamf_Fee_Visible" : Bamf_Fee_Visible,
                         "Secondaries_Visible" : Secondaries_Visible,
                         "Title_Visible" : Title_Visible,
                         "Security_Visible" : Security_Visible,
                         "Amf_Fee_Visible" : Amf_Fee_Visible,
                         "Doc_Fee_Visible" : Doc_Fee_Visible
                         })

# TODO: PAF Changes - End





