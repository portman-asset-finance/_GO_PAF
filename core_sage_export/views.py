import json
import uuid
import time
import datetime
import traceback

from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .functions import generate_split_sage_batch_reference, calculate_batch_forecast, build_sage_transactions_from_batch

from .models import SageBatchHeaders, SageBatchDetails, SageBatchTransactions, SageBatchLock

from core_dd_drawdowns.models import DrawDown

from django.http import HttpResponse
from xlsxwriter.workbook import Workbook
import decimal, io, datetime


@login_required(login_url='signin')
def view_batch(request, sage_batch_ref):
    """
    Returns data for a specific batch header id
    :param request:
    :param _id:
    :return:
    """

    #
    time.sleep(0.1)  # <- NEEDED FOR LOCKING MECHANISM!
    context = {}

    query = {
        'include': 1,
        'sage_batch_ref': sage_batch_ref
    }

    old_sage_batch_header = SageBatchHeaders.objects.get(sage_batch_ref=sage_batch_ref)

    try:
        sage_batch_lock = SageBatchLock.objects.filter(sage_batch_header=old_sage_batch_header, released__isnull=True).order_by('-id')[0]
    except:
        sage_batch_lock = False

    if sage_batch_lock:
        context['sage_batch_lock'] = sage_batch_lock
        context['sage_batch_lock_check'] = True
    else:
        sage_batch_lock_session_id = str(uuid.uuid1())
        sage_batch_lock = SageBatchLock(sage_batch_header=old_sage_batch_header, user=request.user, session_id=sage_batch_lock_session_id)
        sage_batch_lock.save()

    if SageBatchHeaders.processed:
        sage_batch_lock = False

    context['sage_batch_lock'] = sage_batch_lock

    if request.method == 'POST':

        removed_transactions_filter = SageBatchTransactions.objects.filter(remove=True)
        removed_transactions_filter_wip = removed_transactions_filter

        if removed_transactions_filter.count() > 0:

            # Create new batch header
            new_batch_record = {
                'sage_batch_ref': generate_split_sage_batch_reference(sage_batch_ref),
                'status': 'NOT RECORDED',
                'sage_batch_type': 'Split Due Day Batch',
                'processed': datetime.datetime.now(),
                'batch_header': old_sage_batch_header.batch_header,
                'sage_batch_date': old_sage_batch_header.sage_batch_date
            }
            new_sage_batch_header = SageBatchHeaders(**new_batch_record)
            new_sage_batch_header.save()

            removed_transactions_filter.update(sage_batch_ref=new_sage_batch_header.sage_batch_ref, remove=False)
            wip_removed_transactions_filter = SageBatchTransactions.objects.filter(sage_batch_ref=new_sage_batch_header.sage_batch_ref)

            aggregate_amount = wip_removed_transactions_filter.filter(sage_batch_ref=new_sage_batch_header.sage_batch_ref).aggregate(Sum('sage_batch_netpayment'))
            wip_aggregate_amount = aggregate_amount.get("sage_batch_netpayment__sum", 0) or 0

            # aggregate_amount = removed_transactions_filter.aggregate(Sum('sage_batch_netpayment'))
            new_sage_batch_header.total_debit_amount = wip_aggregate_amount
            new_sage_batch_header.total_credit_amount = -wip_aggregate_amount
            new_sage_batch_header.save()

        old_removed_transactions_filter = SageBatchTransactions.objects.filter(sage_batch_ref=sage_batch_ref)
        old_aggregate_amount = old_removed_transactions_filter.filter(sage_batch_ref=sage_batch_ref).aggregate(Sum('sage_batch_netpayment'))
        old_wip_aggregate_amount = old_aggregate_amount.get("sage_batch_netpayment__sum", 0) or 0

        old_sage_batch_header.status = 'RECORDED'
        old_sage_batch_header.total_debit_amount = old_wip_aggregate_amount
        old_sage_batch_header.total_credit_amount = -old_wip_aggregate_amount
        old_sage_batch_header.save()

        return redirect('core_sage_export:view_batches')

    # Filtering
    filters = ('agreementnumber__contains', 'sage_batch_customercompany__contains', 'sage_batch_agreementdefname',
               'transactiondate', 'sage_batch_typedesc', 'transactionsourceid__contains')
    for k in filters:
        if request.GET.get(k):
            query[k] = request.GET[k]
            context['filter'] = query

    transactions_for_batch = SageBatchTransactions.objects.filter(**query)
    context['filtered_count'] = transactions_for_batch.count()

    transactions_for_batch_total = SageBatchTransactions.objects.filter(remove=False, sage_batch_ref=sage_batch_ref).aggregate(Sum('sage_batch_netpayment'))
    wip_transactions_for_batch = transactions_for_batch_total["sage_batch_netpayment__sum"]

    context.update({
        'wip_transactions_for_batch': wip_transactions_for_batch,
        'sage_batch_ref': sage_batch_ref,
        'sage_batch_header': old_sage_batch_header,
        'forecast': calculate_batch_forecast(sage_batch_ref)
    })

    paginator = Paginator(transactions_for_batch, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    context['records'] = pub

    if query.get('ddi_status'):
        query['ddi_status'] = '{}'.format(query['ddi_status'])

    context['query'] = query
    context['include'] = request.GET.get('include')

    return render(request, 'sage_batch_screen.html', context)


@login_required(login_url='signin')
def view_batches(request,):
    """
    NUMBER 1

    Renders a list of historic batches
    :param request:
    :return:
    """

    template = 'sage_batch_list.html'

    context = {}

    query = {}
    for k in ('reference__contains', 'due_date', 'total_amount', 'status'):
        if request.GET.get(k):
            query[k] = request.GET[k]

    if query:
        recs = SageBatchHeaders.objects.filter(**query).order_by('-id')
    else:
        recs = SageBatchHeaders.objects.all().order_by('-id')

    query2 = {}
    # bh_rec = SageBatchHeaders.objects.get(sage_batch_ref=sage_batch_ref)
    if query2:
        recs2 = SageBatchDetails.objects.filter(**query2).order_by('-id')
    else:
        recs2 = SageBatchDetails.objects.all().order_by('-id')

    paginator = Paginator(recs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    batch_numbers = {}
    for rec in pub:
        batch_numbers[rec.sage_batch_ref] = DrawDown.objects.filter(status='RECEIVED',
                                                                    batch_header=rec.batch_header,).count()
    context['batch_numbers'] = batch_numbers

    context['records'] = pub
    context['filter'] = query
    context['records2'] = recs2
    context['filter2'] = query2

    return render(request, template, context)


@login_required(login_url='signin')
def view_details(request, sage_batch_ref):
    """
    Renders a list of historic batches
    :param request:
    :return:
    """

    template = 'sage_batch_detail.html'

    # bh_rec = SageBatchDetails.get(sage_batch_ref=sage_batch_ref)

    context = {}

    query2 = {}
    # for k in ('reference__contains', 'due_date', 'total_amount', 'status'):
    #     if request.GET.get(k):
    #         query[k] = request.GET[k]
    #
    if query2:
        recs = SageBatchDetails.objects.filter(sage_batch_ref_id=sage_batch_ref).order_by('-id')
    else:
        recs = SageBatchDetails.objects.filter(sage_batch_ref_id=sage_batch_ref).order_by('-id')

    # paginator = Paginator(recs, 15)
    # page = request.GET.get('page')
    # try:
    #     pub = paginator.page(page)
    # except PageNotAnInteger:
    #     pub = paginator.page(1)
    # except EmptyPage:
    #     pub = paginator.page(paginator.num_pages)

    context['records'] = recs
    context['filter'] = query2

    return render(request, template, context)


@login_required(login_url='sigin')
def split_transaction(request, transaction_id):

    update = {}
    if request.GET.get('to_be_removed'):
        update['remove'] = True
    if request.GET.get('remove_to_be_removed'):
        update['remove'] = False

    transactions_for_batch = SageBatchTransactions.objects.filter(id=transaction_id)
    transactions_for_batch.update(**update)

    context = {}
    transactions_for_batch_total = SageBatchTransactions.objects.filter(remove=False, sage_batch_ref=transactions_for_batch[0].sage_batch_ref).aggregate(Sum('sage_batch_netpayment'))

    context['total_amount'] = transactions_for_batch_total['sage_batch_netpayment__sum']
    if context['total_amount']:
        context['total_amount'] = '{:,.2f}'.format(context['total_amount'])

    context['forecast'] = calculate_batch_forecast(transactions_for_batch[0].sage_batch_ref)

    return JsonResponse(context)


@login_required(login_url='sigin')
def split_transactions(request, sage_batch_ref):

    context = {}

    query = {
        'include': 1,
        'sage_batch_ref': sage_batch_ref
    }

    save_the_click = True

    action = 'include'
    value = True
    if request.GET.get('to_be_removed'):
        action = 'remove'
        save_the_click = False
    if request.GET.get('remove_to_be_removed'):
        action = 'remove'
        value = False

    # Filtering
    filtering = False
    filters = ('agreementnumber__contains', 'sage_batch_customercompany__contains', 'sage_batch_agreementdefname',
               'transactiondate', 'sage_batch_typedesc', 'transactionsourceid__contains')
    for k in filters:
        if request.GET.get(k):
            filtering = True
            query[k] = request.GET[k]
            context['filter'] = query

    transactions_for_batch = SageBatchTransactions.objects.filter(**query)
    context['filtered_count'] = transactions_for_batch.count()
    transactions_for_batch.update(**{action: value})

    transactions_for_batch_total = SageBatchTransactions.objects.filter(remove=False, sage_batch_ref=sage_batch_ref).aggregate(Sum('sage_batch_netpayment'))
    context['total_amount'] = transactions_for_batch_total['sage_batch_netpayment__sum']
    if context['total_amount']:
        context['total_amount'] = '{:,.2f}'.format(context['total_amount'])

    if not filtering:
        sage_batch_header = SageBatchHeaders.objects.get(sage_batch_ref=sage_batch_ref)
        sage_batch_header.save_the_click = save_the_click
        sage_batch_header.save()

    context['forecast'] = calculate_batch_forecast(transactions_for_batch[0].sage_batch_ref)

    if request.is_ajax():
        return JsonResponse(context)

    return redirect('core_sage_export:view_batch', sage_batch_ref)


@login_required(login_url='signin')
def sage_xlsx(request, sage_batch_ref):

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
    worksheet.set_column('G:G', 30)
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

    recs = SageBatchDetails.objects.filter(sage_batch_ref_id=sage_batch_ref).order_by('-id')
    transactions_for_batch_total = SageBatchTransactions.objects.filter(sage_batch_ref_id=sage_batch_ref,
                                                                        transactionsourceid__in=['GO1','GO3'],remove=0).aggregate(Sum('sage_batch_netpayment'))
    wip_transactions_for_batch = transactions_for_batch_total["sage_batch_netpayment__sum"]

    sagebatchheader = SageBatchHeaders.objects.get(sage_batch_ref=sage_batch_ref)
    date = sagebatchheader.sage_batch_date.strftime('%d/%m/%Y')
    transaction_total = 0

    for transaction in recs:
        n += 1
        # val_summary += transaction.transnetpayment
        if transaction.transactionsourceid == 'SP1' or transaction.transactionsourceid == 'SP2' or transaction.transactionsourceid == 'SP3'\
                or transaction.transactionsourceid == 'GO1' or transaction.transactionsourceid == 'GO3':
            worksheet.write(n, 0, 'JC', center)
            worksheet.write(n, 1, '', italic_center)
            worksheet.write(n, 2, transaction.nominal_account_ref)
            worksheet.write(n, 3, '0')
            worksheet.write(n, 4, '')
            worksheet.write(n, 4, date)
            worksheet.write(n, 5, '')
            worksheet.write(n, 6, transaction.account_reference, center)
            worksheet.write(n, 7, transaction.batch_detail_total, money)
            worksheet.write(n, 8, transaction.tax_code, center)
            if transaction.tax_code == 'T1':
                transaction_wip = (transaction.batch_detail_total or 0)*decimal.Decimal(0.2)
                worksheet.write(n, 9, transaction_wip  , money)
                transaction_total = transaction_total + transaction_wip
            else :
                worksheet.write(n, 9, 0.00, money)
    if wip_transactions_for_batch:
        n += 1
        worksheet.write(n, 0, 'JD', center)
        worksheet.write(n, 1, '', italic_center)
        worksheet.write(n, 2, 'XXXX')
        worksheet.write(n, 3, '0')
        worksheet.write(n, 4, '')
        worksheet.write(n, 4, date)
        worksheet.write(n, 5, '')
        worksheet.write(n, 6, 'DD Call Debtor Control (XXXX)', center)
        worksheet.write(n, 7, wip_transactions_for_batch, money)
        worksheet.write(n, 8, '', center)
        worksheet.write(n, 9, transaction_total, money)
        # worksheet.write(n, 9, '=SUM(J2:J'+str(n)+')')
            # if transaction.tax_code != 'T1':
            #     worksheet.write(n, 8, transaction.batch_detail_total*decimal(0.2), center)
            # else:
            #     worksheet.write(n, 8, '0.00', money)

    workbook.close()
    output.seek(0)

    filename = 'Sage Export '+ sage_batch_ref +' @ {date:%Y-%m-%d}.xlsx'\
                                                .format(date=datetime.datetime.now())

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    output.close()
    return response


@login_required(login_url='signin')
def process_batch(request, sage_batch_ref):

    context = {}

    try:
        build_sage_transactions_from_batch(SageBatchHeaders.objects.get(sage_batch_ref=sage_batch_ref))
    except Exception as e:
        if str(e) == "This batch has already been processed (1).":
            context['already_complete'] = True
        else:
            context['error'] = '{} {}'.format(e, traceback.format_exc())

    return JsonResponse(context)


@login_required(login_url='signin')
def unlock_batch(request, sage_batch_ref):
    if request.method == "POST":
        sage_batch_lock_session_id = request.POST.get("session_id")
        if sage_batch_lock_session_id:
            try:
                batch_lock = SageBatchLock.objects.get(session_id=sage_batch_lock_session_id)
                batch_lock.released = datetime.datetime.now()
                batch_lock.save()
            except Exception as e:
                pass
    return JsonResponse({"success": True})

