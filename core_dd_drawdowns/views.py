
import re
import json
import uuid
import time
import datetime
import traceback

from django.shortcuts import render, redirect, Http404
from django.db.models import Sum
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .models import DrawDown, BatchHeaders, StatusDefinition, BatchLock, SyncDrawdowns
from .functions import sync_drawdown_table, process_batch, resync_drawdowns_with_dd_history, forecast_prediction, get_batches

from core.models import ncf_dd_status_text
from core.functions_go_id_selector import daysbeforecalldd
# TODO: GO PAF - Start
from core_agreement_crud.models import go_account_transaction_summary, go_funder
# TODO: GO PAF - End
OPEN = StatusDefinition.objects.get(text_code='OPEN')
REMOVED = StatusDefinition.objects.get(text_code='REMOVED')
ARCHIVED = StatusDefinition.objects.get(text_code='ARCHIVED')


@login_required(login_url='signin')
def active(request):

    return JsonResponse({
        'count': BatchHeaders.objects.filter(status=StatusDefinition.objects.get(text_code='OPEN')).count()
    })


@login_required(login_url='signin')
def view_batch_by_ref(request, batch_ref):

    bh_rec = BatchHeaders.objects.get(reference=batch_ref)

    return redirect('core_dd_drawdowns:view_batch', id=bh_rec.id)


@login_required(login_url='signin')
def view_batch(request, id):
    """
    Returns data for a specific batch header id
    :param request:
    :param _id:
    :return:
    """

    bh_rec = BatchHeaders.objects.get(id=id)

    context = {
        'count': bh_rec.total_count,
        'amount': bh_rec.total_amount,
        'status': bh_rec.status.text_code,
        'due_date': bh_rec.due_date,
        'created': bh_rec.created,
        'batch_id': bh_rec.id,
        'batch_ref': bh_rec.reference,
        'success': request.GET.get('success'),
        'sent': bh_rec.sent,
        'uk_due_date': bh_rec.due_date.strftime('%d/%m/%Y'),
        'uk_call_date': bh_rec.call_date.strftime('%d/%m/%Y'),
        'funder_code': bh_rec.funder.funder_code
    }

    if bh_rec.status == OPEN:

        try:
            batch_lock = BatchLock.objects.filter(batch_header=bh_rec, released__isnull=True).order_by('-id')[0]
        except:
            batch_lock = False

        if batch_lock:
            context['batch_lock'] = batch_lock
            context['batch_lock_check'] = True
        else:
            batch_lock_session_id = str(uuid.uuid1())
            batch_lock = BatchLock(batch_header=bh_rec, user=request.user, session_id=batch_lock_session_id)
            batch_lock.save()

            context['batch_lock'] = batch_lock

        resync = False
        url = reverse('core_dd_drawdowns:view_batch', args=[id])

        if request.META.get('HTTP_REFERER'):
            if not re.search(url, request.META['HTTP_REFERER']):
                resync = True
        else:
            resync = True

        if resync:
            resync_drawdowns_with_dd_history(bh_rec.reference)

    else:
        context['history'] = True

    query = {
        'batch_header': bh_rec
    }
    for k in ('agreement_id__contains', 'amount', 'ddi_status', 'status'):
        if request.GET.get(k):
            query[k] = request.GET[k]
            context['filter'] = query

    if query.get('ddi_status'):
        if query['ddi_status'] == 'No Setup':
            del(query['ddi_status'])
            query['dd_reference__isnull'] = True
        else:
            query['ddi_status'] = ncf_dd_status_text.objects.get(dd_text_description=query.get('ddi_status'))

    recs = DrawDown.objects.filter(**query)

    context['filtered_count'] = recs.count()

    paginator = Paginator(recs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    context['records'] = pub

    # TODO: GO PAF - Start
    context['go_funder1'] = go_funder.objects.get(funder_code='1')
    context['go_funder2'] = go_funder.objects.get(funder_code='2')
    context['go_funder3'] = go_funder.objects.get(funder_code='3')
    context['go_funder4'] = go_funder.objects.get(funder_code='4')
    context['go_funder5'] = go_funder.objects.get(funder_code='5')
    # TODO: GO PAF - End

    context.update({'forecast': forecast_prediction(bh_rec.reference)})

    if query.get('ddi_status'):
        query['ddi_status'] = '{}'.format(query['ddi_status'])

    context['query'] = query

    return render(request, 'batch_screen.html', context)


@login_required(login_url='signin')
def view_batches(request):
    """
    Renders a list of historic batches
    :param request:
    :return:
    """

    template = 'batch_list.html'

    context = {
        'invalid_due_date': request.GET.get('invalid_due_date')
    }

    try:
        get_batches(request, context)
    except Exception as e:
        context['error'] = '{} {}'.format(e, traceback.format_exc())

    # TODO: GO PAF - Start
    context['go_funder1'] = go_funder.objects.get(funder_code='1')
    context['go_funder2'] = go_funder.objects.get(funder_code='2')
    context['go_funder3'] = go_funder.objects.get(funder_code='3')
    context['go_funder4'] = go_funder.objects.get(funder_code='4')
    context['go_funder5'] = go_funder.objects.get(funder_code='5')
    # TODO: GO PAF - End

    return render(request, template, context)


@login_required(login_url='signin')
def process_drawdowns(request, batch_ref):
    """
    :param request:
    :param batch_ref:
    :return:
    """

    context = {}
    error = False

    if request.method == 'POST':
        try:
            retval = process_batch(batch_ref)
            if type(retval) is list:
                context['changes'] = retval
                context['forecast'] = forecast_prediction(batch_ref)
            else:
                # print(retval)
                context['success'] = retval
        except Exception as e:
            error = True
             # context['error'] = '{} {}'.format(e, traceback.format_exc())
            context['error'] = str(e)

        if error:
            try:
                bh_obj = BatchHeaders.objects.get(reference=batch_ref)
                bh_obj.status = OPEN
                bh_obj.save()
                DrawDown.objects.filter(batch_header=batch_ref).update(status=OPEN)
            except:
                pass

    return JsonResponse(context)


@login_required(login_url='signin')
def delete_drawdown(request, batch_ref, dd_id):
    """
    Removes the entry from the DrawDown table
    :param request:
    :param batch_ref:
    :param dd_id:
    :return:
    """

    if request.method == 'POST':

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)
        dd_obj = DrawDown.objects.get(id=dd_id)

        bh_obj.total_count -= 1
        bh_obj.total_amount -= dd_obj.amount

        dd_obj.delete()
        bh_obj.save()

    return JsonResponse({'success': True})


@login_required(login_url='signin')
def delete_drawdowns(request, batch_ref):
    """

    :param request:
    :param batch_ref:
    :param dd_id:
    :return:
    """

    if request.method == 'POST' and request.POST.get('filter'):

        query = json.loads(request.POST['filter'])
        if query.get('ddi_status'):
            if query['ddi_status'] == 'No Setup':
                query['dd_reference__isnull'] = True
            else:
                query['ddi_status'] = ncf_dd_status_text.objects.get(dd_text_description=query.get('ddi_status'))

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)
        dd_recs = DrawDown.objects.filter(batch_header=bh_obj, **query)

        if dd_recs.count() > 0:

            for dd_obj in dd_recs:

                bh_obj.total_count -= 1
                bh_obj.total_amount -= dd_obj.amount

                dd_obj.delete()
                bh_obj.save()

    return JsonResponse({'success': True})


@login_required(login_url='signin')
def create_batch(request, due_date):
    """
    Returns drawdowns ready to be batched and also handles the batch file
    :param request:
    :param due_date:
    :return:
    """

    template_name = 'batch_screen.html'

    context = {
        'records': [],
        'amount': '',
        'b_amount': '',
        'count': '',
        'b_count': '',
        'due_date': '',
        'batch_ref': '',
        'remove_success': request.GET.get('remove_success')
    }

    call_date = request.GET.get('call_date') or due_date

    if request.method == 'POST':
        pass

    else:

        try:
            datetime.datetime.strptime(due_date, '%Y-%m-%d')
            datetime.datetime.strptime(call_date, '%Y-%m-%d')
        except:
            raise Http404()

        try:

            count = 0
            amount = 0

            days = daysbeforecalldd()
            if datetime.datetime.strptime(call_date, "%Y-%m-%d") < datetime.datetime.now() + datetime.timedelta(days=days):
                raise Exception("Due date must be at least 7 days in the future.")

            try:
                batches = sync_drawdown_table(due_date, user=request.user, call_date=call_date)
            except Exception as e:
                context['error'] = '{} {}'.format(e, traceback.format_exc())
                get_batches(request, context)
                return render(request, 'batch_list.html', context)

            new_batches = batches.get('new_batches', [])
            existing_batches = batches.get('existing_batches', [])

            # New batches but none existing
            if len(new_batches) and not len(existing_batches):
                if len(new_batches) == 1:
                    return redirect('core_dd_drawdowns:view_batch', id=new_batches[0])
                else:
                    url = reverse('core_dd_drawdowns:view_batches') + '?due_date={}&created={}'.format(due_date,
                                                                                                       len(new_batches))
                    return redirect(url)

            # No new batches but existing batches
            if not len(new_batches) and len(existing_batches):
                if len(existing_batches) == 1:
                    return redirect('core_dd_drawdowns:view_batch', id=existing_batches[0])
                else:
                    url = reverse('core_dd_drawdowns:view_batches') + '?due_date={}&open={}'.format(due_date,
                                                                                                    len(existing_batches))
                    return redirect(url)

            # New batches and existing batches
            elif len(new_batches) and len(existing_batches):
                url = reverse('core_dd_drawdowns:view_batches') + '?due_date={}&created={}'.format(due_date,
                                                                                                   len(new_batches))
                return redirect(url)

            context['count'] = count
            context['amount'] = '{0:0,.2f}'.format(amount or 0)

            context['due_date'] = due_date
            context['uk_due_date'] = datetime.datetime.strftime(datetime.datetime.strptime(due_date, '%Y-%m-%d'), '%d/%m/%Y')
            if type(call_date) is str:
                context['uk_call_date'] = datetime.datetime.strftime(datetime.datetime.strptime(call_date, '%Y-%m-%d'), '%d/%m/%Y')
            else:
                context['uk_call_date'] = call_date.strftime('%d/%m/%Y')

        except Exception as e:
            context['error'] = '{} {}'.format(e, traceback.format_exc())

    if not context['batch_ref'] and not context.get('error'):
        url = reverse('core_dd_drawdowns:view_batches') + '?invalid_due_date=1'
        return redirect(url)

    return render(request, template_name, context)


@login_required(login_url='signin')
def soft_delete_drawdown(request, batch_ref, dd_id):

    data = {'success': True}

    if request.method == 'POST':

        dd_obj = DrawDown.objects.get(id=dd_id)
        dd_obj.status = StatusDefinition.objects.get(text_code='REMOVED')
        dd_obj.save()

        qry = {
            'batch_header': batch_ref,
            'status': 'OPEN'
        }

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)

        bh_filter = DrawDown.objects.filter(**qry)

        bh_obj.total_count = bh_filter.count()
        bh_obj.total_amount = bh_filter.aggregate(Sum('amount')).get('amount__sum', 0) or 0

        go_account_transaction_summary.objects.filter(transactiondate=bh_obj.due_date,
                                                      agreementnumber=dd_obj.agreement_id).update(transactionbatch_id='')

        BatchHeaders.objects.filter(reference=batch_ref).update(total_count=bh_obj.total_count,
                                                                total_amount=bh_obj.total_amount)

        data.update({
            'forecast': forecast_prediction(batch_ref)
        })

    return JsonResponse(data)


@login_required(login_url='signin')
def soft_delete_drawdowns(request, batch_ref):

    data = {'success': True}

    if request.method == 'POST':

        # Check for filters.
        query = {
            'batch_header': batch_ref
        }
        for k in ('agreement_id__contains', 'amount', 'ddi_status'):
            if request.GET.get(k):
                query[k] = request.GET[k]

        if query.get('ddi_status'):
            if query['ddi_status'] == 'No Setup':
                del (query['ddi_status'])
                query['dd_reference__isnull'] = True
            else:
                query['ddi_status'] = ncf_dd_status_text.objects.get(dd_text_description=query.get('ddi_status'))

        dd_filter = DrawDown.objects.filter(**query)
        dd_filter.update(status=REMOVED)

        aids = [row.agreement_id for row in dd_filter]

        go_account_transaction_summary.objects.filter(transactionbatch_id=batch_ref,
                                                      agreementnumber__in=aids).update(transactionbatch_id='')

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)

        dd_filter = DrawDown.objects.filter(status=OPEN, batch_header=batch_ref)

        bh_obj.total_count = dd_filter.count()
        bh_obj.total_amount = dd_filter.aggregate(Sum('amount')).get('amount__sum', 0) or 0

        bh_obj.save()

        data.update({
            'forecast': forecast_prediction(batch_ref)
        })

    return JsonResponse(data)


@login_required(login_url='signin')
def re_add_drawdown(request, batch_ref, dd_id):

    data = {'success': True}

    if request.method == 'POST':

        dd_obj = DrawDown.objects.get(id=dd_id)
        dd_obj.status = OPEN
        dd_obj.save()

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)
        bh_obj.total_count = DrawDown.objects.filter(batch_header=batch_ref, status='OPEN').count()
        bh_obj.total_amount = DrawDown.objects.filter(batch_header=batch_ref, status='OPEN').aggregate(
                                                                                      Sum('amount')).get('amount__sum', 0) or 0

        bh_obj.save()

        ats_filter = go_account_transaction_summary.objects.filter(transactiondate=bh_obj.due_date,
                                                                   agreementnumber=dd_obj.agreement_id)

        ats_filter.update(transactionbatch_id=batch_ref)

        data.update({
            'forecast': forecast_prediction(batch_ref)
        })

    return JsonResponse(data)


@login_required(login_url='signin')
def re_add_drawdowns(request, batch_ref):
    data = {'success': True}

    if request.method == 'POST':

        # Check for filters.
        query = {
            'batch_header': batch_ref
        }
        for k in ('agreement_id__contains', 'amount', 'ddi_status'):
            if request.GET.get(k):
                query[k] = request.GET[k]

        if query.get('ddi_status'):
            if query['ddi_status'] == 'No Setup':
                del (query['ddi_status'])
                query['dd_reference__isnull'] = True
            else:
                query['ddi_status'] = ncf_dd_status_text.objects.get(dd_text_description=query.get('ddi_status'))

        dd_filter = DrawDown.objects.filter(**query)
        dd_filter.update(status=OPEN)

        bh_obj = BatchHeaders.objects.get(reference=batch_ref)
        bh_obj.total_count = DrawDown.objects.filter(batch_header=batch_ref, status='OPEN').count()
        bh_obj.total_amount = DrawDown.objects.filter(batch_header=batch_ref, status='OPEN').aggregate(
            Sum('amount')).get('amount__sum', 0) or 0

        bh_obj.save()

        aids = [row.agreement_id for row in dd_filter]

        go_account_transaction_summary.objects.filter(transactiondate=bh_obj.due_date,
                                                      agreementnumber__in=aids).update(transactionbatch_id=batch_ref)

        data.update({
            'forecast': forecast_prediction(batch_ref)
        })

    return JsonResponse(data)


@login_required(login_url='signin')
def unlock_batch(request, batch_id):
    if request.method == "POST":
        batch_lock_session_id = request.POST.get("session_id")
        if batch_lock_session_id:
            try:
                batch_lock = BatchLock.objects.get(session_id=batch_lock_session_id)
                batch_lock.released = datetime.datetime.now()
                batch_lock.save()
                # print('Release lock {}'.format(batch_lock_session_id))
            except Exception as e:
                print(e)
                pass
        else:
            BatchLock.objects.filter(released__isnull=True,
                                     batch_header=batch_id).update(released=datetime.datetime.now())
    return JsonResponse({"success": True})


@login_required(login_url='signin')
def update_call_date(request, batch_ref):

    context = {'success': True}

    call_date = request.POST.get('call_date')

    if call_date:
        try:
            call_date = datetime.datetime.strptime(call_date, "%Y-%m-%d")
            BatchHeaders.objects.filter(reference=batch_ref).update(call_date=call_date)
            call_date = call_date.strftime("%d/%m/%Y")
            context['success'] = call_date
        except ValueError:
            context = {'success': False, 'error': 'Invalid Date'}

    return JsonResponse(context)


@login_required(login_url='signin')
def archive_batch(request, batch_ref):

    if request.method == 'POST':

        dd_filter = DrawDown.objects.filter(batch_header=batch_ref)
        total_count = dd_filter.count()
        total_amount = dd_filter.aggregate(Sum('amount')).get('amount__sum', 0) or 0
        dd_filter.update(status=REMOVED)

        dd_batch_transaction_removal = go_account_transaction_summary.objects.filter(transactionbatch_id=batch_ref)
        dd_batch_transaction_removal.update(transactionbatch_id='')

        bh_rec = BatchHeaders.objects.get(reference=batch_ref)
        bh_rec.total_count = total_count
        bh_rec.total_amount = total_amount
        bh_rec.status = ARCHIVED
        bh_rec.save()

    return redirect('core_dd_drawdowns:view_batch', id=bh_rec.id)
