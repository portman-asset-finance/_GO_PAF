
import json
import numpy
import eazysdk
import requests
import datetime

from datetime import date, timedelta

from .models import Contracts, BacsIssues, Payments, RequestLog

from core_agreement_crud.models import go_agreement_index, go_agreement_querydetail

from core_direct_debits.models import DDHistory

from core.models import holiday_dates


JSON_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'apiKey': 'P1ldNFNepm6XEABhhYb01pHZhk'
}

ENV = 'sandbox'  # or ecm3
CLIENT_CODE = 'APITMG'
API_KEY = 'P1ldNFNepm6XEABhhYb01pHZhk'


def get_eazysdk():

    client = eazysdk.EazySDK()

    client.settings.current_environment['env'] = ENV

    if ENV == 'sandbox':
        client.settings.sandbox_client_details['client_code'] = CLIENT_CODE
        client.settings.sandbox_client_details['api_key'] = API_KEY

    elif ENV == 'ecm3':
        client.settings.ecm3_client_details['client_code'] = CLIENT_CODE
        client.settings.ecm3_client_details['api_key'] = API_KEY

    return client


def create_dd_mandate(agreement_id, reference, account_name, account_number, sort_code, user=None):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    querydetail = go_agreement_querydetail.objects.get(go_id=go_id.id)

    contract = None
    bank_ref = querydetail.agreementbankreference
    bank_sort_code = querydetail.agreementbanksortcode
    bank_account_name = querydetail.agreementbankaccountname
    bank_account_number = querydetail.agreementbankaccountnumber

    # ======================================
    # Step 1: Do we have a contract already?
    # ======================================
    if Contracts.objects.filter(agreement_id=agreement_id).exists():
        contract = Contracts.objects.get(agreement_id=agreement_id)

    # ==========================================
    # Step 2: Have any customer details changed?
    # ==========================================
    kwargs = {
        'first_name': querydetail.agreementcustomernumber.customerfirstname or 'Matt',
        'last_name': querydetail.agreementcustomernumber.customersurname or 'Brown',
        'email': querydetail.agreementcustomernumber.customeremail,
        'sort_code': sort_code,
        'company_name': querydetail.agreementcustomernumber.customercompany,
        'account_name': account_name,
        'account_number': account_number,
        'address_line1': querydetail.agreementcustomernumber.customeraddress1,
        'post_code': querydetail.agreementcustomernumber.customerpostcode,
        'reference': reference,
        'agreement_id': agreement_id,
        'user': user,
    }
    if contract:
        if bank_ref != reference:
            create_contract(contract.ez_customer_id, **kwargs)
        else:
            update = False
            if bank_sort_code != sort_code:
                update = True
            elif bank_account_number != account_number:
                update = True
            elif bank_account_name != account_name:
                update = True
            if update:
                update_customer(contract.ez_customer_id, **kwargs)
    else:
        create_customer_and_contract(**kwargs)

    return True


def create_customer_and_contract(**kwargs):
    """
    Creates a 'customer' with EazyCollect, then creates a 'Contract'
    with that customer. The contract is the mandate. All customers are "archived" unless
    they have a contract.

    :param kwargs:
    :return:
    """

    # ============================================
    # Step 1: Validate we have required arguments.
    # ============================================
    required_args = ('first_name', 'last_name', 'email', 'sort_code', 'company_name',
                     'account_number', 'address_line1', 'agreement_id', 'reference')
    for arg in required_args:
        if not kwargs.get(arg):
            raise Exception("create_customer: Missing required keyword argument '{}'".format(arg))

    setup_contract = kwargs.get('setup_contract', True)

    # =======================
    # Step 2: Initialize SDK.
    # =======================
    client = get_eazysdk()

    # =====================
    # Step 3: Make request.
    # =====================
    response = client.post.customer(kwargs['email'], 'Mx', kwargs['agreement_id'], kwargs['first_name'],
                                    kwargs['last_name'], kwargs['address_line1'], kwargs['post_code'],
                                    kwargs['account_number'], kwargs['sort_code'], kwargs['account_name'])
    json_response = json.loads(response)

    # ======================
    # Step 4: Store details.
    # ======================
    contract = Contracts(
                agreement_id=kwargs['agreement_id'],
                ez_customer_id=json_response['Id'],
                first_name=kwargs['first_name'],
                last_name=kwargs['last_name'],
                company_name=kwargs['company_name'],
                email=kwargs['email'],
                address_line1=kwargs['address_line1'],
                post_code=kwargs['post_code'],
                account_number=kwargs['account_number'],
                account_name=kwargs['account_name'],
                sort_code=kwargs['sort_code'])
    contract.save()

    # ======================== #
    # Step 5: Create contract. #
    # ======================== #
    if not setup_contract:
        return

    # ===================== #
    # Step 6: Make request. #
    # ===================== #
    dd_ref = kwargs['reference']
    start_date = datetime.datetime.today() + timedelta(days=16)
    response = client.post.contract(json_response['Id'], 'Standard DD Schedule - Adhoc', start_date.strftime("%Y-%m-%d"),
                                    False, 'Until further notice', 'Switch to further notice', custom_dd_reference=dd_ref)

    json_response = json.loads(response)
    contract.ez_contract_id = json_response['Id']
    contract.save()

    # ============================== #
    # Step 7: Remove current 9999's. #
    # ============================== #
    dd_filter = DDHistory.objects.filter(agreement_no=kwargs['agreement_id'])
    count = dd_filter.count()
    dd_filter.update(sequence=count, valid=False)

    # ==================================== #
    # Step 8: Create new DDHistory record. #
    # ==================================== #
    DDHistory(
        agreement_no=kwargs['agreement_id'],
        sequence=9999,
        reference=kwargs['reference'],
        account_number=kwargs['account_number'],
        account_name=kwargs['account_name'],
        sort_code=kwargs['sort_code'],
        dd_reference=contract.ez_contract_id,
        effective_date=datetime.datetime.now(),
        provider='eazycollect',
        user=kwargs['user'],
        valid=True
    ).save()

    return True


def update_customer(ez_customer_id, **kwargs):

    # ============================================ #
    # Step 1: Validate we have required arguments. #
    # ============================================ #
    required_args = ('first_name', 'last_name', 'email', 'sort_code', 'company_name',
                     'account_name', 'account_number', 'address_line1', 'agreement_id')
    for arg in required_args:
        if not kwargs.get(arg):
            raise Exception("create_customer: Missing required keyword argument '{}'".format(arg))

    # ============================ #
    # Step 2: Get contract record. #
    # ============================ #
    contract = Contracts.objects.get(agreement_id=kwargs['agreement_id'])

    # ======================= #
    # Step 3: Initialize SDK. #
    # ======================= #
    client = get_eazysdk()

    # ===================== #
    # Step 4: Make request. #
    # ===================== #
    response = client.patch.customer(kwargs['email'], 'Mx', kwargs['agreement_id'], kwargs['first_name'],
                                     kwargs['last_name'], kwargs['address_line1'], kwargs['post_code'],
                                     kwargs['account_number'], kwargs['sort_code'], kwargs['account_name'])

    json_response = json.loads(response)

    # ======================= #
    # Step 5: Update details. #
    # ======================= #
    contract.first_name = kwargs['first_name']
    contract.last_name = kwargs['last_name']
    contract.company_name = kwargs['company_name']
    contract.account_name = kwargs['account_name']
    contract.sort_code = kwargs['sort_code']
    contract.account_number = kwargs['account_number']
    contract.email = kwargs['email']
    contract.post_code = kwargs['post_code']
    contract.ez_customer_id = json_response['Id']
    contract.save()

    return True


def create_contract(ez_customer_id, **kwargs):

    # ======================= #
    # Step 1: Initialize SDK  #
    # ======================= #
    client = eazysdk.EazySDK()

    # =========================== #
    # Step 2: Create new contract #
    # =========================== #
    start_date = datetime.datetime.today() + timedelta(days=16)
    dd_ref = kwargs['reference']
    response = client.post.contract(ez_customer_id, 'Standard DD Schedule - Adhoc', start_date.strftime("%Y-%m-%d"),
                                    False, 'Until further notice', 'Switch to further notice', custom_dd_reference=dd_ref)
    json_response = json.loads(response)

    # ================================= #
    # Step 3: Cancel previous contracts #
    # ================================= #
    contracts = DDHistory.objects.filter(agreement_no=kwargs['agreement_id'], sequence=9999, provider='eazycollect')
    for row in contracts:
        client.post.cancel_direct_debit(row.dd_reference)
        row.cancelled_date = datetime.datetime.now()
        row.valid = False
        row.save()

    # ============================= #
    # Step 4: Remove current 9999's #
    # ============================= #
    dd_filter = DDHistory.objects.filter(agreement_no=kwargs['agreement_id'])
    contracts.update(sequence=dd_filter.count(), valid=False)

    # =============================== #
    # Step 5: Create DDHistory record #
    # =============================== #
    DDHistory(
        agreement_no=kwargs['agreement_id'],
        sequence=9999,
        reference=kwargs['reference'],
        account_number=kwargs['account_number'],
        account_name=kwargs['account_name'],
        sort_code=kwargs['sort_code'],
        dd_reference=json_response['Id'],
        effective_date=datetime.datetime.now(),
        provider='eazycollect',
        user=kwargs['user'],
        valid=True
    ).save()

    return True


def send_bulk_payments(**kwargs):

    url = 'https://{}.eazycollect.co.uk/api/v3/client/{}/bulk/payments'.format(ENV, CLIENT_CODE)

    data = []
    for rec in kwargs['recs']:
        dt_obj = datetime.datetime.strptime(rec['due_date'], '%Y%m%d')
        formatted_dt = dt_obj.strftime('%Y-%m-%d')
        data.append({
            'contract': rec['dd_reference'],
            'amount': str(rec['amount']),
            'date': '{}'.format(formatted_dt),
            'isCredit': False
        })

    json_data = {
        'Payments': data
    }

    log_obj = RequestLog(http_method='POST', request_type='payment', url=url, source_type='BatchHeaders',
                         source_id=kwargs['batch_ref'], request=json.dumps(json_data), headers=json.dumps(JSON_HEADERS))

    response = requests.post(url, data=json.dumps(json_data), headers=JSON_HEADERS)

    log_obj.status_code = response.status_code

    if response.status_code != 200:
        raise Exception(response.json())

    log_obj.response = json.dumps(response.json())
    log_obj.save()

    return True


def process_callback(post_data):

    if post_data.get('Contract'):

        # ========================================= #
        # Bulk Payment Insert Return Information    #
        # ----------------------------------------- #
        # (See page 55 of API_V3_Documentation.pdf) #
        # ========================================= #

        contract = Contracts.objects.get(ez_contract_id=post_data.get('Contract'))

        data = {
            'agreement_id': contract.agreement_id,
            'ez_payment_id': post_data.get('Id'),
            'ez_contract_id': post_data.get('Contract'),
            'due_date': post_data.get('DueDate'),
            'amount': post_data.get('Amount'),
            'error': post_data.get('Error'),
            'message': post_data.get('Message')
        }
        Payments(**data).save()

        return True

    elif post_data.get('Source'):

        # ========================================= #
        # BACS Object Change Return Information     #
        # ----------------------------------------- #
        # (See page 54 of API_V3_Documentation.pdf) #
        # ========================================= #

        if post_data.get('Source') in ('ADDACS', 'ARUDD', 'DDIC'):

            agreement_id = None

            entity = post_data.get('Entity')

            if entity == 'contract':
                contract = Contracts.objects.get(ez_contract_id=post_data.get('Id'))
                agreement_id = contract.agreement_id

            elif entity == 'payment':
                payment = Payments.objects.get(ez_payment_id=post_data.get('Id'))
                agreement_id = payment.agreement_id

            data = {
                'agreement_id': agreement_id,
                'new_status': post_data.get('NewStatus'),
                'object_id': post_data.get('Id'),
                'change_date': post_data.get('ChangeDate'),
                'entity': post_data.get('Entity'),
                'source': post_data.get('Source'),
                'message': post_data.get('ReportMessage'),
                'comment': post_data.get('Comment')
            }

            BacsIssues(**data).save()

    return True


def get_wds():

    holidays = get_holidays()

    working_days = numpy.busday_offset(date.today(), 10, roll='forward', holidays=holidays).astype(datetime)

    return working_days.strftime("%Y-%m-%d")


def get_holidays(from_date=datetime.datetime.today(), max_days_ahead=90):

    filter_obj = {
        'holiday_date__gte': from_date,
        'holiday_date__lte': from_date + timedelta(days=max_days_ahead)
    }

    recs = []
    for rec in holiday_dates.objects.filter(**filter_obj):
        recs.append('{}'.format(rec.holiday_date))

    return recs


