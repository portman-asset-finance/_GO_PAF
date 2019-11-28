from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Max
from django.core.exceptions import ObjectDoesNotExist

import uuid, getpass, requests, json, datetime, decimal

from core_arrears.models import receipt_allocations_by_agreement, arrears_status, arrears_summary_agreement_level
from core_agreement_crud.models import go_agreement_querydetail, go_customers
from core_payments.models import receipt_record, receipt_type

@login_required(login_url='signin')
def record_payment(request):

    uuidOne = uuid.uuid1()
    collection_id = uuidOne
    created_on = datetime.datetime.now()
    username = getpass.getuser()
    django_user = username
    salestax_rate = 0
    wip_receipt_type = receipt_type.objects.get(rt_type_code=request.POST['target_account'])
    wip_receipt_value_net = (int(float(request.POST['amount'])) / 100) * wip_receipt_type.rt_type_crdr_multiplier
    wip_receipt_value_gross = int(float(request.POST['amount'])) / 100 * wip_receipt_type.rt_type_crdr_multiplier

    received_rec = receipt_record(
        rr_receipt_id=collection_id,
        rr_agreement_number = request.POST['agreement_id'],
        rr_receipt_source = 'manual',
        rr_receipt_source_id = collection_id,
        rr_receipt_type = wip_receipt_type,
        rr_receipt_salestax_rate = salestax_rate,
        rr_receipt_value_net = wip_receipt_value_net,
        rr_receipt_value_gross = wip_receipt_value_gross,
        rr_receipt_user_id = request.user,
        rr_receipt_created_on = created_on
    )
    received_rec.save()

    # Get Total Receipts for Agreement
    receipt_total_value_grossofvat = 0
    receipt_total_value_netofvat = 0

    receipt_extract = receipt_record.objects.filter(rr_agreement_number=request.POST['agreement_id'])
    try:

        receipt_total_tuple = receipt_extract.aggregate(Sum('rr_receipt_value_gross'))
        receipt_total_value_grossofvat = receipt_total_tuple['rr_receipt_value_gross__sum']
        receipt_total_value_netofvat = receipt_total_value_grossofvat / decimal.Decimal(1.2)
        receipt_total_value_netofvat = round(receipt_total_value_netofvat, 2)

    except:
        pass

    # Write/Update Total Receipts at Agreement level
    active_status = arrears_status.objects.get(arr_status_code='A')
    val_today = datetime.datetime.today().strftime('%Y-%m-%d')

    agreement_detail_obj = go_agreement_querydetail.objects.get(agreementnumber=request.POST['agreement_id'])

    try:
        receipt_allocations_by_agreement_obj = receipt_allocations_by_agreement.objects.get(
            rag_agreement_id=request.POST['agreement_id'])
    except:
        receipt_allocations_by_agreement_obj = None

    if receipt_allocations_by_agreement_obj:

        receipt_allocations_by_agreement_obj.rag_received_value_grossofvat = receipt_total_value_grossofvat
        receipt_allocations_by_agreement_obj.rag_received_value_netofvat = receipt_total_value_netofvat

        receipt_allocations_by_agreement_obj.rag_unallocated_value_netofvat = receipt_total_value_netofvat \
                                                - receipt_allocations_by_agreement_obj.rag_allocated_value_netofvat

        receipt_allocations_by_agreement_obj.rag_unallocated_value_grossofvat = receipt_total_value_grossofvat \
                                                - receipt_allocations_by_agreement_obj.rag_allocated_value_grossofvat
        return_unallocated = receipt_total_value_grossofvat \
                                                - receipt_allocations_by_agreement_obj.rag_allocated_value_grossofvat
        receipt_allocations_by_agreement_obj.save()

    else:

        return_unallocated = receipt_total_value_grossofvat

        receipt_allocations_by_agreement.objects.create(
            rag_agreement_id=request.POST['agreement_id'],
            rag_customernumber=agreement_detail_obj.agreementcustomernumber,
            rag_customercompanyname=agreement_detail_obj.customercompany,
            rag_received_count=1,
            rag_received_value_netofvat=receipt_total_value_netofvat,
            rag_received_value_grossofvat=receipt_total_value_grossofvat,
            rag_received_last_date=val_today,
            rag_allocated_count=0,
            rag_allocated_value_netofvat=0,
            rag_allocated_value_grossofvat=0,
            rag_allocated_last_date=val_today,
            rag_unallocated_value_netofvat=receipt_total_value_netofvat,
            rag_unallocated_value_grossofvat=receipt_total_value_grossofvat,
            rag_unallocated_last_date=val_today,
            rag_agent_id=request.user,
            rag_status=active_status,
            rag_status_date=val_today
        )

    # If no arrears record, then write so that it appears in arrears lists.
    try:
        arrears_by_agreement_obj = arrears_summary_agreement_level.objects.get(
            arr_agreement_id=request.POST['agreement_id'])
    except:
        arrears_by_agreement_obj = None

    if not arrears_by_agreement_obj:
        arrears_summary_agreement_level.objects.create(
            arr_agreement_id=request.POST['agreement_id'],
            arr_customernumber=agreement_detail_obj.agreementcustomernumber,
            arr_customercompanyname=agreement_detail_obj.customercompany,
            arr_arrears_count=0,
            arr_arrears_value_netofvat=0,
            arr_arrears_value_grossofvat=0,
            arr_arrears_last_date=val_today,
            arr_collected_count=0,
            arr_collected_value_netofvat=0,
            arr_collected_value_grossofvat=0,
            arr_collected_last_date=val_today,
            arr_writtenoff_count=0,
            arr_writtenoff_value_netofvat=0,
            arr_writtenoff_value_grossofvat=0,
            arr_writtenoff_last_date=val_today,
            arr_balance_value_netofvat=0,
            arr_balance_value_grossofvat=0,
            arr_balance_last_date=val_today,
            arr_unallocated_value_netofvat = receipt_total_value_netofvat,
            arr_unallocated_value_grossofvat = receipt_total_value_grossofvat,
            arr_unallocated_last_date = val_today,
            arr_agent_id=request.user,
            arr_status=active_status,
            arr_status_date=val_today)
    else:
        arrears_by_agreement_obj.arr_unallocated_value_netofvat = receipt_total_value_netofvat
        arrears_by_agreement_obj.arr_unallocated_value_grossofvat = receipt_total_value_grossofvat
        arrears_by_agreement_obj.arr_unallocated_last_date = val_today
        arrears_by_agreement_obj.save()

    wip_new_message_text = None
    wip_arrears_collected_message_text = None
    wip_amount = '{:20,.2f}'.format(wip_receipt_value_gross)
    wip_amount_str = str(wip_amount)

    if wip_receipt_value_gross > 0:

        wip_arrears_collected_message_text = '<tr style="color: forestgreen">'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Agreement&nbsp;:&nbsp;'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + str(request.POST['agreement_id'])
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td>'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Unallocated Receipts Collected</td>'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '£' + wip_amount_str
        wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td></tr>'
        wip_new_message_text = wip_arrears_collected_message_text

    else:

        if wip_receipt_value_gross < 0:
            wip_arrears_collected_message_text = '<tr style="color: red">'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Agreement&nbsp;:&nbsp;'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + str(request.POST['agreement_id'])
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>Cancelled Unallocated Receipts</td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '<td>&nbsp;&nbsp;:&nbsp;&nbsp;</td><td>'
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '£' + wip_amount_str
            wip_arrears_collected_message_text = wip_arrears_collected_message_text + '</td></tr>'
            wip_new_message_text = wip_arrears_collected_message_text

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

    # return HttpResponse(json.dumps(response), content_type="application/json")
    return JsonResponse({"success": True, "unallocated_value": return_unallocated})

@login_required(login_url="signin")
def payment_receipt_save(request, agreement_id, template_name):

    # initialise data dictionary
    data = dict()

    # retrieve form data
    wip_agreement_id = agreement_id

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)

    context = {'agreement': wip_agreement_id,
               'agreement_detail': agreement_detail,
               'agreement_customer': agreement_customer,
               }

    if request.method == 'POST':
        data['html_receipt_form'] = render_to_string(template_name, context, request=request)
    else:
        data['html_receipt_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)

@login_required(login_url="signin")
def record_payment_save(request, agreement_id, template_name):

    # initialise data dictionary
    data = dict()

    # retrieve form data
    wip_agreement_id = agreement_id

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)

    context = {'agreement': wip_agreement_id,
               'agreement_detail': agreement_detail,
               'agreement_customer': agreement_customer
               }

    if request.method == 'POST':
        data['html_record_form'] = render_to_string(template_name, context, request=request)
    else:
        data['html_record_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)

@login_required(login_url="signin")
def payment_receipt_modal(request, agreement_id):
    return payment_receipt_save(request, agreement_id, 'includes/partial_receipt_update.html')

@login_required(login_url="signin")
def modal_record_payment(request, agreement_id):
    return record_payment_save(request, agreement_id, 'includes/partial_record_update.html')
