# Django Imports
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum

# Python Imports
import datetime, decimal

import uuid
import getpass

from core_agreement_crud.models import go_agreement_querydetail
from core_payments.models import receipt_record, receipt_type
from .filters import go_agreement_querydetail_Filter

from core_arrears.models import receipt_allocations_by_agreement, arrears_status, arrears_summary_agreement_level

@login_required(login_url="signin")
def worldpay(request): #, agreement_id):
    agreement_extract = go_agreement_querydetail.objects.all()
    agreement_list = go_agreement_querydetail_Filter(request.GET, queryset=agreement_extract)
    paginator = Paginator(agreement_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') or request.GET.get('customercompany') \
                 or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')
    return render(request, 'core_app_worldpay/worldpay.html', {'agreement_list': agreement_list,
                                                               'agreement_list_qs': pub,
                                                               'has_filter': has_filter,
                                                           })

@login_required(login_url='signin')
def worldpay_charge(request):
    from .models import Collection_WorldPay
    import requests

    wip_amount = int(round(float(request.POST['amount'])))
    print(wip_amount)

    data = {"token" : request.POST['token'],
            # "orderType" : "your-order-type-option",
            "amount" : wip_amount,
            "currencyCode" : "GBP",
            "orderDescription" : request.POST['agreement_id'],
            # "customerOrderCode":"my-customer-order-code",
            #"settlementCurrency":"GBP" ,
            # "name" : "name",
            # "billingAddress" : {
            #     "address1" : "address1",
            #     "postalCode" : "postCode",
            #     "city" : "city",
            #     "countryCode" : "GB"
            # },
            # "deliveryAddress": {
            #     "firstName": "John",
            #     "lastName": "Smith",
            #     "address1": "address1",
            #     "address2": "address2",
            #     "address3": "address3",
            #     "postalCode": "postCode",
            #     "city": "city",
            #     "state": "state",
            #     "countryCode": "GB",
            #     "telephoneNumber": "02079460761"
            # },
            # "shopperEmailAddress": "name@domain.co.uk",
            # "shopperIpAddress": "195.35.90.111",
            # "shopperSessionId" : "123"
            # }'

    }

    import json
    headers = {'Authorization': 'T_S_58c55792-87b1-4782-ba16-9a55f1e87f90',
               'Content-Type': 'application/json'}
    response = requests.post('https://api.worldpay.com/v1/orders',
                             data=json.dumps(data), headers=headers)

    json_res = response.json()

    if response.status_code != 200 or 'httpStatusCode' in json_res:
        return JsonResponse({'success': False, 'message': json_res['message']})

    # response = (
    #     token=request.POST['worldpayToken'],
        # amount=request.POST['amount'],
        #currency="gbp",
        # source=request.POST['token'],
        # order_description=request.POST['name'],
    # )

    uuidOne = uuid.uuid1()
    collection_id = uuidOne
    created_on = datetime.datetime.now()
    username = getpass.getuser()
    django_user = username
    salestax_rate = 0
    wip_receipt_type = receipt_type.objects.get(rt_type_code='DC')

    worldpay_rec = Collection_WorldPay(
        collection_number=collection_id,
        agreement_number=request.POST['agreement_id'],
        collection_quantity = int(round(float(request.POST['amount']))) / 100,
        user_name=django_user,
        created_on=created_on )
    worldpay_rec.save()

    received_rec = receipt_record(
        rr_receipt_id=collection_id,
        rr_agreement_number = request.POST['agreement_id'],
        rr_receipt_source = 'worldpay',
        rr_receipt_source_id = collection_id,
        rr_receipt_type = wip_receipt_type,
        rr_receipt_salestax_rate = salestax_rate,
        rr_receipt_value_net = int(round(float(request.POST['amount']))) / 100,
        rr_receipt_value_gross = int(round(float(request.POST['amount']))) / 100,
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


    # Write/Update receipt Allocations by Agreement
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

    # If no Arrears by Agreement, then write new one
    try:
        arrears_by_agreement_obj = arrears_summary_agreement_level.objects.get(
            arr_agreement_id=request.POST['agreement_id'])
    except:
        arrears_by_agreement_obj = None

    if not arrears_by_agreement_obj:
        arrears_summary_agreement_level.objects.create(
            arr_agreement_id = request.POST['agreement_id'],
            arr_customernumber = agreement_detail_obj.agreementcustomernumber,
            arr_customercompanyname = agreement_detail_obj.customercompany,
            arr_arrears_count = 0,
            arr_arrears_value_netofvat = 0,
            arr_arrears_value_grossofvat = 0,
            arr_arrears_last_date = val_today,
            arr_collected_count = 0,
            arr_collected_value_netofvat = 0,
            arr_collected_value_grossofvat = 0,
            arr_collected_last_date = val_today,
            arr_writtenoff_count = 0,
            arr_writtenoff_value_netofvat = 0,
            arr_writtenoff_value_grossofvat = 0,
            arr_writtenoff_last_date = val_today,
            arr_balance_value_netofvat = 0,
            arr_balance_value_grossofvat = 0,
            arr_balance_last_date = val_today,
            arr_unallocated_value_netofvat=receipt_total_value_netofvat,
            arr_unallocated_value_grossofvat=receipt_total_value_grossofvat,
            arr_unallocated_last_date=val_today,
            arr_agent_id = request.user,
            arr_status = active_status,
            arr_status_date = val_today)
    else:
        arrears_by_agreement_obj.arr_unallocated_value_netofvat = receipt_total_value_netofvat
        arrears_by_agreement_obj.arr_unallocated_value_grossofvat = receipt_total_value_grossofvat
        arrears_by_agreement_obj.arr_unallocated_last_date = val_today
        arrears_by_agreement_obj.save()

    wip_new_message_text = None
    wip_arrears_collected_message_text = None
    wip_amount_num = '{:20,.2f}'.format(int(float(request.POST['amount'])) / 100)
    wip_amount_str = str(wip_amount_num)

    if wip_amount_num != 0:

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
    return JsonResponse({"success": response.json(), "unallocated_value": return_unallocated})
