# Django Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Max
from django.core.exceptions import ObjectDoesNotExist

import datetime

# Models
from django.contrib.auth.models import User

from .models import arrears_summary_agreement_level, \
                    arrears_summary_arrear_level, \
                    arrears_detail_arrear_level, \
                    receipt_allocations_by_agreement, \
                    receipt_allocations_by_arrears, \
                    receipt_allocations_by_detail, \
                    arrears_allocation_type, \
                    arrears_status

from core_payments.models import receipt_record

from core_agreement_crud.models import go_agreement_querydetail, \
                                go_customers, \
                                go_account_transaction_summary

from core.models import ncf_regulated_agreements, ncf_collection_agents
from core.functions_shared import write_account_history

# Filters
from core_dashboard.filters import go_agreement_querydetail_Filter

from .filters import arrears_summary_agreement_level_Filter,\
                        arrears_summary_arrear_level_Filter

# TODO - Only for Development - Remove for Production
from .functions_shared import app_process_bacs_udd_arrears

# Arrears processing
# -------------------------
@login_required(login_url="signin")
def arrears_by_agreement_view(request):

    # retrieve query filters
    query = {}
    for k in ('arr_agreement_id__contains', 'arr_customercompanyname__contains'):
        if request.GET.get(k):
            query[k] = request.GET[k]

    # apply Arrears Status Filter
    if not query:
        arrears_by_agreement_extract = arrears_summary_agreement_level.objects.all()
    else:
        arrears_by_agreement_extract = arrears_summary_agreement_level.objects.filter(**query)

    # Apply Current Arrears Filter
    if arrears_by_agreement_extract:
        if not request.GET.get('current_arrears'):
            arrears_by_agreement_extract_1 = arrears_by_agreement_extract.exclude(arr_balance_value_grossofvat__lte=0)
        else:
            if request.GET.get('current_arrears') == '1':
                arrears_by_agreement_extract_1 = arrears_by_agreement_extract.exclude(arr_balance_value_grossofvat__gt=0)
            else:
                arrears_by_agreement_extract_1 = arrears_by_agreement_extract
    else:
        arrears_by_agreement_extract_1 = arrears_by_agreement_extract

    # apply Unallocated Receipts Filter
    if arrears_by_agreement_extract_1:
        if request.GET.get('unallocated_recpts') == '1':
            arrears_by_agreement_extract_2 = arrears_by_agreement_extract_1.exclude(arr_unallocated_value_grossofvat__lte=0)
        else:
            if request.GET.get('unallocated_recpts') == '2':
                arrears_by_agreement_extract_2 = arrears_by_agreement_extract_1.exclude(arr_unallocated_value_grossofvat__gt=0)
            else:
                arrears_by_agreement_extract_2 = arrears_by_agreement_extract_1
    else:
        arrears_by_agreement_extract_2 = arrears_by_agreement_extract_1

    arrears_by_agreement_list = arrears_by_agreement_extract_2

    # Calculate Summary Totals
    arrears_to_date_percent = 100
    arrears_to_date_total_sum = arrears_by_agreement_list.aggregate(Sum('arr_arrears_value_grossofvat'))
    if not arrears_to_date_total_sum["arr_arrears_value_grossofvat__sum"]:
        arrears_to_date_total_sum["arr_arrears_value_grossofvat__sum"] = 0
        arrears_to_date_percent = 0
    arrears_to_date_total = arrears_to_date_total_sum["arr_arrears_value_grossofvat__sum"]

    collected_adjusted_to_date_percent = 0
    collected_to_date_total_sum = arrears_by_agreement_list.aggregate(Sum('arr_collected_value_grossofvat'))
    if not collected_to_date_total_sum["arr_collected_value_grossofvat__sum"]:
        collected_to_date_total_sum["arr_collected_value_grossofvat__sum"] = 0
    collected_to_date_total = collected_to_date_total_sum["arr_collected_value_grossofvat__sum"]

    adjusted_to_date_total_sum = arrears_by_agreement_list.aggregate(Sum('arr_writtenoff_value_grossofvat'))
    if not adjusted_to_date_total_sum["arr_writtenoff_value_grossofvat__sum"]:
        adjusted_to_date_total_sum["arr_writtenoff_value_grossofvat__sum"] = 0
    adjusted_to_date_total = adjusted_to_date_total_sum["arr_writtenoff_value_grossofvat__sum"]

    collected_adjusted_to_date_total = collected_to_date_total + adjusted_to_date_total
    if arrears_to_date_total != 0:
        collected_adjusted_to_date_percent = (collected_adjusted_to_date_total/arrears_to_date_total) * 100
    else:
        collected_adjusted_to_date_percent = 0

    current_arrear_percent = 0
    current_arrear_total_sum = arrears_by_agreement_list.aggregate(Sum('arr_balance_value_grossofvat'))
    if not current_arrear_total_sum["arr_balance_value_grossofvat__sum"]:
        current_arrear_total_sum["arr_balance_value_grossofvat__sum"] = 0
        current_arrear_percent = 0
    current_arrear_total = current_arrear_total_sum["arr_balance_value_grossofvat__sum"]

    if arrears_to_date_total != 0:
        current_arrear_percent = (current_arrear_total/arrears_to_date_total) * 100
    else:
        current_arrear_percent = 0

    unallocated_receipts_percent = 0
    unallocated_receipts_sum = arrears_by_agreement_list.aggregate(Sum('arr_unallocated_value_grossofvat'))
    if not unallocated_receipts_sum["arr_unallocated_value_grossofvat__sum"]:
        unallocated_receipts_sum["arr_unallocated_value_grossofvat__sum"] = 0
        unallocated_receipts_percent = 0
    unallocated_receipts_total = unallocated_receipts_sum["arr_unallocated_value_grossofvat__sum"]

    if arrears_to_date_total != 0:
        unallocated_receipts_percent = (unallocated_receipts_total / arrears_to_date_total) * 100
    else:
        unallocated_receipts_percent = 0

    has_filter = False
    if query or request.GET.get('current_arrears') or request.GET.get('unallocated_recpts'):
        has_filter = True

    # Pagination
    paginator = Paginator(arrears_by_agreement_list, 9)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    # Process Server Messages from Django Session
    server_messages = {}
    request.session['arrears_by_agreement_messages'] = {}

    # Save Url Query String to Django Session
    wip_querystring = None
    request.session['arrears_by_arrears_return_querystring'] = {}
    request.session['arrears_by_arrears_return_querystring'] = request.get_full_path()

    return render(request, 'core_arrears/arrears_by_agreement_list.html',
                                    {'arrears_list':arrears_by_agreement_list,
                                     'arrears_list_qs': pub,
                                     'filter': query,
                                     'has_filter': has_filter,
                                     'current_arrears_filter': request.GET.get('current_arrears'),
                                     'unallocated_recpts_filter': request.GET.get('unallocated_recpts'),
                                     'arrears_to_date_total': arrears_to_date_total,
                                     'arrears_to_date_percent': arrears_to_date_percent,
                                     'collected_adjusted_to_date_total': collected_adjusted_to_date_total,
                                     'collected_adjusted_to_date_percent': collected_adjusted_to_date_percent,
                                     'current_arrear_total': current_arrear_total,
                                     'current_arrear_percent': current_arrear_percent,
                                     'unallocated_receipts_total': unallocated_receipts_total,
                                     'unallocated_receipts_percent': unallocated_receipts_percent,
                                     'server_messages':server_messages})


@login_required(login_url="signin")
def arrears_by_duedate_view(request):

    val_today = datetime.datetime.today().strftime('%Y-%m-%d')

    # retrieve query filters
    query = {}
    for k in ('ara_agreement_id__contains', 'ara_customercompanyname__contains', 'ara_due_date', 'ara_agent_id'):
        if request.GET.get(k):
            query[k] = request.GET[k]

    filter_agent_id = None
    if request.GET.get('ara_agent_id'):
        filter_agent = request.GET.get('ara_agent_id')
        filter_agent_extract = User.objects.filter(id=filter_agent).first()
        if filter_agent_extract:
            filter_agent_id = filter_agent_extract.id
    else:
        # If current user is a collections agent, then default to their collections
        if User.objects.filter(id=request.user.id, groups__name__in=('NCF_Collections_PrimaryAgents',
                                                                    'NCF_Collections_SecondaryAgents')).\
                                                    exclude(groups__name__in=('NCF_Collections_PrimaryAgentManagement',
                                                                    'NCF_Collections_SecondaryAgentManagement')):
            filter_agent_id = request.user.id
            query['ara_agent_id'] = request.user.id

    collections_management = False
    if User.objects.filter(id=request.user.id, groups__name__in=('NCF_Collections_PrimaryAgentManagement',
                                                                 'NCF_Collections_SecondaryAgentManagement')):
        collections_management = True

    # apply Arrears Status Filter
    if not query:
        arrears_by_duedate_extract = arrears_summary_arrear_level.objects.all()
    else:
        arrears_by_duedate_extract = arrears_summary_arrear_level.objects.filter(**query)

    collection_agents_extract = User.objects.filter(groups__name__in=('NCF_Collections_PrimaryAgents',
                                                                    'NCF_Collections_SecondaryAgents'))

    # Apply Current Arrears Filter
    if arrears_by_duedate_extract:
        if not request.GET.get('outstanding_balance'):
            arrears_by_duedate_extract_1 = arrears_by_duedate_extract.exclude(ara_balance_value_grossofvat__lte=0)
        else:
            if request.GET.get('outstanding_balance') == '1':
                arrears_by_duedate_extract_1 = arrears_by_duedate_extract.exclude(
                    ara_balance_value_grossofvat__gt=0)
            else:
                arrears_by_duedate_extract_1 = arrears_by_duedate_extract
    else:
        arrears_by_duedate_extract_1 = arrears_by_duedate_extract

    # apply Agreement Phase
    if arrears_by_duedate_extract_1:
        if request.GET.get('agreement_phase') == '1':
            arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1.exclude(
                ara_transactionsourceid__in=['SP2','SP3','GO3'])
        else:
            if request.GET.get('agreement_phase') == '2':
                arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1.exclude(
                    ara_transactionsourceid__in=['SP1', 'GO1'])
            else:
                arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1
    else:
        arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1

    arrears_by_duedate_list = arrears_by_duedate_extract_2

    # Calculate Arrears Summary Totals
    arrears_percent = 100
    arrears_count = arrears_by_duedate_list.count()
    arrears_total_sum = arrears_by_duedate_list.aggregate(Sum('ara_arrears_value_grossofvat'))
    if not arrears_total_sum["ara_arrears_value_grossofvat__sum"]:
        arrears_total_sum["ara_arrears_value_grossofvat__sum"] = 0
        arrears_percent = 0
    arrears_total = arrears_total_sum["ara_arrears_value_grossofvat__sum"]

    # Calculate Collected Summary Totals
    collected_percent = 0
    collected_count = arrears_by_duedate_list.filter(ara_collected_value_grossofvat__gt=0).count()
    collected_total_sum = arrears_by_duedate_list.aggregate(Sum('ara_collected_value_grossofvat'))
    if not collected_total_sum["ara_collected_value_grossofvat__sum"]:
        collected_total_sum["ara_collected_value_grossofvat__sum"] = 0
        collected_percent = 0
    collected_total = collected_total_sum["ara_collected_value_grossofvat__sum"]

    if arrears_total != 0:
        collected_percent = (collected_total/arrears_total) * 100
    else:
        collected_percent = 0

    # Calculate Adjusted Summary Totals
    adjusted_percent = 0
    adjusted_count = arrears_by_duedate_list.filter(ara_writtenoff_value_grossofvat__gt=0).count()
    adjusted_total_sum = arrears_by_duedate_list.aggregate(Sum('ara_writtenoff_value_grossofvat'))
    if not adjusted_total_sum["ara_writtenoff_value_grossofvat__sum"]:
        adjusted_total_sum["ara_writtenoff_value_grossofvat__sum"] = 0
        adjusted_percent = 0
    adjusted_total = adjusted_total_sum["ara_writtenoff_value_grossofvat__sum"]

    if arrears_total != 0:
        adjusted_percent = (adjusted_total/arrears_total) * 100
    else:
        adjusted_percent = 0

    # Calculate Current Balance Summary Totals
    balance_percent = 100
    balance_count = arrears_by_duedate_list.filter(ara_balance_value_grossofvat__gt=0).count()
    balance_total_sum = arrears_by_duedate_list.aggregate(Sum('ara_balance_value_grossofvat'))
    if not balance_total_sum["ara_balance_value_grossofvat__sum"]:
        balance_total_sum["ara_balance_value_grossofvat__sum"] = 0
        balance_percent = 0
    balance_total = balance_total_sum["ara_balance_value_grossofvat__sum"]

    if balance_total != 0:
        balance_percent = (balance_total/arrears_total) * 100
    else:
        balance_percent = 0

    paginator = Paginator(arrears_by_duedate_list, 9)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    has_filter = False
    if query or filter_agent_id or request.GET.get('outstanding_balance') or request.GET.get('agreement_phase'):
        has_filter = True


    # Process Server Messages from Django Session
    # server_messages = request.session.get('arrears_by_duedate_messages')
    request.session['arrears_by_duedate_messages'] = {}
    server_messages = request.session.get('arrears_by_duedate_messages')

    # Save Url Query String to Django Session
    request.session['arrears_by_arrears_return_querystring'] = {}
    request.session['arrears_by_arrears_return_querystring'] = request.get_full_path()

    return render(request, 'core_arrears/arrears_by_duedate_list.html', {'arrears_list':arrears_by_duedate_list,
                                                'arrears_list_qs': pub,
                                                'has_filter': has_filter,
                                                'filter': query,
                                                'filter_agent_id': filter_agent_id,
                                                'agreement_phase_filter': request.GET.get('agreement_phase'),
                                                'outstanding_balance_filter': request.GET.get('outstanding_balance'),
                                                'collection_agents': collection_agents_extract,
                                                'collections_management': collections_management,
                                                'arrears_total': arrears_total,
                                                'arrears_percent': arrears_percent,
                                                'arrears_count': arrears_count,
                                                'collected_total': collected_total,
                                                'collected_percent': collected_percent,
                                                'collected_count': collected_count,
                                                'adjusted_total': adjusted_total,
                                                'adjusted_percent': adjusted_percent,
                                                'adjusted_count': adjusted_count,
                                                'balance_total': balance_total,
                                                'balance_percent': balance_percent,
                                                'balance_count': balance_count,
                                                'server_messages':server_messages})


@login_required(login_url='signin')
def change_target_agent(request):

    agents_updated_count = 0
    data = {'success': True, 'updated': agents_updated_count}

    # retrieve query filters
    query = {}
    for k in ('ara_agreement_id__contains', 'ara_customercompanyname__contains', 'ara_due_date', 'ara_agent_id'):
        if request.GET.get(k):
            query[k] = request.GET[k]

    filter_agent_id = None
    if request.GET.get('ara_agent_id'):
        filter_agent = request.GET.get('ara_agent_id')
        filter_agent_extract = User.objects.filter(id=filter_agent).first()
        if filter_agent_extract:
            filter_agent_id = filter_agent_extract.id

    # apply Arrears Status Filter
    if not query:
        arrears_by_duedate_extract = arrears_summary_arrear_level.objects.all()
    else:
        arrears_by_duedate_extract = arrears_summary_arrear_level.objects.filter(**query)

    collection_agents_extract = User.objects.filter(groups__name='NCF_Collections_PrimaryAgents')

    # Apply Current Arrears Filter
    if arrears_by_duedate_extract:
        if not request.GET.get('outstanding_balance'):
            arrears_by_duedate_extract_1 = arrears_by_duedate_extract.exclude(ara_balance_value_grossofvat__lte=0)
        else:
            if request.GET.get('outstanding_balance') == '1':
                arrears_by_duedate_extract_1 = arrears_by_duedate_extract.exclude(
                    ara_balance_value_grossofvat__gt=0)
            else:
                arrears_by_duedate_extract_1 = arrears_by_duedate_extract
    else:
        arrears_by_duedate_extract_1 = arrears_by_duedate_extract

    # apply Agreement Phase
    if arrears_by_duedate_extract_1:
        if request.GET.get('agreement_phase') == '1':
            arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1.exclude(
                ara_transactionsourceid__in=['SP2', 'SP3', 'GO3'])
        else:
            if request.GET.get('agreement_phase') == '2':
                arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1.exclude(
                    ara_transactionsourceid__in=['SP1', 'GO1'])
            else:
                arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1
    else:
        arrears_by_duedate_extract_2 = arrears_by_duedate_extract_1

    arrears_by_duedate_list = arrears_by_duedate_extract_2


    if arrears_by_duedate_list.count() > 0:
        arrears_by_duedate_list.update(ara_agent_id=request.GET.get('new_agent'))
        agents_updated_count = arrears_by_duedate_list.count()

    data.update({
        'updated_count': agents_updated_count
    })

    return JsonResponse(data)


@login_required(login_url="signin")
def arrears_by_arrears_summary_view(request, agreement_id):

    val_today = datetime.datetime.today().strftime('%Y-%m-%d')

    # Core Querysets
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    arrears_by_summary_extract = arrears_summary_arrear_level.objects.filter(ara_agreement_id=agreement_id)\
                        .order_by('-ara_due_date',)
    receipt_allocations = receipt_allocations_by_arrears.objects.select_related().filter(ras_agreement_id=agreement_id)\
                        .order_by('-ras_due_date', '-ras_effective_date')
    receipt_collections = receipt_record.objects.filter(rr_agreement_number=agreement_id)\
                            .order_by('-rr_receipt_created_on')

    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    agreement_billing_to_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                              transactiondate__lte=val_today) \
        .exclude(transactionsourceid__in=['SP9', 'GO9', 'GO8'])
    agreement_billing_totals = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id) \
        .exclude(transactionsourceid__in=['SP9', 'GO9', 'GO8'])

    # get the total of any unallocated receipts
    try:
        unallocated_receipts_total = receipt_allocations_by_agreement.objects.get(rag_agreement_id=agreement_id)
        unallocated_receipts_total_val = unallocated_receipts_total.rag_unallocated_value_grossofvat
    except:
        unallocated_receipts_total_val = 0

    #  Get Billing to Date
    agreement_billing_to_date_dict = agreement_billing_to_date.aggregate(Sum('transgrosspayment'))
    if (agreement_billing_to_date_dict is not None) and \
            (agreement_billing_to_date_dict["transgrosspayment__sum"] is not None):
        agreement_billing_to_date_val = agreement_billing_to_date_dict["transgrosspayment__sum"]
    else:
        agreement_billing_to_date_val = 0

    #  Total Billing forecast for agreement
    agreement_billing_totals_dict = agreement_billing_totals.aggregate(Sum('transgrosspayment'))
    if (agreement_billing_totals_dict is not None) and \
            (agreement_billing_totals_dict["transgrosspayment__sum"] is not None):
        agreement_billing_totals_val = agreement_billing_totals_dict["transgrosspayment__sum"]
    else:
        agreement_billing_totals_val = 0

    # Get Total Arrears for AGreement
    arrears_by_agreement_extract = arrears_summary_agreement_level.objects.filter(arr_agreement_id=agreement_id).first()
    if arrears_by_agreement_extract:
        total_agreement_arrears_value = arrears_by_agreement_extract.arr_balance_value_grossofvat
    else:
        total_agreement_arrears_value = 0

    # Agreement % Totals for data widgets
    if agreement_billing_totals_val > 0:
        agreement_billing_to_date_percent = 0
        agreement_arrears_percent = 0
        unallocated_receipts_percent = 0
        agreement_billing_to_date_percent = (agreement_billing_to_date_val / agreement_billing_totals_val) * 100
        agreement_arrears_percent = (total_agreement_arrears_value / agreement_billing_totals_val) * 100
        unallocated_receipts_percent = (unallocated_receipts_total_val / agreement_billing_totals_val) * 100
    else:
        agreement_billing_to_date_percent = 0
        agreement_arrears_percent = 0
        unallocated_receipts_percent = 0

    # Get Regulated Status
    agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=agreement_id).exists()
    if agreement_regulated:
        agreement_regulated_flag = True
    else:
        agreement_regulated_flag = False

    # Agreement Type
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
    else:
        agreement_type = 'HP'

    # Add Arrears Row Number
    row_index = 0
    for row in arrears_by_summary_extract:
        if row.ara_transactionsourceid in ['SP1', 'SP2', 'SP3', 'GO1', 'GO3']:
            row_index += 1
        row.row_index = row_index

    # Add Collections Row Number
    row2_index = receipt_record.objects.filter(rr_agreement_number=agreement_id).count()+1
    for row2 in receipt_collections:
        row2_index -= 1
        if row2.rr_receipt_type_id.startswith('DR'):
            receipt_crdr_flag = 'DR'
        else:
            receipt_crdr_flag = 'CR'
        row2.receipt_crdr_flag = receipt_crdr_flag
        row2.row2_index = row2_index

    # Retrieve arrears_by_agreement query string from Django Session
    arrears_by_arrears_return_querystring = request.session.get('arrears_by_arrears_return_querystring')

    # Retrieve, Display and Clear server messages from Django Session
    server_messages = request.session.get('arrears_by_arrears_messages')
    request.session['arrears_by_arrears_messages'] = {}

    # Return to Template
    return render(request, 'core_arrears/arrears_by_arrears_summary.html',
                  {'agreement_detail': agreement_detail,
                   'agreement_billing_totals_val': agreement_billing_totals_val,
                   'agreement_billing_to_date_val': agreement_billing_to_date_val,
                   'agreement_billing_to_date_percent': agreement_billing_to_date_percent,
                   'total_agreement_arrears_value': total_agreement_arrears_value,
                   'agreement_arrears_percent': agreement_arrears_percent,
                   'unallocated_receipts_total_val': unallocated_receipts_total_val,
                   'unallocated_receipts_percent': unallocated_receipts_percent,
                   'agreement_customer': agreement_customer,
                   'arrears_summary_list': arrears_by_summary_extract,
                   'receipt_allocations': receipt_allocations,
                   'receipt_collections': receipt_collections,
                   'agreement_type': agreement_type,
                   'agreement_regulated_flag': agreement_regulated_flag,
                   'arrears_by_arrears_return_querystring':arrears_by_arrears_return_querystring,
                   'server_messages': server_messages
                   })


@login_required(login_url="signin")
def arrear_save_form(request, ara_agreement_id, ara_arrears_id, template_name):

    # initialise data dictionary
    data = dict()

    # retrieve form data
    wip_agreement_id = ara_agreement_id
    wip_arrears_id = ara_arrears_id

    # retrieve database objects
    arrears_by_agreement_extract = arrears_summary_agreement_level.objects.get(arr_agreement_id=wip_agreement_id)
    arrears_by_summary_extract = arrears_summary_arrear_level.objects.filter(ara_agreement_id=wip_agreement_id,
                                                                             ara_arrears_id=wip_arrears_id) \
                                                                            .order_by('-ara_due_date', ).first()

    current_agent = arrears_by_summary_extract.ara_agent_id_id
    collection_agents_extract = User.objects.filter(groups__name='NCF_Collections_PrimaryAgents')

    active_status = arrears_status.objects.get(arr_status_code='A')
    val_today = datetime.datetime.today().strftime('%Y-%m-%d')
    val_transactionsourceid = arrears_by_summary_extract.ara_transactionsourceid

    # POST Request
    # ============
    if request.method == 'POST':

        # Retrieve Input from Form
        form_arrears_total_arrears = request.POST.get('arrears_total_arrears')
        form_arrears_total_collected = request.POST.get('arrears_total_collected')
        form_arrears_total_adjustment = request.POST.get('arrears_total_adjustment')
        form_arrears_total_balance = request.POST.get('arrears_total_balance')
        form_arrear_val_1 = request.POST.get('arrear_val_1')
        form_collected_val_1 = request.POST.get('collected_val_1')
        form_adjustment_val_1 = request.POST.get('adjustment_val_1')
        form_balance_val_1 = request.POST.get('balance_val_1')
        form_arrear_val_2 = request.POST.get('arrear_val_2')
        form_collected_val_2 = request.POST.get('collected_val_2')
        form_adjustment_val_2 = request.POST.get('adjustment_val_2')
        form_balance_val_2 = request.POST.get('balance_val_2')
        form_arrear_val_3 = request.POST.get('arrear_val_3')
        form_collected_val_3 = request.POST.get('collected_val_3')
        form_adjustment_val_3 = request.POST.get('adjustment_val_3')
        form_balance_val_3 = request.POST.get('balance_val_3')
        form_arrear_val_4 = request.POST.get('arrear_val_4')
        form_collected_val_4 = request.POST.get('collected_val_4')
        form_adjustment_val_4 = request.POST.get('adjustment_val_4')
        form_balance_val_4 = request.POST.get('balance_val_4')
        form_arrear_val_5 = request.POST.get('arrear_val_5')
        form_collected_val_5 = request.POST.get('collected_val_5')
        form_adjustment_val_5 = request.POST.get('adjustment_val_5')
        form_balance_val_5 = request.POST.get('balance_val_5')
        form_arrear_val_6 = request.POST.get('arrear_val_6')
        form_collected_val_6 = request.POST.get('collected_val_6')
        form_adjustment_val_6 = request.POST.get('adjustment_val_6')
        form_balance_val_6 = request.POST.get('balance_val_6')
        if request.POST.get('target_agent'):
            form_new_agent_id = request.POST.get('target_agent')
            try:
                form_new_agent = User.objects.get(id=form_new_agent_id)
            except:
                form_new_agent = request.user
        else:
            form_new_agent = request.user

        # remove comma separators from numeric
        str_arrears_total_arrears = form_arrears_total_arrears.replace(",", "")
        str_arrears_total_collected = form_arrears_total_collected.replace(",","")
        str_arrears_total_adjustment = form_arrears_total_adjustment.replace(",","")
        str_arrears_total_balance = form_arrears_total_balance.replace(",","")
        str_arrear_val_1 = form_arrear_val_1.replace(",","")
        str_collected_val_1 = form_collected_val_1.replace(",","")
        str_adjustment_val_1 = form_adjustment_val_1.replace(",","")
        str_balance_val_1 = form_balance_val_1.replace(",","")
        str_arrear_val_2 = form_arrear_val_2.replace(",", "")
        str_collected_val_2 = form_collected_val_2.replace(",", "")
        str_adjustment_val_2 = form_adjustment_val_2.replace(",", "")
        str_balance_val_2 = form_balance_val_2.replace(",", "")
        str_arrear_val_3 = form_arrear_val_3.replace(",", "")
        str_collected_val_3 = form_collected_val_3.replace(",", "")
        str_adjustment_val_3 = form_adjustment_val_3.replace(",", "")
        str_balance_val_3 = form_balance_val_3.replace(",", "")
        str_arrear_val_4 = form_arrear_val_4.replace(",", "")
        str_collected_val_4 = form_collected_val_4.replace(",", "")
        str_adjustment_val_4 = form_adjustment_val_4.replace(",", "")
        str_balance_val_4 = form_balance_val_4.replace(",", "")
        str_arrear_val_5 = form_arrear_val_5.replace(",", "")
        str_collected_val_5 = form_collected_val_5.replace(",", "")
        str_adjustment_val_5 = form_adjustment_val_5.replace(",", "")
        str_balance_val_5 = form_balance_val_5.replace(",", "")
        str_arrear_val_6 = form_arrear_val_6.replace(",", "")
        str_collected_val_6 = form_collected_val_6.replace(",", "")
        str_adjustment_val_6 = form_adjustment_val_6.replace(",", "")
        str_balance_val_6 = form_balance_val_6.replace(",", "")

        # convert to float and then round
        val_arrears_total_arrears = round(floatify(str_arrears_total_arrears), 2)
        val_arrears_total_collected = round(floatify(str_arrears_total_collected),2)
        val_arrears_total_adjustment = round(floatify(str_arrears_total_adjustment),2)
        val_arrears_total_balance = round(floatify(str_arrears_total_balance),2)
        rental_arrears_value = round(floatify(str_arrear_val_1), 2)
        rental_collected_value = round(floatify(str_collected_val_1), 2)
        rental_adjustment_value = round(floatify(str_adjustment_val_1), 2)
        rental_balance_value = round(floatify(str_balance_val_1), 2)
        bamf_arrears_value = round(floatify(str_arrear_val_2), 2)
        bamf_collected_value = round(floatify(str_collected_val_2), 2)
        bamf_adjustment_value = round(floatify(str_adjustment_val_2), 2)
        bamf_balance_value = round(floatify(str_balance_val_2), 2)
        risk_arrears_value = round(floatify(str_arrear_val_3), 2)
        risk_collected_value = round(floatify(str_collected_val_3), 2)
        risk_adjustment_value = round(floatify(str_adjustment_val_3), 2)
        risk_balance_value = round(floatify(str_balance_val_3), 2)
        bounce_arrears_value = round(floatify(str_arrear_val_4), 2)
        bounce_collected_value = round(floatify(str_collected_val_4), 2)
        bounce_adjustment_value = round(floatify(str_adjustment_val_4), 2)
        bounce_balance_value = round(floatify(str_balance_val_4), 2)
        letter_arrears_value = round(floatify(str_arrear_val_5), 2)
        letter_collected_value = round(floatify(str_collected_val_5), 2)
        letter_adjustment_value = round(floatify(str_adjustment_val_5), 2)
        letter_balance_value = round(floatify(str_balance_val_5), 2)
        visit_arrears_value = round(floatify(str_arrear_val_6), 2)
        visit_collected_value = round(floatify(str_collected_val_6), 2)
        visit_adjustment_value = round(floatify(str_adjustment_val_6), 2)
        visit_balance_value = round(floatify(str_balance_val_6), 2)

        # RECEIPTS : get the next Receipt allocation_id
        # =============================================
        try:
            dict_last_id = receipt_allocations_by_arrears.objects.\
                filter(ras_agreement_id=wip_agreement_id, ras_arrears_id=wip_arrears_id) \
                .aggregate(Max('ras_allocation_id'))
            wip_last_allocation_id = dict_last_id["ras_allocation_id__max"]
        except ObjectDoesNotExist:
            wip_last_allocation_id = 0

        if not wip_last_allocation_id:
            wip_last_allocation_id = 0

        wip_next_allocation_id = wip_last_allocation_id + 1

        # Retrieve all Allocation Types for use later
        # ===========================================
        if val_transactionsourceid == 'SP1' or val_transactionsourceid == 'GO1':
            val_arrears_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=100)
            val_bamf_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=105)
            val_risk_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=101)
            val_bounce_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=102)
            val_letter_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=103)
            val_visit_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=104)
        else:
            val_arrears_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=200)
            val_bamf_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=205)
            val_risk_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=201)
            val_bounce_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=202)
            val_letter_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=203)
            val_visit_charge_type = arrears_allocation_type.objects. \
                get(arr_allocation_src_id=val_transactionsourceid, arr_allocation_id=204)

        # RECEIPTS : Create RECEIPT_ALLOCATIONS_BY_ARREARS object
        # ============================================
        receipt_allocations_by_arrears.objects.create(
            ras_agreement_id=wip_agreement_id,
            ras_customernumber=arrears_by_agreement_extract.arr_customernumber,
            ras_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
            ras_effective_date=datetime.datetime.now(),
            ras_due_date=arrears_by_summary_extract.ara_due_date,
            ras_transactionsourceid=arrears_by_summary_extract.ara_transactionsourceid,
            ras_reference=arrears_by_summary_extract.ara_reference,
            ras_referencestrip=arrears_by_summary_extract.ara_referencestrip,
            ras_return_description=arrears_by_summary_extract.ara_return_description,
            ras_arrears_id=wip_arrears_id,
            ras_allocation_id=wip_next_allocation_id,
            ras_arrears_value_netofvat=round((val_arrears_total_arrears/1.2),2),
            ras_arrears_value_grossofvat=val_arrears_total_arrears,
            ras_collected_value_netofvat=round((val_arrears_total_collected/1.2),2),
            ras_collected_value_grossofvat=val_arrears_total_collected,
            ras_adjustment_value_netofvat=round((val_arrears_total_adjustment/1.2),2),
            ras_adjustment_value_grossofvat=val_arrears_total_adjustment,
            ras_balance_value_netofvat=round((val_arrears_total_balance/1.2),2),
            ras_balance_value_grossofvat=val_arrears_total_balance,
            ras_agent_id=form_new_agent,
            ras_status=active_status,
            ras_status_date=val_today,
        )

        # RECEIPTS : CREATE RECEIPT_ALLOCATIONS_BY_DETAIL objects
        # =============================================

        wip_history_rental_collected_grossofvat = 0
        wip_history_rental_adjustment_grossofvat = 0
        wip_history_bouncefees_collected_grossofvat = 0
        wip_history_bouncefees_adjustment_grossofvat = 0

        if rental_arrears_value != 0:

            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber = arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname = arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date = datetime.datetime.now(),
                rad_due_date = arrears_by_summary_extract.ara_due_date,
                rad_reference = arrears_by_summary_extract.ara_reference,
                rad_referencestrip = arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id = wip_arrears_id,
                rad_allocation_id = wip_next_allocation_id,
                rad_allocation_charge_type=val_arrears_charge_type,
                rad_arrears_value_netofvat = round((rental_arrears_value/1.2),2),
                rad_arrears_value_grossofvat = rental_arrears_value,
                rad_collected_value_netofvat = round((rental_collected_value/1.2),2),
                rad_collected_value_grossofvat = rental_collected_value,
                rad_adjustment_value_netofvat = round((rental_adjustment_value/1.2),2),
                rad_adjustment_value_grossofvat = rental_adjustment_value,
                rad_balance_value_netofvat = round((rental_balance_value/1.2),2),
                rad_balance_value_grossofvat = rental_balance_value,
                rad_agent_id = form_new_agent,
                rad_status = active_status,
                rad_status_date = val_today
            )

            wip_history_rental_collected_grossofvat = wip_history_rental_collected_grossofvat + rental_collected_value
            wip_history_rental_adjustment_grossofvat = wip_history_rental_adjustment_grossofvat + rental_adjustment_value

        if bamf_arrears_value != 0:
            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date=datetime.datetime.now(),
                rad_due_date=arrears_by_summary_extract.ara_due_date,
                rad_reference=arrears_by_summary_extract.ara_reference,
                rad_referencestrip=arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id=wip_arrears_id,
                rad_allocation_id=wip_next_allocation_id,
                rad_allocation_charge_type=val_bamf_charge_type,
                rad_arrears_value_netofvat=round((bamf_arrears_value / 1.2), 2),
                rad_arrears_value_grossofvat=bamf_arrears_value,
                rad_collected_value_netofvat=round((bamf_collected_value / 1.2), 2),
                rad_collected_value_grossofvat=bamf_collected_value,
                rad_adjustment_value_netofvat=round((bamf_adjustment_value / 1.2), 2),
                rad_adjustment_value_grossofvat=bamf_adjustment_value,
                rad_balance_value_netofvat=round((bamf_balance_value / 1.2), 2),
                rad_balance_value_grossofvat=bamf_balance_value,
                rad_agent_id=form_new_agent,
                rad_status=active_status,
                rad_status_date=val_today
            )

            wip_history_rental_collected_grossofvat = wip_history_rental_collected_grossofvat + bamf_collected_value
            wip_history_rental_adjustment_grossofvat = wip_history_rental_adjustment_grossofvat + bamf_adjustment_value

        if risk_arrears_value != 0:

            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date=datetime.datetime.now(),
                rad_due_date=arrears_by_summary_extract.ara_due_date,
                rad_reference=arrears_by_summary_extract.ara_reference,
                rad_referencestrip=arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id=wip_arrears_id,
                rad_allocation_id=wip_next_allocation_id,
                rad_allocation_charge_type=val_risk_charge_type,
                rad_arrears_value_netofvat=round((risk_arrears_value / 1.2), 2),
                rad_arrears_value_grossofvat=risk_arrears_value,
                rad_collected_value_netofvat=round((risk_collected_value / 1.2), 2),
                rad_collected_value_grossofvat=risk_collected_value,
                rad_adjustment_value_netofvat=round((risk_adjustment_value / 1.2), 2),
                rad_adjustment_value_grossofvat=risk_adjustment_value,
                rad_balance_value_netofvat=round((risk_balance_value / 1.2), 2),
                rad_balance_value_grossofvat=risk_balance_value,
                rad_agent_id=form_new_agent,
                rad_status=active_status,
                rad_status_date=val_today
            )

            wip_history_rental_collected_grossofvat = wip_history_rental_collected_grossofvat + risk_collected_value
            wip_history_rental_adjustment_grossofvat = wip_history_rental_adjustment_grossofvat + risk_adjustment_value

        wip_due_date = arrears_by_summary_extract.ara_due_date.strftime('%d/%m/%Y')
        wip_history_date = datetime.date.today()
        if not isinstance(wip_history_date, datetime.datetime):
            my_time = datetime.datetime.min.time()
            wip_history_date = datetime.datetime.combine(wip_history_date, my_time)

        if wip_history_rental_collected_grossofvat != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '701',
                                  'Col',
                                  (-1 * wip_history_rental_collected_grossofvat),
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'DD Balance Collected for ' + wip_due_date)

        if wip_history_rental_adjustment_grossofvat != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '701',
                                  'Col',
                                  (-1 * wip_history_rental_adjustment_grossofvat),
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'DD Balance Adjustment for ' + wip_due_date)

        if bounce_arrears_value != 0:
            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date=datetime.datetime.now(),
                rad_due_date=arrears_by_summary_extract.ara_due_date,
                rad_reference=arrears_by_summary_extract.ara_reference,
                rad_referencestrip=arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id=wip_arrears_id,
                rad_allocation_id=wip_next_allocation_id,
                rad_allocation_charge_type=val_bounce_charge_type,
                rad_arrears_value_netofvat=round((bounce_arrears_value / 1.2), 2),
                rad_arrears_value_grossofvat=bounce_arrears_value,
                rad_collected_value_netofvat=round((bounce_collected_value / 1.2), 2),
                rad_collected_value_grossofvat=bounce_collected_value,
                rad_adjustment_value_netofvat=round((bounce_adjustment_value / 1.2), 2),
                rad_adjustment_value_grossofvat=bounce_adjustment_value,
                rad_balance_value_netofvat=round((bounce_balance_value / 1.2), 2),
                rad_balance_value_grossofvat=bounce_balance_value,
                rad_agent_id=form_new_agent,
                rad_status=active_status,
                rad_status_date=val_today
            )

            wip_history_bouncefees_collected_grossofvat = bounce_collected_value
            wip_history_bouncefees_adjustment_grossofvat = bounce_adjustment_value

        if letter_arrears_value != 0:
            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date=datetime.datetime.now(),
                rad_due_date=arrears_by_summary_extract.ara_due_date,
                rad_reference=arrears_by_summary_extract.ara_reference,
                rad_referencestrip=arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id=wip_arrears_id,
                rad_allocation_id=wip_next_allocation_id,
                rad_allocation_charge_type=val_letter_charge_type,
                rad_arrears_value_netofvat=round((letter_arrears_value / 1.2), 2),
                rad_arrears_value_grossofvat=letter_arrears_value,
                rad_collected_value_netofvat=round((letter_collected_value / 1.2), 2),
                rad_collected_value_grossofvat=letter_collected_value,
                rad_adjustment_value_netofvat=round((letter_adjustment_value / 1.2), 2),
                rad_adjustment_value_grossofvat=letter_adjustment_value,
                rad_balance_value_netofvat=round((letter_balance_value / 1.2), 2),
                rad_balance_value_grossofvat=letter_balance_value,
                rad_agent_id=form_new_agent,
                rad_status=active_status,
                rad_status_date=val_today
            )

            wip_history_bouncefees_collected_grossofvat = wip_history_bouncefees_collected_grossofvat + letter_collected_value
            wip_history_bouncefees_adjustment_grossofvat = wip_history_bouncefees_adjustment_grossofvat + letter_adjustment_value

        if visit_arrears_value != 0:
            receipt_allocations_by_detail.objects.create(
                rad_agreement_id=wip_agreement_id,
                rad_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rad_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rad_effective_date=datetime.datetime.now(),
                rad_due_date=arrears_by_summary_extract.ara_due_date,
                rad_reference=arrears_by_summary_extract.ara_reference,
                rad_referencestrip=arrears_by_summary_extract.ara_referencestrip,
                rad_arrears_id=wip_arrears_id,
                rad_allocation_id=wip_next_allocation_id,
                rad_allocation_charge_type=val_visit_charge_type,
                rad_arrears_value_netofvat=round((visit_arrears_value / 1.2), 2),
                rad_arrears_value_grossofvat=visit_arrears_value,
                rad_collected_value_netofvat=round((visit_collected_value / 1.2), 2),
                rad_collected_value_grossofvat=visit_collected_value,
                rad_adjustment_value_netofvat=round((visit_adjustment_value / 1.2), 2),
                rad_adjustment_value_grossofvat=visit_adjustment_value,
                rad_balance_value_netofvat=round((visit_balance_value / 1.2), 2),
                rad_balance_value_grossofvat=visit_balance_value,
                rad_agent_id=form_new_agent,
                rad_status=active_status,
                rad_status_date=val_today
            )

            wip_history_bouncefees_collected_grossofvat = wip_history_bouncefees_collected_grossofvat + visit_collected_value
            wip_history_bouncefees_adjustment_grossofvat = wip_history_bouncefees_adjustment_grossofvat + visit_adjustment_value

        wip_due_date = arrears_by_summary_extract.ara_due_date.strftime('%d/%m/%Y')
        wip_history_date = datetime.date.today()
        if not isinstance(wip_history_date, datetime.datetime):
            my_time = datetime.datetime.min.time()
            wip_history_date = datetime.datetime.combine(wip_history_date, my_time)

        if wip_history_bouncefees_collected_grossofvat != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '702',
                                  'Col',
                                  (-1 * wip_history_bouncefees_collected_grossofvat),
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'Bounce Fees Collected for ' + wip_due_date)

        if wip_history_bouncefees_adjustment_grossofvat != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '702',
                                  'Col',
                                  (-1 * wip_history_bouncefees_adjustment_grossofvat),
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'Bounce Fee Adjustment for ' + wip_due_date)

        # RECEIPTS : Recalculate receipt allocations by agreement
        # ============================================
        allocated_collected_gross = 0
        allocated_collected_net = 0
        allocated_count = 0
        no_date = datetime.datetime.strptime('Jan 1 2000', '%b %d %Y').date()
        last_allocated_date = no_date
        last_unallocated_date = no_date

        # RECEIPTS : GET the new total of Receipt Allocations for the agreement
        # ==========================================================
        # receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id)
        receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id) \
            .exclude(ras_status__arr_status_code='X')
        for receipt_allocation in receipt_allocations:

            allocated_collected_gross += receipt_allocation.ras_collected_value_grossofvat
            allocated_collected_net += receipt_allocation.ras_collected_value_netofvat
            if receipt_allocation.ras_collected_value_grossofvat != 0:
                allocated_count += 1
                if receipt_allocation.ras_status_date > last_allocated_date:
                    last_allocated_date = receipt_allocation.ras_status_date

        # RECEIPTS : Amend/Write Receipt Allocations by Agreement
        # =======================================================
        try:
            receipt_allocations_by_agreement_obj = receipt_allocations_by_agreement.objects.get(rag_agreement_id=wip_agreement_id)
        except ObjectDoesNotExist:
            receipt_allocations_by_agreement_obj = None

        if receipt_allocations_by_agreement_obj:

            unallocated_value_netofvat = receipt_allocations_by_agreement_obj.rag_received_value_netofvat - allocated_collected_net
            unallocated_value_grossofvat = receipt_allocations_by_agreement_obj.rag_received_value_grossofvat - allocated_collected_gross
            if last_allocated_date != '2000-01-01':
                last_unallocated_date = last_allocated_date

            receipt_allocations_by_agreement_obj.rag_allocated_value_netofvat = allocated_collected_net
            receipt_allocations_by_agreement_obj.rag_allocated_value_grossofvat = allocated_collected_gross
            receipt_allocations_by_agreement_obj.rag_allocated_last_date = last_allocated_date
            receipt_allocations_by_agreement_obj.rag_allocated_count = allocated_count
            receipt_allocations_by_agreement_obj.rag_unallocated_value_netofvat = unallocated_value_netofvat
            receipt_allocations_by_agreement_obj.rag_unallocated_value_grossofvat = unallocated_value_grossofvat
            receipt_allocations_by_agreement_obj.rag_unallocated_last_date = last_unallocated_date
            receipt_allocations_by_agreement_obj.rag_agent_id = form_new_agent
            receipt_allocations_by_agreement_obj.rag_status = active_status
            receipt_allocations_by_agreement_obj.rag_status_date = val_today
            receipt_allocations_by_agreement_obj.save()

        else:

            receipt_allocations_by_agreement.objects.create(
                rag_agreement_id=wip_agreement_id,
                rag_customernumber = arrears_by_agreement_extract.arr_customernumber,
                rag_customercompanyname = arrears_by_agreement_extract.arr_customercompanyname,
                rag_received_count = 1,
                rag_received_value_netofvat = 0,
                rag_received_value_grossofvat = 0,
                rag_received_last_date = val_today,
                rag_allocated_count = 0,
                rag_allocated_value_netofvat = 0,
                rag_allocated_value_grossofvat = 0,
                rag_allocated_last_date = val_today,
                rag_unallocated_value_netofvat = 0,
                rag_unallocated_value_grossofvat = 0,
                rag_unallocated_last_date = val_today,
                rag_agent_id = form_new_agent,
                rag_status = active_status,
                rag_status_date = val_today
            )

        # ARREARS: Write/Update arrears detail level
        # ==========================================
        arrears_by_detail_extract = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                               ard_arrears_id=wip_arrears_id) \
            .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')

        for arrear_detail in arrears_by_detail_extract:

            # sum_arrears_value_netofvat = 0
            # sum_arrears_value_grossofvat = 0
            sum_collected_value_netofvat = 0
            sum_collected_value_grossofvat = 0
            sum_collected_last_date = 0
            sum_writtenoff_value_netofvat = 0
            sum_writtenoff_value_grossofvat = 0
            sum_balance_value_netofvat = 0
            sum_balance_value_grossofvat = 0
            val_receipt_allocated = False

            # receipt_allocations_by_detail_extract = receipt_allocations_by_detail.objects.\
            #     filter(rad_agreement_id=arrear_detail.ard_agreement_id,
            #            rad_arrears_id=arrear_detail.ard_arrears_id,
            #            rad_allocation_charge_type_id=arrear_detail.ard_arrears_charge_type_id).\
            #         order_by('rad_allocation_id')

            receipt_allocations_by_detail_extract = receipt_allocations_by_detail.objects. \
                filter(rad_agreement_id=arrear_detail.ard_agreement_id,
                       rad_arrears_id=arrear_detail.ard_arrears_id,
                       rad_allocation_charge_type_id=arrear_detail.ard_arrears_charge_type_id). \
                exclude(rad_status__arr_status_code='X').order_by('rad_allocation_id')

            for receipt_allocation in receipt_allocations_by_detail_extract:

                val_receipt_allocated = True
                # sum_arrears_value_netofvat += receipt_allocation.rad_arrears_value_netofvat
                # sum_arrears_value_grossofvat += receipt_allocation.rad_arrears_value_grossofvat
                sum_collected_value_netofvat += receipt_allocation.rad_collected_value_netofvat
                sum_collected_value_grossofvat += receipt_allocation.rad_collected_value_grossofvat
                sum_writtenoff_value_netofvat += receipt_allocation.rad_adjustment_value_netofvat
                sum_writtenoff_value_grossofvat += receipt_allocation.rad_adjustment_value_grossofvat
                # sum_balance_value_netofvat = sum_arrears_value_netofvat - sum_collected_value_netofvat\
                #                                 - sum_writtenoff_value_netofvat
                # sum_balance_value_grossofvat = sum_arrears_value_grossofvat - sum_collected_value_grossofvat\
                #                                 - sum_writtenoff_value_grossofvat
                val_status_date = receipt_allocation.rad_status_date
                val_agent_id = receipt_allocation.rad_agent_id
                val_status = receipt_allocation.rad_status

            if val_receipt_allocated:

                # arrear_detail.ard_arrears_value_netofvat = sum_arrears_value_netofvat
                # arrear_detail.ard_arrears_value_grossofvat = sum_arrears_value_grossofvat
                arrear_detail.ard_collected_value_netofvat = sum_collected_value_netofvat
                arrear_detail.ard_collected_value_grossofvat = sum_collected_value_grossofvat
                arrear_detail.ard_writtenoff_value_netofvat = sum_writtenoff_value_netofvat
                arrear_detail.ard_writtenoff_value_grossofvat = sum_writtenoff_value_grossofvat
                arrear_detail.ard_balance_value_netofvat = arrear_detail.ard_arrears_value_netofvat \
                                                           - sum_collected_value_netofvat \
                                                           - sum_writtenoff_value_netofvat
                arrear_detail.ard_balance_value_grossofvat = arrear_detail.ard_arrears_value_grossofvat \
                                                           - sum_collected_value_grossofvat \
                                                           - sum_writtenoff_value_grossofvat
                arrear_detail.ard_agent_id = val_agent_id
                arrear_detail.ard_status = val_status
                arrear_detail.ard_status_date = val_status_date
                arrear_detail.save()


        # ARREARS: Write/Update arrears at ARREARS level
        # ==============================================
        try:

            # Get the Arrears level object to be updated
            arrears_by_arrears_extract = arrears_summary_arrear_level.objects.get(ara_agreement_id=wip_agreement_id,
                                                                                    ara_arrears_id=wip_arrears_id)

            val_collected_value_netofvat = 0
            val_collected_value_grossofvat = 0
            val_collected_count = 0
            val_writtenoff_value_netofvat = 0
            val_writtenoff_value_grossofvat = 0
            val_writtenoff_count = 0
            val_balance_value_netofvat = 0
            val_balance_value_grossofvat = 0
            val_arrears_value_netofvat = 0
            val_arrears_value_grossofvat = 0

            if arrears_by_arrears_extract:

                # Now get and sum all arrear details for arrears_id
                arrears_by_detail_extract = arrears_detail_arrear_level.objects.filter(
                    ard_agreement_id=wip_agreement_id,
                    ard_arrears_id=wip_arrears_id) \
                    .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')

                # Sum values
                try:
                    tuple_retrieved_aggregates = arrears_by_detail_extract.aggregate(Sum('ard_collected_value_netofvat'),
                                                                                     Sum('ard_collected_value_grossofvat'),
                                                                                     Sum('ard_writtenoff_value_netofvat'),
                                                                                     Sum('ard_writtenoff_value_grossofvat'),
                                                                                     Sum('ard_arrears_value_netofvat'),
                                                                                     Sum('ard_arrears_value_grossofvat')
                                                                                     )
                    if tuple_retrieved_aggregates is not None:

                        # if tuple_retrieved_aggregates('ard_collected_value_netofvat__sum') != 0:
                        val_collected_value_netofvat = tuple_retrieved_aggregates['ard_collected_value_netofvat__sum']

                        # if tuple_retrieved_aggregates('ard_collected_value_grossofvat__sum') != 0:
                        val_collected_value_grossofvat = tuple_retrieved_aggregates['ard_collected_value_grossofvat__sum']

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_netofvat__sum') != 0:
                        val_writtenoff_value_netofvat = tuple_retrieved_aggregates["ard_writtenoff_value_netofvat__sum"]

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_grossofvat__sum') != 0:
                        val_writtenoff_value_grossofvat = tuple_retrieved_aggregates['ard_writtenoff_value_grossofvat__sum']

                        val_arrears_value_netofvat = tuple_retrieved_aggregates["ard_arrears_value_netofvat__sum"]
                        val_arrears_value_grossofvat = tuple_retrieved_aggregates['ard_arrears_value_grossofvat__sum']

                except:
                    pass

            val_balance_value_netofvat = val_arrears_value_netofvat - \
                                            val_collected_value_netofvat - val_writtenoff_value_netofvat

            val_balance_value_grossofvat = val_arrears_value_grossofvat - \
                                         val_collected_value_grossofvat - val_writtenoff_value_grossofvat

            arrears_by_arrears_extract.ara_arrears_value_netofvat = val_arrears_value_netofvat
            arrears_by_arrears_extract.ara_arrears_value_grossofvat = val_arrears_value_grossofvat
            arrears_by_arrears_extract.ara_collected_value_netofvat = val_collected_value_netofvat
            arrears_by_arrears_extract.ara_collected_value_grossofvat = val_collected_value_grossofvat
            arrears_by_arrears_extract.ara_collected_count = val_collected_count
            arrears_by_arrears_extract.ara_writtenoff_value_netofvat = val_writtenoff_value_netofvat
            arrears_by_arrears_extract.ara_writtenoff_value_grossofvat = val_writtenoff_value_grossofvat
            arrears_by_arrears_extract.ara_writtenoff_count = val_writtenoff_count
            arrears_by_arrears_extract.ara_balance_value_netofvat = val_balance_value_netofvat
            arrears_by_arrears_extract.ara_balance_value_grossofvat = val_balance_value_grossofvat
            arrears_by_arrears_extract.ara_status_date = val_today
            arrears_by_arrears_extract.save()

        except:

            pass

        # ARREARS: Write/Update arrears at AGREEMENT level
        # ================================================
        try:

            # Get the Agreement level object to be updated
            arrears_by_agreement_extract = arrears_summary_agreement_level.objects.get(arr_agreement_id=wip_agreement_id)

            print('Hello')
            print(arrears_by_agreement_extract.arr_agreement_id)
            val_collected_value_netofvat = 0
            val_collected_value_grossofvat = 0
            val_collected_count = 0
            val_writtenoff_value_netofvat = 0
            val_writtenoff_value_grossofvat = 0
            val_writtenoff_count = 0
            val_balance_value_netofvat = 0
            val_balance_value_grossofvat = 0
            val_arrears_value_netofvat = 0
            val_arrears_value_grossofvat = 0

            if arrears_by_agreement_extract:

                # Now get and sum all arrear details for arrears_id
                arrears_by_arrears_extract = arrears_summary_arrear_level.objects.filter(
                    ara_agreement_id=wip_agreement_id) \
                    .order_by('-ara_due_date', 'ara_arrears_id')

                # Sum values
                try:
                    tuple_retrieved_aggregates = arrears_by_arrears_extract.aggregate(Sum('ara_collected_value_netofvat'),
                                                                                     Sum('ara_collected_value_grossofvat'),
                                                                                     Sum('ara_writtenoff_value_netofvat'),
                                                                                     Sum('ara_writtenoff_value_grossofvat'),
                                                                                     Sum('ara_arrears_value_netofvat'),
                                                                                     Sum('ara_arrears_value_grossofvat')
                                                                                     )
                    if tuple_retrieved_aggregates is not None:

                        # if tuple_retrieved_aggregates('ard_collected_value_netofvat__sum') != 0:
                        val_collected_value_netofvat = tuple_retrieved_aggregates['ara_collected_value_netofvat__sum']

                        # if tuple_retrieved_aggregates('ard_collected_value_grossofvat__sum') != 0:
                        val_collected_value_grossofvat = tuple_retrieved_aggregates['ara_collected_value_grossofvat__sum']

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_netofvat__sum') != 0:
                        val_writtenoff_value_netofvat = tuple_retrieved_aggregates["ara_writtenoff_value_netofvat__sum"]

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_grossofvat__sum') != 0:
                        val_writtenoff_value_grossofvat = tuple_retrieved_aggregates['ara_writtenoff_value_grossofvat__sum']

                        val_arrears_value_netofvat = tuple_retrieved_aggregates["ara_arrears_value_netofvat__sum"]
                        val_arrears_value_grossofvat = tuple_retrieved_aggregates['ara_arrears_value_grossofvat__sum']

                        print('again')
                        print(val_collected_value_netofvat)

                except:
                    pass



            val_balance_value_netofvat = val_arrears_value_netofvat - \
                                            val_collected_value_netofvat - val_writtenoff_value_netofvat

            val_balance_value_grossofvat = val_arrears_value_grossofvat - \
                                         val_collected_value_grossofvat - val_writtenoff_value_grossofvat

            # Get Unallocated receipts
            unallocated_by_agreement = receipt_allocations_by_agreement.objects.filter(
                                            rag_agreement_id=wip_agreement_id).first()
            if unallocated_by_agreement:
                xip_unallocated_value_netofvat = unallocated_by_agreement.rag_unallocated_value_netofvat
                xip_unallocated_value_grossofvat = unallocated_by_agreement.rag_unallocated_value_grossofvat
                xip_unallocated_last_date = unallocated_by_agreement.rag_unallocated_last_date
            else:
                xip_unallocated_value_netofvat = 0
                xip_unallocated_value_grossofvat = 0
                xip_unallocated_last_date = val_today

            print('again2')
            print(val_collected_value_netofvat)
            arrears_by_agreement_extract.arr_arrears_value_netofvat = val_arrears_value_netofvat
            arrears_by_agreement_extract.arr_arrears_value_grossofvat = val_arrears_value_grossofvat
            arrears_by_agreement_extract.arr_collected_value_netofvat = val_collected_value_netofvat
            arrears_by_agreement_extract.arr_collected_value_grossofvat = val_collected_value_grossofvat
            arrears_by_agreement_extract.arr_collected_count = val_collected_count
            arrears_by_agreement_extract.arr_writtenoff_value_netofvat = val_writtenoff_value_netofvat
            arrears_by_agreement_extract.arr_writtenoff_value_grossofvat = val_writtenoff_value_grossofvat
            arrears_by_agreement_extract.arr_writtenoff_count = val_writtenoff_count
            arrears_by_agreement_extract.arr_balance_value_netofvat = val_balance_value_netofvat
            arrears_by_agreement_extract.arr_balance_value_grossofvat = val_balance_value_grossofvat
            arrears_by_agreement_extract.arr_status_date = val_today
            arrears_by_agreement_extract.arr_unallocated_value_netofvat = xip_unallocated_value_netofvat
            arrears_by_agreement_extract.arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat
            arrears_by_agreement_extract.arr_unallocated_last_date = xip_unallocated_last_date
            arrears_by_agreement_extract.save()

        except:

            pass

        # UI : Build Context for redisplay of list
        # ========================================
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id)
        agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
        arrears_by_summary_extract = arrears_summary_arrear_level.objects.filter(ara_agreement_id=wip_agreement_id) \
            .order_by('-ara_due_date', )
        receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id) \
            .order_by('-ras_due_date', '-ras_effective_date')
        receipt_collections = receipt_record.objects.filter(rr_agreement_number=wip_agreement_id) \
            .order_by('-rr_receipt_created_on')

        # Get Regulated Status
        agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=wip_agreement_id).exists()
        if agreement_regulated:
            agreement_regulated_flag = True
        else:
            agreement_regulated_flag = False

        # Agreement Type
        if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
            agreement_type = 'Lease'
        else:
            agreement_type = 'HP'

        # Add Row Number
        row_index = 0
        for row in arrears_by_summary_extract:
            if row.ara_transactionsourceid in ['SP1', 'SP2', 'SP3', 'GO1', 'GO3']:
                row_index += 1
            row.row_index = row_index

        # Add Collections Row Number
        row2_index = receipt_record.objects.filter(rr_agreement_number=wip_agreement_id).count() + 1
        for row2 in receipt_collections:
            row2_index -= 1
            row2.row2_index = row2_index

        # Messaging in Session Variables
        # ------------------------------
        # Format Arrears Collected Message

        wip_new_message_text = None
        wip_arrears_collected_message_text = None
        wip_arrears_writtenoff_message_text = None

        if val_arrears_total_collected != 0:
            wip_arrears_collected_message_text = '<tr style="color: forestgreen">'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Agreement&nbsp;:&nbsp;'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text +  str(wip_agreement_id)
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Receipts Allocated to Arrears</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '£' + form_arrears_total_collected
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td></tr>'
            wip_new_message_text = wip_arrears_collected_message_text

        if val_arrears_total_adjustment != 0:
            wip_arrears_writtenoff_message_text = '<tr style="color: forestgreen">'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>Agreement&nbsp;:&nbsp;'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + str(wip_agreement_id)
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>Written Off Value</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '£' + form_arrears_total_adjustment
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '</td></tr>'
            if wip_new_message_text:
                wip_new_message_text = wip_new_message_text + wip_arrears_writtenoff_message_text
            else:
                wip_new_message_text = wip_arrears_writtenoff_message_text

        if wip_new_message_text:

            # Arrears by Agreement Messages
            wip_arrears_by_agreement_messages = request.session.get('arrears_by_agreement_messages')
            if not wip_arrears_by_agreement_messages:
                wip_arrears_by_agreement_messages = ''
            request.session['arrears_by_agreement_messages'] = wip_arrears_by_agreement_messages + wip_new_message_text

            # Arrears by Arrears Messages
            wip_arrears_by_arrears_messages = request.session.get('arrears_by_arrears_messages')
            if not wip_arrears_by_arrears_messages:
                wip_arrears_by_arrears_messages = ''
            request.session['arrears_by_arrears_messages'] = wip_arrears_by_arrears_messages + wip_new_message_text

        # Return to Template
        data['form_is_valid'] = True
        template_name = 'includes/partial_arrears_by_arrears_summary_content.html'
        context = {'agreement_detail': agreement_detail,
                   'agreement_customer': agreement_customer,
                   'arrears_summary_list': arrears_by_summary_extract,
                   'receipt_allocations': receipt_allocations,
                   'receipt_collections': receipt_collections,
                   'agreement_type': agreement_type,
                   'agreement_regulated_flag': agreement_regulated_flag}

        data['html_arrears_list'] = render_to_string(template_name, context)

    # GET Request
    # ===========
    else:

        # initialise values
        rental_arrears_value = 0
        rental_collected_value = 0
        rental_adjustment_value = 0
        rental_balance_value = 0
        return_description = 0
        bamf_arrears_value = 0
        bamf_collected_value = 0
        bamf_adjustment_value = 0
        bamf_balance_value = 0
        risk_arrears_value = 0
        risk_collected_value = 0
        risk_adjustment_value = 0
        risk_balance_value = 0
        bounce_arrears_value = 0
        bounce_collected_value = 0
        bounce_adjustment_value = 0
        bounce_balance_value = 0
        letter_arrears_value = 0
        letter_collected_value = 0
        letter_adjustment_value = 0
        letter_balance_value = 0
        visit_arrears_value = 0
        visit_collected_value = 0
        visit_adjustment_value = 0
        visit_balance_value = 0
        val_today = datetime.datetime.today().strftime('%Y-%m-%d')

        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id)
        agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
        agreement_billing_to_date = go_account_transaction_summary.objects.filter(agreementnumber=wip_agreement_id,
                                                                             transactiondate__lte=val_today) \
                                                                             .exclude(transactionsourceid='SP9')
        agreement_billing_totals = go_account_transaction_summary.objects.filter(agreementnumber=wip_agreement_id) \
                                                                            .exclude(transactionsourceid='SP9')

        # get the total of any unallocated receipts
        try:
            unallocated_receipts_total = receipt_allocations_by_agreement.objects.get(rag_agreement_id=wip_agreement_id)
            unallocated_receipts_total_val = unallocated_receipts_total.rag_unallocated_value_grossofvat
        except:
            unallocated_receipts_total_val = 0

        # Get Agreement Phase and Debt Due Date
        arrears_due_date = arrears_by_summary_extract.ara_due_date
        arrears_agreement_phase_id = arrears_by_summary_extract.ara_transactionsourceid

        if arrears_agreement_phase_id == 'SP1' or arrears_agreement_phase_id == 'GO1':
            arrears_agreement_phase = 'Primary'
        else:
            arrears_agreement_phase = 'Secondary'

        #  Get Billing to Date
        agreement_billing_to_date_dict = agreement_billing_to_date.aggregate(Sum('transgrosspayment'))
        if (agreement_billing_to_date_dict is not None) and \
                (agreement_billing_to_date_dict["transgrosspayment__sum"] is not None):
            agreement_billing_to_date_val = agreement_billing_to_date_dict["transgrosspayment__sum"]
        else:
            agreement_billing_to_date_val = 0

        #  Total Billing forecast for agreement
        agreement_billing_totals_dict = agreement_billing_totals.aggregate(Sum('transgrosspayment'))
        if (agreement_billing_totals_dict is not None) and \
                (agreement_billing_totals_dict["transgrosspayment__sum"] is not None) :
            agreement_billing_totals_val = agreement_billing_totals_dict["transgrosspayment__sum"]
        else:
            agreement_billing_totals_val = 0

        # Get Total Arrears for AGreement
        total_agreement_arrears_value = arrears_by_agreement_extract.arr_balance_value_grossofvat

        # Agreement % Totals for data widgets
        if agreement_billing_totals_val > 0:
            agreement_billing_to_date_percent = 0
            agreement_arrears_percent = 0
            unallocated_receipts_percent = 0
            agreement_billing_to_date_percent = (agreement_billing_to_date_val / agreement_billing_totals_val) * 100
            agreement_arrears_percent = (total_agreement_arrears_value / agreement_billing_totals_val) * 100
            unallocated_receipts_percent = (unallocated_receipts_total_val / agreement_billing_totals_val) * 100
        else:
            agreement_billing_to_date_percent = 0
            agreement_arrears_percent = 0
            unallocated_receipts_percent = 0

        # Get Regulated Status
        agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=wip_agreement_id).exists()
        if agreement_regulated:
            agreement_regulated_flag = True
        else:
            agreement_regulated_flag = False

        # Get Agreement Type
        if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
            agreement_type = 'Lease'
        else:
            agreement_type = 'HP'

        # TODO Implement Dataset procdessing rather than hard coded charge type retrieval
        arrears_by_detail_extract = arrears_detail_arrear_level.objects.select_related('ard_arrears_charge_type').\
                                            filter(ard_agreement_id=wip_agreement_id, ard_arrears_id=wip_arrears_id) \
                                            .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')

        for arrear_detail in arrears_by_detail_extract:

            # TODO Once PoC completed and verified, rationalise into Data Dictionary data sets.

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 100) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 200):
                # rental values
                rental_arrears_value = arrear_detail.ard_balance_value_grossofvat
                rental_collected_value = 0
                rental_adjustment_value = 0
                rental_balance_value = arrear_detail.ard_balance_value_grossofvat
                return_description = arrear_detail.ard_return_description

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 105) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 205):
                # BAMF values
                bamf_arrears_value = arrear_detail.ard_balance_value_grossofvat
                bamf_collected_value = 0
                bamf_adjustment_value = 0
                bamf_balance_value = arrear_detail.ard_balance_value_grossofvat

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 101) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 201):
                # RISK values
                risk_arrears_value = arrear_detail.ard_balance_value_grossofvat
                risk_collected_value = 0
                risk_adjustment_value = 0
                risk_balance_value = arrear_detail.ard_balance_value_grossofvat

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 102) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 202):
                # BOUNCE FEE values
                bounce_arrears_value = arrear_detail.ard_balance_value_grossofvat
                bounce_collected_value = 0
                bounce_adjustment_value = 0
                bounce_balance_value = arrear_detail.ard_balance_value_grossofvat

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 103) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 203):
                #LETTER FEE values
                letter_arrears_value = arrear_detail.ard_balance_value_grossofvat
                letter_collected_value = 0
                letter_adjustment_value = 0
                letter_balance_value = arrear_detail.ard_balance_value_grossofvat

            if (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 104) or \
                    (arrear_detail.ard_arrears_charge_type.arr_allocation_id == 204):
                # VISIT FEE values
                visit_arrears_value = arrear_detail.ard_balance_value_grossofvat
                visit_collected_value = 0
                visit_adjustment_value = 0
                visit_balance_value = arrear_detail.ard_balance_value_grossofvat

            arrears_total_collected = 0

        context = {'agreement': wip_agreement_id, 'arrear': wip_arrears_id,
                   'arrears_agreement_phase':arrears_agreement_phase,
                   'arrears_due_date': arrears_due_date,
                   'agreement_billing_totals_val': agreement_billing_totals_val,
                   'agreement_billing_to_date_val': agreement_billing_to_date_val,
                   'agreement_billing_to_date_percent' : agreement_billing_to_date_percent,
                   'total_agreement_arrears_value' : total_agreement_arrears_value,
                   'agreement_arrears_percent':  agreement_arrears_percent,
                   'unallocated_receipts_total_val': unallocated_receipts_total_val,
                   'unallocated_receipts_percent' : unallocated_receipts_percent,
                   'rental_arrears_value': rental_arrears_value,
                   'rental_collected_value':rental_collected_value,
                   'rental_adjustment_value':rental_adjustment_value,
                   'rental_balance_value': rental_balance_value,
                   'return_description': return_description,
                   'bamf_arrears_value': bamf_arrears_value,
                   'bamf_collected_value': bamf_collected_value,
                   'bamf_adjustment_value': bamf_adjustment_value,
                   'bamf_balance_value': bamf_balance_value,
                   'risk_arrears_value': risk_arrears_value,
                   'risk_collected_value': risk_collected_value,
                   'risk_adjustment_value': risk_adjustment_value,
                   'risk_balance_value': risk_balance_value,
                   'bounce_arrears_value': bounce_arrears_value,
                   'bounce_collected_value': bounce_collected_value,
                   'bounce_adjustment_value': bounce_adjustment_value,
                   'bounce_balance_value': bounce_balance_value,
                   'letter_arrears_value': letter_arrears_value,
                   'letter_collected_value': letter_collected_value,
                   'letter_adjustment_value': letter_adjustment_value,
                   'letter_balance_value': letter_balance_value,
                   'visit_arrears_value': visit_arrears_value,
                   'visit_collected_value': visit_collected_value,
                   'visit_adjustment_value': visit_adjustment_value,
                   'visit_balance_value': visit_balance_value,
                   'agreement_detail': agreement_detail,
                   'agreement_customer': agreement_customer,
                   'agreement_type': agreement_type,
                   'agreement_regulated_flag': agreement_regulated_flag,
                   'collection_agents': collection_agents_extract,
                   'current_agent': current_agent
                   }

        data['html_arrears_form'] = render_to_string(template_name, context, request=request)

    # return json response to arrear_update()
    return JsonResponse(data)


@login_required(login_url="signin")
def arrear_receipt_view_detail(request, ras_agreement_id, ras_arrears_id,
                                      ras_allocation_id, template_name):
    # initialise data dictionary
    data = dict()

    # retrieve and save incoming paramater data
    wip_agreement_id = ras_agreement_id
    wip_arrears_id = ras_arrears_id
    wip_allocation_id = ras_allocation_id

    # retrieve database objects
    arrears_by_agreement_extract = arrears_summary_agreement_level.objects.get(arr_agreement_id=wip_agreement_id)
    arrears_by_summary_extract = arrears_summary_arrear_level.objects.filter(ara_agreement_id=wip_agreement_id,
                                                                             ara_arrears_id=wip_arrears_id) \
        .order_by('-ara_due_date', ).first()

    val_transactionsourceid = arrears_by_summary_extract.ara_transactionsourceid
    wip_return_description = arrears_by_summary_extract.ara_return_description
    active_status = arrears_status.objects.get(arr_status_code='A')
    cancelled_status = arrears_status.objects.get(arr_status_code='X')
    val_today = datetime.datetime.today().strftime('%Y-%m-%d')

    # POST Request
    # ============
    if request.method == 'POST':

        # Retrieve Input from Form
        form_arrears_total_arrears = request.POST.get('arrears_total_arrears')
        form_arrears_total_collected = request.POST.get('arrears_total_collected')
        form_arrears_total_adjustment = request.POST.get('arrears_total_adjustment')
        form_arrears_total_balance = request.POST.get('arrears_total_balance')
        form_arrear_val_1 = request.POST.get('arrear_val_1')
        form_collected_val_1 = request.POST.get('collected_val_1')
        form_adjustment_val_1 = request.POST.get('adjustment_val_1')
        form_balance_val_1 = request.POST.get('balance_val_1')
        form_arrear_val_2 = request.POST.get('arrear_val_2')
        form_collected_val_2 = request.POST.get('collected_val_2')
        form_adjustment_val_2 = request.POST.get('adjustment_val_2')
        form_balance_val_2 = request.POST.get('balance_val_2')
        form_arrear_val_3 = request.POST.get('arrear_val_3')
        form_collected_val_3 = request.POST.get('collected_val_3')
        form_adjustment_val_3 = request.POST.get('adjustment_val_3')
        form_balance_val_3 = request.POST.get('balance_val_3')
        form_arrear_val_4 = request.POST.get('arrear_val_4')
        form_collected_val_4 = request.POST.get('collected_val_4')
        form_adjustment_val_4 = request.POST.get('adjustment_val_4')
        form_balance_val_4 = request.POST.get('balance_val_4')
        form_arrear_val_5 = request.POST.get('arrear_val_5')
        form_collected_val_5 = request.POST.get('collected_val_5')
        form_adjustment_val_5 = request.POST.get('adjustment_val_5')
        form_balance_val_5 = request.POST.get('balance_val_5')
        form_arrear_val_6 = request.POST.get('arrear_val_6')
        form_collected_val_6 = request.POST.get('collected_val_6')
        form_adjustment_val_6 = request.POST.get('adjustment_val_6')
        form_balance_val_6 = request.POST.get('balance_val_6')

        # remove comma separators from numeric
        str_arrears_total_arrears = form_arrears_total_arrears.replace(",", "")
        str_arrears_total_collected = form_arrears_total_collected.replace(",", "")
        str_arrears_total_adjustment = form_arrears_total_adjustment.replace(",", "")
        str_arrears_total_balance = form_arrears_total_balance.replace(",", "")
        str_arrear_val_1 = form_arrear_val_1.replace(",", "")
        str_collected_val_1 = form_collected_val_1.replace(",", "")
        str_adjustment_val_1 = form_adjustment_val_1.replace(",", "")
        str_balance_val_1 = form_balance_val_1.replace(",", "")
        str_arrear_val_2 = form_arrear_val_2.replace(",", "")
        str_collected_val_2 = form_collected_val_2.replace(",", "")
        str_adjustment_val_2 = form_adjustment_val_2.replace(",", "")
        str_balance_val_2 = form_balance_val_2.replace(",", "")
        str_arrear_val_3 = form_arrear_val_3.replace(",", "")
        str_collected_val_3 = form_collected_val_3.replace(",", "")
        str_adjustment_val_3 = form_adjustment_val_3.replace(",", "")
        str_balance_val_3 = form_balance_val_3.replace(",", "")
        str_arrear_val_4 = form_arrear_val_4.replace(",", "")
        str_collected_val_4 = form_collected_val_4.replace(",", "")
        str_adjustment_val_4 = form_adjustment_val_4.replace(",", "")
        str_balance_val_4 = form_balance_val_4.replace(",", "")
        str_arrear_val_5 = form_arrear_val_5.replace(",", "")
        str_collected_val_5 = form_collected_val_5.replace(",", "")
        str_adjustment_val_5 = form_adjustment_val_5.replace(",", "")
        str_balance_val_5 = form_balance_val_5.replace(",", "")
        str_arrear_val_6 = form_arrear_val_6.replace(",", "")
        str_collected_val_6 = form_collected_val_6.replace(",", "")
        str_adjustment_val_6 = form_adjustment_val_6.replace(",", "")
        str_balance_val_6 = form_balance_val_6.replace(",", "")

        # convert to float and then round
        val_arrears_total_arrears = round(floatify(str_arrears_total_arrears), 2)
        val_arrears_total_collected = round(floatify(str_arrears_total_collected), 2)
        val_arrears_total_adjustment = round(floatify(str_arrears_total_adjustment), 2)
        val_arrears_total_balance = round(floatify(str_arrears_total_balance), 2)
        rental_arrears_value = round(floatify(str_arrear_val_1), 2)
        rental_collected_value = round(floatify(str_collected_val_1), 2)
        rental_adjustment_value = round(floatify(str_adjustment_val_1), 2)
        rental_balance_value = round(floatify(str_balance_val_1), 2)
        bamf_arrears_value = round(floatify(str_arrear_val_2), 2)
        bamf_collected_value = round(floatify(str_collected_val_2), 2)
        bamf_adjustment_value = round(floatify(str_adjustment_val_2), 2)
        bamf_balance_value = round(floatify(str_balance_val_2), 2)
        risk_arrears_value = round(floatify(str_arrear_val_3), 2)
        risk_collected_value = round(floatify(str_collected_val_3), 2)
        risk_adjustment_value = round(floatify(str_adjustment_val_3), 2)
        risk_balance_value = round(floatify(str_balance_val_3), 2)
        bounce_arrears_value = round(floatify(str_arrear_val_4), 2)
        bounce_collected_value = round(floatify(str_collected_val_4), 2)
        bounce_adjustment_value = round(floatify(str_adjustment_val_4), 2)
        bounce_balance_value = round(floatify(str_balance_val_4), 2)
        letter_arrears_value = round(floatify(str_arrear_val_5), 2)
        letter_collected_value = round(floatify(str_collected_val_5), 2)
        letter_adjustment_value = round(floatify(str_adjustment_val_5), 2)
        letter_balance_value = round(floatify(str_balance_val_5), 2)
        visit_arrears_value = round(floatify(str_arrear_val_6), 2)
        visit_collected_value = round(floatify(str_collected_val_6), 2)
        visit_adjustment_value = round(floatify(str_adjustment_val_6), 2)
        visit_balance_value = round(floatify(str_balance_val_6), 2)


        # RECEIPTS : Cancel RECEIPT_ALLOCATIONS_BY_ARREARS object
        # =======================================================
        receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id,
                                                                            ras_arrears_id=wip_arrears_id,
                                                                            ras_allocation_id=wip_allocation_id)
        for receipt_allocation in receipt_allocations:

            receipt_allocation.ras_status = cancelled_status
            receipt_allocation.ras_agent_id = request.user
            receipt_allocation.ras_status_date = val_today
            receipt_allocation.save()


        # RECEIPTS : Cancel RECEIPT_ALLOCATIONS_BY_DETAIL objects
        # =======================================================
        receipt_allocation_details = receipt_allocations_by_detail.objects.filter(rad_agreement_id=wip_agreement_id,
                                                                                  rad_arrears_id=wip_arrears_id,
                                                                                  rad_allocation_id=wip_allocation_id)

        wip_dd_collected_val = 0
        wip_dd_adjusted_val = 0
        wip_fees_collected_val = 0
        wip_fees_adjusted_val = 0
        wip_due_date = None

        for receipt_allocation_detail in receipt_allocation_details:

            wip_due_date = receipt_allocation_detail.rad_due_date

            receipt_allocation_detail.rad_status = cancelled_status
            receipt_allocation_detail.rad_agent_id = request.user
            receipt_allocation_detail.rad_status_date = val_today
            receipt_allocation_detail.save()

            try:
                receipt_allocation_type = arrears_allocation_type.objects.get(id=receipt_allocation_detail.rad_allocation_charge_type_id)
                if not receipt_allocation_type.arr_allocation_value_gross:
                    wip_dd_collected_val = wip_dd_collected_val + receipt_allocation_detail.rad_collected_value_grossofvat
                    wip_dd_adjusted_val = wip_dd_adjusted_val + receipt_allocation_detail.rad_adjustment_value_grossofvat
                else:
                    wip_fees_collected_val = wip_fees_collected_val + receipt_allocation_detail.rad_collected_value_grossofvat
                    wip_fees_adjusted_val = wip_fees_adjusted_val + receipt_allocation_detail.rad_adjustment_value_grossofvat
            except:
                wip_dd_collected_val = wip_dd_collected_val + receipt_allocation_detail.rad_collected_value_grossofvat
                wip_dd_adjusted_val = wip_dd_adjusted_val + receipt_allocation_detail.rad_adjustment_value_grossofvat

        wip_history_date = datetime.date.today()
        if not isinstance(wip_history_date, datetime.datetime):
            my_time = datetime.datetime.min.time()
            wip_history_date = datetime.datetime.combine(wip_history_date, my_time)

        wip_due_date = wip_due_date.strftime('%d/%m/%Y')

        if wip_dd_collected_val != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '0',
                                  'Col',
                                  wip_dd_collected_val,
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'CANCELLED DD Collection for ' + wip_due_date)

        if wip_dd_adjusted_val != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '0',
                                  'Col',
                                  wip_dd_adjusted_val,
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'CANCELLED DD Adjustment for ' + wip_due_date)

        if wip_fees_collected_val != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '0',
                                  'Col',
                                  wip_fees_collected_val,
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'CANCELLED Bounce Fees Collection for ' + wip_due_date)

        if wip_fees_adjusted_val != 0:
            write_account_history(wip_agreement_id,
                                  wip_history_date,
                                  'GO9',
                                  '0',
                                  'Col',
                                  wip_fees_adjusted_val,
                                  'GROSS',
                                  0,
                                  0,
                                  None,
                                  'CANCELLED Bounce Fees  Adjustment for ' + wip_due_date)


        # RECEIPTS : Recalculate receipt allocations by agreement
        # ============================================
        allocated_collected_gross = 0
        allocated_collected_net = 0
        allocated_count = 0
        no_date = datetime.datetime.strptime('Jan 1 2000', '%b %d %Y').date()
        last_allocated_date = no_date
        last_unallocated_date = no_date

        # RECEIPTS : GET the new total of Receipt Allocations for the agreement
        # ==========================================================
        receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id)\
                                .exclude(ras_status__arr_status_code='X')
        for receipt_allocation in receipt_allocations:

            allocated_collected_gross += receipt_allocation.ras_collected_value_grossofvat
            allocated_collected_net += receipt_allocation.ras_collected_value_netofvat
            if receipt_allocation.ras_collected_value_grossofvat != 0:
                allocated_count += 1
                if receipt_allocation.ras_status_date > last_allocated_date:
                    last_allocated_date = receipt_allocation.ras_status_date

        # RECEIPTS : Amend/Write Receipt Allocations by Agreement
        # =======================================================
        try:
            receipt_allocations_by_agreement_obj = receipt_allocations_by_agreement.objects.get(
                rag_agreement_id=wip_agreement_id)
        except ObjectDoesNotExist:
            receipt_allocations_by_agreement_obj = None

        if receipt_allocations_by_agreement_obj:

            unallocated_value_netofvat = receipt_allocations_by_agreement_obj.rag_received_value_netofvat - allocated_collected_net
            unallocated_value_grossofvat = receipt_allocations_by_agreement_obj.rag_received_value_grossofvat - allocated_collected_gross
            if last_allocated_date != '2000-01-01':
                last_unallocated_date = last_allocated_date

            receipt_allocations_by_agreement_obj.rag_allocated_value_netofvat = allocated_collected_net
            receipt_allocations_by_agreement_obj.rag_allocated_value_grossofvat = allocated_collected_gross
            receipt_allocations_by_agreement_obj.rag_allocated_last_date = last_allocated_date
            receipt_allocations_by_agreement_obj.rag_allocated_count = allocated_count
            receipt_allocations_by_agreement_obj.rag_unallocated_value_netofvat = unallocated_value_netofvat
            receipt_allocations_by_agreement_obj.rag_unallocated_value_grossofvat = unallocated_value_grossofvat
            receipt_allocations_by_agreement_obj.rag_unallocated_last_date = last_unallocated_date
            receipt_allocations_by_agreement_obj.rag_agent_id = request.user
            receipt_allocations_by_agreement_obj.rag_status = active_status
            receipt_allocations_by_agreement_obj.rag_status_date = val_today
            receipt_allocations_by_agreement_obj.save()

        else:

            receipt_allocations_by_agreement.objects.create(
                rag_agreement_id=wip_agreement_id,
                rag_customernumber=arrears_by_agreement_extract.arr_customernumber,
                rag_customercompanyname=arrears_by_agreement_extract.arr_customercompanyname,
                rag_received_count=1,
                rag_received_value_netofvat=0,
                rag_received_value_grossofvat=0,
                rag_received_last_date=val_today,
                rag_allocated_count=0,
                rag_allocated_value_netofvat=0,
                rag_allocated_value_grossofvat=0,
                rag_allocated_last_date=val_today,
                rag_unallocated_value_netofvat=0,
                rag_unallocated_value_grossofvat=0,
                rag_unallocated_last_date=val_today,
                rag_agent_id=request.user,
                rag_status=active_status,
                rag_status_date=val_today
            )

        # ARREARS: Write/Update arrears detail level
        # ==========================================
        arrears_by_detail_extract = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                               ard_arrears_id=wip_arrears_id) \
            .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')

        for arrear_detail in arrears_by_detail_extract:

            sum_arrears_value_netofvat = 0
            sum_arrears_value_grossofvat = 0
            sum_collected_value_netofvat = 0
            sum_collected_value_grossofvat = 0
            sum_collected_last_date = 0
            sum_writtenoff_value_netofvat = 0
            sum_writtenoff_value_grossofvat = 0
            sum_balance_value_netofvat = 0
            sum_balance_value_grossofvat = 0
            val_receipt_allocated = False

            receipt_allocations_by_detail_extract = receipt_allocations_by_detail.objects. \
                filter(rad_agreement_id=arrear_detail.ard_agreement_id,
                       rad_arrears_id=arrear_detail.ard_arrears_id,
                       rad_allocation_charge_type_id=arrear_detail.ard_arrears_charge_type_id). \
                exclude(rad_status__arr_status_code='X').order_by('rad_allocation_id')

            for receipt_allocation in receipt_allocations_by_detail_extract:

                val_receipt_allocated = True
                sum_collected_value_netofvat += receipt_allocation.rad_collected_value_netofvat
                sum_collected_value_grossofvat += receipt_allocation.rad_collected_value_grossofvat
                sum_writtenoff_value_netofvat += receipt_allocation.rad_adjustment_value_netofvat
                sum_writtenoff_value_grossofvat += receipt_allocation.rad_adjustment_value_grossofvat
                val_status_date = receipt_allocation.rad_status_date
                val_agent_id = receipt_allocation.rad_agent_id
                val_status = receipt_allocation.rad_status

            if val_receipt_allocated:
                arrear_detail.ard_agent_id = val_agent_id
                arrear_detail.ard_status = val_status
                arrear_detail.ard_status_date = val_status_date

            arrear_detail.ard_collected_value_netofvat = sum_collected_value_netofvat
            arrear_detail.ard_collected_value_grossofvat = sum_collected_value_grossofvat
            arrear_detail.ard_writtenoff_value_netofvat = sum_writtenoff_value_netofvat
            arrear_detail.ard_writtenoff_value_grossofvat = sum_writtenoff_value_grossofvat
            arrear_detail.ard_balance_value_netofvat = arrear_detail.ard_arrears_value_netofvat \
                                                       - sum_collected_value_netofvat \
                                                       - sum_writtenoff_value_netofvat
            arrear_detail.ard_balance_value_grossofvat = arrear_detail.ard_arrears_value_grossofvat \
                                                         - sum_collected_value_grossofvat \
                                                         - sum_writtenoff_value_grossofvat
            arrear_detail.save()

        # ARREARS: Write/Update arrears at ARREARS level
        # ==============================================
        try:

            # Get the Arrears level object to be updated
            arrears_by_arrears_extract = arrears_summary_arrear_level.objects.get(ara_agreement_id=wip_agreement_id,
                                                                                  ara_arrears_id=wip_arrears_id)

            val_collected_value_netofvat = 0
            val_collected_value_grossofvat = 0
            val_collected_count = 0
            val_writtenoff_value_netofvat = 0
            val_writtenoff_value_grossofvat = 0
            val_writtenoff_count = 0
            val_balance_value_netofvat = 0
            val_balance_value_grossofvat = 0

            if arrears_by_arrears_extract:

                # Now get and sum all arrear details for arrears_id
                arrears_by_detail_extract = arrears_detail_arrear_level.objects.filter(
                    ard_agreement_id=wip_agreement_id,
                    ard_arrears_id=wip_arrears_id) \
                    .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')

                # Sum values
                try:
                    tuple_retrieved_aggregates = arrears_by_detail_extract.aggregate(
                        Sum('ard_collected_value_netofvat'),
                        Sum('ard_collected_value_grossofvat'),
                        Sum('ard_writtenoff_value_netofvat'),
                        Sum('ard_writtenoff_value_grossofvat'))
                    if tuple_retrieved_aggregates is not None:
                        # if tuple_retrieved_aggregates('ard_collected_value_netofvat__sum') != 0:
                        val_collected_value_netofvat = tuple_retrieved_aggregates['ard_collected_value_netofvat__sum']

                        # if tuple_retrieved_aggregates('ard_collected_value_grossofvat__sum') != 0:
                        val_collected_value_grossofvat = tuple_retrieved_aggregates[
                            'ard_collected_value_grossofvat__sum']

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_netofvat__sum') != 0:
                        val_writtenoff_value_netofvat = tuple_retrieved_aggregates["ard_writtenoff_value_netofvat__sum"]

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_grossofvat__sum') != 0:
                        val_writtenoff_value_grossofvat = tuple_retrieved_aggregates[
                            'ard_writtenoff_value_grossofvat__sum']

                except:
                    pass

            val_balance_value_netofvat = arrears_by_arrears_extract.ara_arrears_value_netofvat - \
                                         val_collected_value_netofvat - val_writtenoff_value_netofvat

            val_balance_value_grossofvat = arrears_by_arrears_extract.ara_arrears_value_grossofvat - \
                                           val_collected_value_grossofvat - val_writtenoff_value_grossofvat

            arrears_by_arrears_extract.ara_collected_value_netofvat = val_collected_value_netofvat
            arrears_by_arrears_extract.ara_collected_value_grossofvat = val_collected_value_grossofvat
            arrears_by_arrears_extract.ara_collected_count = val_collected_count
            arrears_by_arrears_extract.ara_writtenoff_value_netofvat = val_writtenoff_value_netofvat
            arrears_by_arrears_extract.ara_writtenoff_value_grossofvat = val_writtenoff_value_grossofvat
            arrears_by_arrears_extract.ara_writtenoff_count = val_writtenoff_count
            arrears_by_arrears_extract.ara_balance_value_netofvat = val_balance_value_netofvat
            arrears_by_arrears_extract.ara_balance_value_grossofvat = val_balance_value_grossofvat
            arrears_by_arrears_extract.ara_status_date = val_today
            arrears_by_arrears_extract.save()

        except:

            pass

        # ARREARS: Write/Update arrears at AGREEMENT level
        # ================================================
        try:

            # Get the Agreement level object to be updated
            arrears_by_agreement_extract = arrears_summary_agreement_level.objects.get(
                arr_agreement_id=wip_agreement_id)

            val_collected_value_netofvat = 0
            val_collected_value_grossofvat = 0
            val_collected_count = 0
            val_writtenoff_value_netofvat = 0
            val_writtenoff_value_grossofvat = 0
            val_writtenoff_count = 0
            val_balance_value_netofvat = 0
            val_balance_value_grossofvat = 0

            if arrears_by_agreement_extract:

                # Now get and sum all arrear details for arrears_id
                arrears_by_arrears_extract = arrears_summary_arrear_level.objects.filter(
                    ara_agreement_id=wip_agreement_id) \
                    .order_by('-ara_due_date', 'ara_arrears_id')

                # Sum values
                try:
                    tuple_retrieved_aggregates = arrears_by_arrears_extract.aggregate(
                        Sum('ara_collected_value_netofvat'),
                        Sum('ara_collected_value_grossofvat'),
                        Sum('ara_writtenoff_value_netofvat'),
                        Sum('ara_writtenoff_value_grossofvat'))
                    if tuple_retrieved_aggregates is not None:
                        # if tuple_retrieved_aggregates('ard_collected_value_netofvat__sum') != 0:
                        val_collected_value_netofvat = tuple_retrieved_aggregates['ara_collected_value_netofvat__sum']

                        # if tuple_retrieved_aggregates('ard_collected_value_grossofvat__sum') != 0:
                        val_collected_value_grossofvat = tuple_retrieved_aggregates[
                            'ara_collected_value_grossofvat__sum']

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_netofvat__sum') != 0:
                        val_writtenoff_value_netofvat = tuple_retrieved_aggregates["ara_writtenoff_value_netofvat__sum"]

                        # if tuple_retrieved_aggregates('ard_writtenoff_value_grossofvat__sum') != 0:
                        val_writtenoff_value_grossofvat = tuple_retrieved_aggregates[
                            'ara_writtenoff_value_grossofvat__sum']

                except:
                    pass

            # Get Unallocated receipts
            unallocated_by_agreement = receipt_allocations_by_agreement.objects.filter(
                rag_agreement_id=wip_agreement_id).first()
            if unallocated_by_agreement:
                xip_unallocated_value_netofvat = unallocated_by_agreement.rag_unallocated_value_netofvat
                xip_unallocated_value_grossofvat = unallocated_by_agreement.rag_unallocated_value_grossofvat
                xip_unallocated_last_date = unallocated_by_agreement.rag_unallocated_last_date
            else:
                xip_unallocated_value_netofvat = 0
                xip_unallocated_value_grossofvat = 0
                xip_unallocated_last_date = val_today

            val_balance_value_netofvat = arrears_by_agreement_extract.arr_arrears_value_netofvat - \
                                         val_collected_value_netofvat - val_writtenoff_value_netofvat

            val_balance_value_grossofvat = arrears_by_agreement_extract.arr_arrears_value_grossofvat - \
                                           val_collected_value_grossofvat - val_writtenoff_value_grossofvat

            arrears_by_agreement_extract.arr_collected_value_netofvat = val_collected_value_netofvat
            arrears_by_agreement_extract.arr_collected_value_grossofvat = val_collected_value_grossofvat
            arrears_by_agreement_extract.arr_collected_count = val_collected_count
            arrears_by_agreement_extract.arr_writtenoff_value_netofvat = val_writtenoff_value_netofvat
            arrears_by_agreement_extract.arr_writtenoff_value_grossofvat = val_writtenoff_value_grossofvat
            arrears_by_agreement_extract.arr_writtenoff_count = val_writtenoff_count
            arrears_by_agreement_extract.arr_balance_value_netofvat = val_balance_value_netofvat
            arrears_by_agreement_extract.arr_balance_value_grossofvat = val_balance_value_grossofvat
            arrears_by_agreement_extract.arr_status_date = val_today
            arrears_by_agreement_extract.arr_unallocated_value_netofvat = xip_unallocated_value_netofvat
            arrears_by_agreement_extract.arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat
            arrears_by_agreement_extract.arr_unallocated_last_date = xip_unallocated_last_date
            arrears_by_agreement_extract.save()

        except:

            pass

        # UI : Build Context for redisplay of list
        # ========================================
        arrears_by_summary_extract_list = arrears_summary_arrear_level.objects.filter(ara_agreement_id=wip_agreement_id) \
            .order_by('-ara_due_date', )
        arrears_by_detail_extract = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id) \
            .order_by('-ard_due_date', 'ard_arrears_id', 'ard_arrears_charge_type_id')
        receipt_allocations = receipt_allocations_by_arrears.objects.filter(ras_agreement_id=wip_agreement_id) \
            .order_by('-ras_due_date', '-ras_effective_date')

        # Add Row Number
        row_index = 0
        for row in arrears_by_summary_extract_list:
            if row.ara_transactionsourceid in ['SP1', 'SP2', 'SP3', 'GO1', 'GO3']:
                row_index += 1
            row.row_index = row_index

        # Messaging in Session Variables
        # ------------------------------
        # Format Arrears Collected Message

        wip_new_message_text = None
        wip_arrears_collected_message_text = None
        wip_arrears_writtenoff_message_text = None

        if val_arrears_total_collected != 0:
            wip_arrears_collected_message_text = '<tr style="color: #fd3259 !important;">'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Agreement&nbsp;:&nbsp;'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + str(wip_agreement_id)
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Receipts Allocated to Arrears</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '£' + form_arrears_total_collected
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>CANCELLED</td></tr>'
            wip_new_message_text = wip_arrears_collected_message_text

        if val_arrears_total_adjustment != 0:
            wip_arrears_writtenoff_message_text = '<tr style="color: #fd3259 !important;">'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>Agreement&nbsp;:&nbsp;'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + str(wip_agreement_id)
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>Written Off Value</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '£' + form_arrears_total_adjustment
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '</td>'
            wip_arrears_writtenoff_message_text = wip_arrears_writtenoff_message_text + '<td>CANCELLED</td></tr>'
            if wip_new_message_text:
                wip_new_message_text = wip_new_message_text + wip_arrears_writtenoff_message_text
            else:
                wip_new_message_text = wip_arrears_writtenoff_message_text

        if wip_new_message_text:

            # Arrears by Agreement Messages
            wip_arrears_by_agreement_messages = request.session.get('arrears_by_agreement_messages')
            if not wip_arrears_by_agreement_messages:
                wip_arrears_by_agreement_messages = ''
            request.session[
                'arrears_by_agreement_messages'] = wip_arrears_by_agreement_messages + wip_new_message_text

            # Arrears by Arrears Messages
            wip_arrears_by_arrears_messages = request.session.get('arrears_by_arrears_messages')
            if not wip_arrears_by_arrears_messages:
                wip_arrears_by_arrears_messages = ''
            request.session['arrears_by_arrears_messages'] = wip_arrears_by_arrears_messages + wip_new_message_text

        data['form_is_valid'] = True
        template_name = 'includes/partial_arrears_by_arrears_summary_list.html'
        context = {'arrears_summary_list': arrears_by_summary_extract_list,
                   'arrears_detail_list': arrears_by_detail_extract,
                   'receipt_allocations': receipt_allocations}

        data['html_arrears_list'] = render_to_string(template_name, context)

    # GET Request
    # ===========
    else:
        # initialise values
        rental_arrears_value = 0
        rental_collected_value = 0
        rental_adjustment_value = 0
        rental_balance_value = 0
        return_description = 0
        bamf_arrears_value = 0
        bamf_collected_value = 0
        bamf_adjustment_value = 0
        bamf_balance_value = 0
        risk_arrears_value = 0
        risk_collected_value = 0
        risk_adjustment_value = 0
        risk_balance_value = 0
        bounce_arrears_value = 0
        bounce_collected_value = 0
        bounce_adjustment_value = 0
        bounce_balance_value = 0
        letter_arrears_value = 0
        letter_collected_value = 0
        letter_adjustment_value = 0
        letter_balance_value = 0
        visit_arrears_value = 0
        visit_collected_value = 0
        visit_adjustment_value = 0
        visit_balance_value = 0
        created_on = datetime.datetime.today().strftime('%m/%d/%Y')
        created_by = ''
        val_today = datetime.datetime.today().strftime('%Y-%m-%d')

        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id)
        agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
        agreement_billing_to_date = go_account_transaction_summary.objects.filter(agreementnumber=wip_agreement_id,
                                                                                  transactiondate__lte=val_today) \
            .exclude(transactionsourceid='SP9')
        agreement_billing_totals = go_account_transaction_summary.objects.filter(agreementnumber=wip_agreement_id) \
            .exclude(transactionsourceid='SP9')

        # get the total of any unallocated receipts
        try:
            unallocated_receipts_total = receipt_allocations_by_agreement.objects.get(rag_agreement_id=wip_agreement_id)
            unallocated_receipts_total_val = unallocated_receipts_total.rag_unallocated_value_grossofvat
        except:
            unallocated_receipts_total_val = 0

        # Get Agreement Phase and Debt Due Date
        arrears_due_date = arrears_by_summary_extract.ara_due_date
        arrears_agreement_phase_id = arrears_by_summary_extract.ara_transactionsourceid

        if arrears_agreement_phase_id == 'SP1' or arrears_agreement_phase_id == 'GO1':
            arrears_agreement_phase = 'Primary'
        else:
            arrears_agreement_phase = 'Secondary'

        #  Get Billing to Date
        agreement_billing_to_date_dict = agreement_billing_to_date.aggregate(Sum('transgrosspayment'))
        if (agreement_billing_to_date_dict is not None) and \
                (agreement_billing_to_date_dict["transgrosspayment__sum"] is not None):
            agreement_billing_to_date_val = agreement_billing_to_date_dict["transgrosspayment__sum"]
        else:
            agreement_billing_to_date_val = 0

        #  Total Billing forecast for agreement
        agreement_billing_totals_dict = agreement_billing_totals.aggregate(Sum('transgrosspayment'))
        if (agreement_billing_totals_dict is not None) and \
                (agreement_billing_totals_dict["transgrosspayment__sum"] is not None):
            agreement_billing_totals_val = agreement_billing_totals_dict["transgrosspayment__sum"]
        else:
            agreement_billing_totals_val = 0

        # Get Total Arrears for AGreement
        total_agreement_arrears_value = arrears_by_agreement_extract.arr_balance_value_grossofvat

        # Agreement % Totals for data widgets
        if agreement_billing_totals_val > 0:
            agreement_billing_to_date_percent = 0
            agreement_arrears_percent = 0
            unallocated_receipts_percent = 0
            agreement_billing_to_date_percent = (agreement_billing_to_date_val / agreement_billing_totals_val) * 100
            agreement_arrears_percent = (total_agreement_arrears_value / agreement_billing_totals_val) * 100
            unallocated_receipts_percent = (unallocated_receipts_total_val / agreement_billing_totals_val) * 100
        else:
            agreement_billing_to_date_percent = 0
            agreement_arrears_percent = 0
            unallocated_receipts_percent = 0

        # Get Regulated Status
        agreement_regulated = ncf_regulated_agreements.objects.filter(ra_agreement_id=wip_agreement_id).exists()
        if agreement_regulated:
            agreement_regulated_flag = True
        else:
            agreement_regulated_flag = False

        # Get Agreement Type
        if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
            agreement_type = 'Lease'
        else:
            agreement_type = 'HP'

        # TODO Implement Dataset procdessing rather than hard coded charge type retrieval
        allocations_by_detail_extract = receipt_allocations_by_detail.objects.select_related('rad_allocation_charge_type'). \
            filter(rad_agreement_id=wip_agreement_id, rad_arrears_id=wip_arrears_id, rad_allocation_id=wip_allocation_id) \
            .order_by('-rad_due_date', 'rad_arrears_id', 'rad_allocation_charge_type_id')

        for allocation_detail in allocations_by_detail_extract:

            # TODO Once PoC completed and verified, rationalise into Data Dictionary data sets.

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 100) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 200):
                # rental values
                rental_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                rental_collected_value = allocation_detail.rad_collected_value_grossofvat
                rental_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                rental_balance_value = allocation_detail.rad_balance_value_grossofvat
                return_description = wip_return_description

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 105) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 205):
                # BAMF values
                bamf_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                bamf_collected_value = allocation_detail.rad_collected_value_grossofvat
                bamf_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                bamf_balance_value = allocation_detail.rad_balance_value_grossofvat

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 101) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 201):
                # RISK values
                risk_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                risk_collected_value = allocation_detail.rad_collected_value_grossofvat
                risk_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                risk_balance_value = allocation_detail.rad_balance_value_grossofvat

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 102) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 202):
                # BOUNCE FEE values
                bounce_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                bounce_collected_value = allocation_detail.rad_collected_value_grossofvat
                bounce_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                bounce_balance_value = allocation_detail.rad_balance_value_grossofvat

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 103) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 203):
                # LETTER FEE values
                letter_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                letter_collected_value = allocation_detail.rad_collected_value_grossofvat
                letter_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                letter_balance_value = allocation_detail.rad_balance_value_grossofvat

            if (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 104) or \
                    (allocation_detail.rad_allocation_charge_type.arr_allocation_id == 204):
                # VISIT FEE values
                visit_arrears_value = allocation_detail.rad_arrears_value_grossofvat
                visit_collected_value = allocation_detail.rad_collected_value_grossofvat
                visit_adjustment_value = allocation_detail.rad_adjustment_value_grossofvat
                visit_balance_value = allocation_detail.rad_balance_value_grossofvat

            created_on = allocation_detail.rad_status_date
            created_by = allocation_detail.rad_agent_id
            cancelled_flag = allocation_detail.rad_status.arr_status_code

        context = {'agreement': wip_agreement_id, 'arrear': wip_arrears_id, 'allocation':wip_allocation_id,
                   'arrears_agreement_phase': arrears_agreement_phase,
                   'arrears_due_date': arrears_due_date,
                   'agreement_billing_totals_val': agreement_billing_totals_val,
                   'agreement_billing_to_date_val': agreement_billing_to_date_val,
                   'agreement_billing_to_date_percent': agreement_billing_to_date_percent,
                   'total_agreement_arrears_value': total_agreement_arrears_value,
                   'agreement_arrears_percent': agreement_arrears_percent,
                   'unallocated_receipts_total_val': unallocated_receipts_total_val,
                   'unallocated_receipts_percent': unallocated_receipts_percent,
                   'rental_arrears_value': rental_arrears_value,
                   'rental_collected_value': rental_collected_value,
                   'rental_adjustment_value': rental_adjustment_value,
                   'rental_balance_value': rental_balance_value,
                   'return_description': return_description,
                   'bamf_arrears_value': bamf_arrears_value,
                   'bamf_collected_value': bamf_collected_value,
                   'bamf_adjustment_value': bamf_adjustment_value,
                   'bamf_balance_value': bamf_balance_value,
                   'risk_arrears_value': risk_arrears_value,
                   'risk_collected_value': risk_collected_value,
                   'risk_adjustment_value': risk_adjustment_value,
                   'risk_balance_value': risk_balance_value,
                   'bounce_arrears_value': bounce_arrears_value,
                   'bounce_collected_value': bounce_collected_value,
                   'bounce_adjustment_value': bounce_adjustment_value,
                   'bounce_balance_value': bounce_balance_value,
                   'letter_arrears_value': letter_arrears_value,
                   'letter_collected_value': letter_collected_value,
                   'letter_adjustment_value': letter_adjustment_value,
                   'letter_balance_value': letter_balance_value,
                   'visit_arrears_value': visit_arrears_value,
                   'visit_collected_value': visit_collected_value,
                   'visit_adjustment_value': visit_adjustment_value,
                   'visit_balance_value': visit_balance_value,
                   'agreement_detail': agreement_detail,
                   'agreement_customer': agreement_customer,
                   'agreement_type': agreement_type,
                   'agreement_regulated_flag': agreement_regulated_flag,
                   'created_on': created_on,
                   'created_by': created_by,
                   'cancelled_flag': cancelled_flag
                   }

        data['html_arrears_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url="signin")
def arrear_update(request, ara_agreement_id, ara_arrears_id):

    # return json response as received from arrear_save_form
    return arrear_save_form(request, ara_agreement_id, ara_arrears_id, 'includes/partial_arrear_update.html')


@login_required(login_url="signin")
def arrear_receipt_view(request, ras_agreement_id, ras_arrears_id, ras_allocation_id):

    # return json response as received from arrear_save_form
    return arrear_receipt_view_detail(request, ras_agreement_id, ras_arrears_id,
                                      ras_allocation_id, 'includes/partial_view_modal.html')


# Check that value is number
def floatify(arg_value):
    try:
        return_value = float(arg_value)
    except ValueError:
        return_value = float(0.0)

    return return_value