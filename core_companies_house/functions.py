
from .apps import CoreCompaniesHouseConfig

from .models import RequestType, RequestLog, CompanyHouse_CompanyProfile,eTagAudit, \
    CompanyHouse_CompanyProfile_Previous_Company_Names, CompanyHouse_Registered_Office_Address, CompanyHouse_Company_Officers, CompanyHouse_Charge_List, eTagAudit, CompanyHouse_Changes
from django.db.models import Q

from core_agreement_crud.models import  go_agreement_index, go_agreement_querydetail, go_customers

import re
import base64
import requests
import datetime
#############
# Constants #
#############

API_KEY = CoreCompaniesHouseConfig.api_key
BASE_URL = CoreCompaniesHouseConfig.base_url
AUTH_HEADER = base64.b64encode(bytes('{}:'.format(API_KEY), 'UTF-8'))
HTTP_STATUS_CODES = {
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Payload Too Large',
    414: 'URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'I\'m a teapot',
    421: 'Misdirected Request',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    425: 'Too Early',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    451: 'Unavailable For Legal Reasons',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    510: 'Not Extended',
    511: 'Network Authentication Required',
    526: 'Invalid SSL Certificate',
    598: 'Network read timeout error'
}

def api_call(api_type, **kwargs):
    """
    Main function that handles making all of the requests.
    PLEASE LOOK FURTHER DOWN BELOW TO VIEW EXAMPLE RESPONSES FOR EACH REQUEST TYPE.
    :return: Response JSON.

    """

    # Step 1: Get the request type
    # =============================
    request_type = RequestType.objects.get(code=api_type)

    # Step 2: Validate we have the correct kwargs
    # ============================================
    required_kwargs = re.findall('{(\\w+)}', request_type.url)
    for kwarg in required_kwargs:
        if not kwargs.get(kwarg):
            raise Exception("Missing keyword argument '{}' for {} request. (Required: {})".format(kwarg, api_type,
                                                                                                  required_kwargs))

    # Step 3: Build URL
    # ==================
    url = BASE_URL + request_type.url
    for kwarg in required_kwargs:
        url = re.sub('{{{}}}'.format(kwarg), kwargs[kwarg], url)
    print(url)
    # Step 4: Create Authorization header
    # ====================================
    headers = {
        'Authorization': 'Basic {}'.format(AUTH_HEADER.decode('UTF-8'))
    }

    # Step 5: Create request
    # =======================
    http_client = None
    if request_type.method == 'GET':
        http_client = requests.get(url, headers=headers)

    if http_client is None:
        raise Exception("HTTP Request Method {} not catered for.".format(request_type.method))

    # Step 6: Log response
    # =====================
    ___log_request_response(request_type, http_client)
    # ___log_company_profile(request_type, http_client) 1
    # ___log_company_profile_company_names(request_type, http_client) 1

    # ___log_registered_company_address(request_type, http_client) 2
    # ___log_company_profile_company_officers(request_type, http_client) 3
    # ___log_company_profile_charge_list(request_type, http_client)

    # Step 7: Was we successful?
    # ===========================
    if http_client.status_code not in [200,404]:
        raise Exception("Request failed with HTTP status code {} {}".format(http_client.status_code,
                                                                            HTTP_STATUS_CODES.get(http_client.status_code, '')))

    # Step 8: Handle response
    # ========================
    return http_client.json()


def schedule_request_for_companyinspector():
    pass


def ___log_request_response(request_type, http_client):
    """
    Log the response.
    :return:
    """

    log_rec = {
        'request_type': request_type,
        'status_code': http_client.status_code,
        'response': http_client.text,
        'full_url': http_client.url,
    }
    RequestLog(**log_rec).save()

    return True

def ___log_company_profile(companies_house_json_dictionary, company_number=None):
    """
    Log the response.
    :return:
    """

    # Check to see if we have an eTag
    etag_obj = None
    try:
        etag_obj = eTagAudit.objects.get(company_number=company_number, type_of_change='COMPANY_PROFILE')
        etag = etag_obj.etag
    except:
        etag = None

    # If the etag already matches what we have, return as we
    # don't need to do anything
    if companies_house_json_dictionary.get('etag') == etag:
        return True

    # If the etag is different, update the current etag with
    # the new one
    if etag_obj:
        etag_obj.etag = companies_house_json_dictionary['etag']

    # We don't have an existing etag so lets create one
    else:
        etag_obj = eTagAudit(
            company_number=company_number,
            etag=companies_house_json_dictionary['etag'],
            type_of_change=RequestType.objects.get(code='COMPANY_PROFILE'),

        )

    # CompanyHouse_CompanyProfile.objects.filter(company_number=company_number).delete()

    # Create new record.
    log_rec = {
        'company_number': company_number,
        'registered_office_address_address_line_1' : companies_house_json_dictionary.get('registered_office_address').get('address_line_1'),
        'registered_office_address_address_line_2' : companies_house_json_dictionary.get('registered_office_address').get('address_line_2'),
        'registered_office_address_locality' : companies_house_json_dictionary.get('registered_office_address').get('locality'),
        'registered_office_address_region' : companies_house_json_dictionary.get('registered_office_address').get('region'),
        'registered_office_address_postal_code' : companies_house_json_dictionary.get('registered_office_address').get('postal_code'),
        'date_of_creation' : companies_house_json_dictionary.get('date_of_creation'),
        'last_full_members_list_date' : companies_house_json_dictionary.get('last_full_members_list_date'),
        'company_name' : companies_house_json_dictionary.get('company_name'),
        'status' : companies_house_json_dictionary.get('status'),
        'has_been_liquidated' : companies_house_json_dictionary.get('has_been_liquidated'),
        'jurisdiction' : companies_house_json_dictionary.get('jurisdiction'),

        'accounts_next_due' : companies_house_json_dictionary.get('accounts').get('next_due'),
        # 'accounts_accounting_reference_date' : companies_house_json_dictionary.get('accounts').get('next_due'),
        'accounts_next_made_up_to' : companies_house_json_dictionary.get('accounts').get('next_made_up_to'),
        'accounts_next_accounts_period_end_on' : companies_house_json_dictionary.get('accounts').get('next_accounts').get('period_end_on'),
        'accounts_next_accounts_due_on' : companies_house_json_dictionary.get('accounts').get('next_accounts').get('due_on'),
        'accounts_next_accounts_period_start_on' : companies_house_json_dictionary.get('accounts').get('next_accounts').get('period_start_on'),
        'accounts_next_accounts_overdue' : companies_house_json_dictionary.get('accounts').get('next_accounts').get('overdue'),
        'accounts_overdue' : companies_house_json_dictionary.get('accounts').get('overdue'),
        'accounts_last_accounts_made_up_to' : companies_house_json_dictionary.get('accounts').get('last_accounts').get('made_up_to'),
        'accounts_last_accounts_type' : companies_house_json_dictionary.get('accounts').get('last_accounts').get('type'),
        'accounts_last_accounts_period_end_on' : companies_house_json_dictionary.get('accounts').get('last_accounts').get('period_end_on'),
        'accounts_last_accounts_period_start_on' : companies_house_json_dictionary.get('accounts').get('last_accounts').get('period_start_on'),

        'undeliverable_registered_office_address' : companies_house_json_dictionary.get('undeliverable_registered_office_address'),
        'sic_codes' : companies_house_json_dictionary.get('sic_codes'),
        'type' : companies_house_json_dictionary.get('type'),
        'etag' : companies_house_json_dictionary.get('etag'),
        'has_insolvency_history' : companies_house_json_dictionary.get('has_insolvency_history'),
        'company_status' : companies_house_json_dictionary.get('company_status'),
        'has_charges' : companies_house_json_dictionary.get('has_charges'),

        'confirmation_statement_next_due' : companies_house_json_dictionary.get('confirmation_statement').get('next_due'),
        'confirmation_statement_last_made_up_to' : companies_house_json_dictionary.get('confirmation_statement').get('last_made_up_to'),
        'confirmation_statement_next_made_up_to' : companies_house_json_dictionary.get('confirmation_statement').get('next_made_up_to'),
        'confirmation_statement_overdue' : companies_house_json_dictionary.get('confirmation_statement').get('statement_overdue'),

        'links_self' : companies_house_json_dictionary.get('links').get('self'),
        'links_filing_history' : companies_house_json_dictionary.get('links').get('filing_history'),
        'links_officers' : companies_house_json_dictionary.get('links').get('officers'),
        'links_persons_with_significant_control' : companies_house_json_dictionary.get('links').get('persons_with_significant_control'),

        # 'previous_company_names_name' : companies_house_json_dictionary.get('previous_company_names').get('name'),
        # 'previous_company_names_ceased_on' : companies_house_json_dictionary.get('previous_company_names').get('ceased_on'),
        # 'previous_company_names_effective_from' : companies_house_json_dictionary.get('previous_company_names').get('effective_from'),

        'registered_office_is_in_dispute' : companies_house_json_dictionary.get('registered_office_is_in_dispute'),
        'can_file' : companies_house_json_dictionary.get('can_file'),
    }
    if eTagAudit.objects.filter(etag=companies_house_json_dictionary.get('etag')):
        return True
    else:
        CompanyHouse_CompanyProfile.objects.filter(company_number=company_number).delete()
        CompanyHouse_CompanyProfile(**log_rec).save()
        etag_obj.save()

        # agreementnumber = row.agreement_id
        agreement_number = go_agreement_index.objects.filter(company_ref_no=company_number)[0]
        datalookup = go_agreement_querydetail.objects.get(agreementnumber=agreement_number)
        customer_data = go_customers.objects.get(customernumber=datalookup.agreementcustomernumber)
        log_rec = {
            'company': datalookup.customercompany,
            'company_number': company_number,
            'contact_name': customer_data.customercontact,
            'contact_number': customer_data.customermobilenumber+"  "+customer_data.customerphonenumber,
            'account_manager': datalookup.agreementauthority,
            'type_of_change': "Profile",
            'ncf_customer_number': datalookup.agreementcustomernumber,
            'link': "/company/" + company_number,
            'checked': "Unchecked",
            'etag': companies_house_json_dictionary.get('etag'),
        }
        CompanyHouse_Changes(**log_rec).save()

    return True

def ___log_company_profile_company_names(companies_house_json_dictionary, company_number=None):
    """
    Log the response.
    :return:
    """
    # companies_house_json_dictionary = http_client.json()
    CompanyHouse_CompanyProfile_Previous_Company_Names.objects.filter(company_number=company_number).delete()

    for row in companies_house_json_dictionary.get('previous_company_names', []):
        log_rec = {
            'company_number' : company_number,
            'previous_company_names_name' : row.get('name'),
            'previous_company_names_ceased_on' : row.get('ceased_on'),
            'previous_company_names_effective_from' : row.get('effective_from'),
        }
        CompanyHouse_CompanyProfile_Previous_Company_Names(**log_rec).save()


    return True

def ___log_registered_company_address(companies_house_json_dictionary, company_number=None):
    """
    Log the response.
    :return:
    """

    # Check to see if we have an eTag
    etag_obj = None
    try:
        etag_obj = eTagAudit.objects.get(company_number=company_number, type_of_change='REGISTERED_OFFICE_ADDRESS')
        etag = etag_obj.etag
    except:
        etag = None

    # If the etag already matches what we have, return as we
    # don't need to do anything
    if companies_house_json_dictionary.get('etag') == etag:
        return True

    # If the etag is different, update the current etag with
    # the new one
    if etag_obj:
        etag_obj.etag = companies_house_json_dictionary['etag']

    # We don't have an existing etag so lets create one
    else:
        etag_obj = eTagAudit(
            company_number=company_number,
            etag=companies_house_json_dictionary['etag'],
            type_of_change=RequestType.objects.get(code='REGISTERED_OFFICE_ADDRESS'),

        )

    # CompanyHouse_Registered_Office_Address.objects.filter(company_number=company_number).delete()

    log_rec = {
        'company_number': company_number,
        'address_line_1' : companies_house_json_dictionary.get('address_line_1'),
        'address_line_2' : companies_house_json_dictionary.get('address_line_2'),
        'locality' : companies_house_json_dictionary.get('locality'),
        'region' : companies_house_json_dictionary.get('region'),
        'postal_code' : companies_house_json_dictionary.get('postal_code'),
        'kind'  : companies_house_json_dictionary.get('kind'),
        'etag'  : companies_house_json_dictionary.get('etag'),
        'links_self'  : companies_house_json_dictionary.get('links').get('self'),
    }

    if eTagAudit.objects.filter(etag=companies_house_json_dictionary.get('etag')):
        return True
    else:
        # CompanyHouse_Registered_Office_Address.objects.filter(company_number=company_number).delete()
        CompanyHouse_Registered_Office_Address(**log_rec).save()
        etag_obj.save()

        # agreementnumber = row.agreement_id
        agreement_number = go_agreement_index.objects.filter(company_ref_no=company_number)[0]
        datalookup = go_agreement_querydetail.objects.get(agreementnumber=agreement_number)
        customer_data = go_customers.objects.get(customernumber=datalookup.agreementcustomernumber)
        log_rec = {
            'company': datalookup.customercompany,
            'company_number': company_number,
            'contact_name': customer_data.customercontact,
            'contact_number': customer_data.customermobilenumber+" "+customer_data.customerphonenumber,
            'account_manager': datalookup.agreementauthority,
            'type_of_change': "Address",
            'ncf_customer_number': datalookup.agreementcustomernumber,
            'link': "/company/" + company_number,
            'checked': "Unchecked",
            'etag': companies_house_json_dictionary.get('etag'),
        }
        CompanyHouse_Changes(**log_rec).save()

    return True

def ___log_company_profile_company_officers(companies_house_json_dictionary, company_number=None):
    """
    Log the response.
    :return:
    """

    # Check to see if we have an eTag
    etag_obj = None
    try:
        etag_obj = eTagAudit.objects.get(company_number=company_number, type_of_change='COMPANY_OFFICERS')
        etag = etag_obj.etag
    except:
        etag = None

    # If the etag already matches what we have, return as we
    # don't need to do anything
    if companies_house_json_dictionary.get('etag') == etag:
        return True

    # If the etag is different, update the current etag with
    # the new one
    if etag_obj:
        etag_obj.etag = companies_house_json_dictionary['etag']

    # We don't have an existing etag so lets create one
    else:
        etag_obj = eTagAudit(
            company_number=company_number,
            etag=companies_house_json_dictionary['etag'],
            type_of_change=RequestType.objects.get(code='COMPANY_OFFICERS'),

        )
    CompanyHouse_Company_Officers.objects.filter(company_number=company_number).delete()
    for row in companies_house_json_dictionary.get('items'):

        log_rec = {
            'company_number': company_number,
            'etag' :  row.get('etag'),
            'country_of_residence' : row.get('country_of_residence'),
            'appointed_on' : row.get('appointed_on'),
            'date_of_birth_month' : row.get('date_of_birth',{}).get('month'),
            'date_of_birth_year' : row.get('date_of_birth',{}).get('year'),
            'nationality' : row.get('nationality'),
            'officer_role' : row.get('officer_role'),
            'address_country' : row.get('address', {}).get('country'),
            'address_region' : row.get('address', {}).get('region'),
            'address_premises' : row.get('address',{}).get('premises'),
            'address_address_line_1' : row.get('address',{}).get('address_line_1'),
            'address_locality' : row.get('address',{}).get('locality'),
            'address_postal_code' : row.get('address',{}).get('postal_code'),
            'occupation' : row.get('occupation'),
            'name' : row.get('name'),
        }

        CompanyHouse_Company_Officers(**log_rec).save()
    if eTagAudit.objects.filter(etag=etag_obj.etag):
        print('working')
    else:
        etag_obj.save()
        agreement_number = go_agreement_index.objects.filter(company_ref_no=company_number)[0]
        datalookup = go_agreement_querydetail.objects.get(agreementnumber=agreement_number)
        customer_data = go_customers.objects.get(customernumber=datalookup.agreementcustomernumber)
        log_rec = {
            'company': datalookup.customercompany,
            'company_number': company_number,
            'contact_name': customer_data.customercontact,
            'contact_number': customer_data.customermobilenumber+" "+customer_data.customerphonenumber,
            'account_manager': datalookup.agreementauthority,
            'type_of_change': "Officer",
            'ncf_customer_number': datalookup.agreementcustomernumber,
            'link': "/company/" + company_number + "/officers",
            'checked': "Unchecked",
            'etag': etag_obj.etag,
        }
        CompanyHouse_Changes(**log_rec).save()

    return True

def ___log_company_profile_charge_list(companies_house_json_dictionary, company_number=None):
    """
    Log the response.
    :return:
    """

    # Check to see if we have an eTag
    etag_obj = None
    try:
        etag_obj = eTagAudit.objects.get(company_number=company_number, type_of_change='CHARGES_LIST')
        etag = etag_obj.etag
    except:
        etag = None

    # If the etag already matches what we have, return as we
    # don't need to do anything
    # print(etag)
    # if companies_house_json_dictionary.get('etag') == etag:
    #     return True

    # If the etag is different, update the current etag with
    # the new one
    if etag_obj:
        etag_obj.etag = companies_house_json_dictionary['etag']

    # We don't have an existing etag so lets create one
    else:
        etag_obj = eTagAudit(
            company_number=company_number,
            # etag=companies_house_json_dictionary['etag'],
            type_of_change=RequestType.objects.get(code='CHARGES_LIST'),
        )

    CompanyHouse_Charge_List.objects.filter(company_number=company_number).delete()

    for row in companies_house_json_dictionary.get('items',{}):
        log_rec = {
            'company_number' : company_number,
            'description' : row.get('particulars',{}).get('description'),
            'contains_negative_pledge' : row.get('particulars',{}).get('contains_negative_pledge'),
            'contains_floating_charge' : row.get('particulars',{}).get('contains_floating_charge'),
            'floating_charge_covers_all' : row.get('particulars',{}).get('floating_charge_covers_all'),
            'contains_fixed_charge' : row.get('particulars',{}).get('contains_fixed_charge'),
            'type' : row.get('particulars',{}).get('type'),
            'created_on' : row.get('created_on'),
            'persons_entitled' : row.get('persons_entitled',{}),
            'classification_description' : row.get('classification', {}).get('description'),
            'classification_type' : row.get('classification', {}).get('type'),
            'status' : row.get('status'),
            'transactions_filing_type' : row.get('transactions', {}),
            # 'transactions_filing' : row.get('filing'),
            # 'transactions_delivered_on' : row.get('transactions', {}).get('delivered_on'),
            'charge_number' : row.get('charge_number'),
            'charge_code' : row.get('charge_code'),
            'delivered_on' : row.get('delivered_on'),
            'etag' : row.get('etag'),
            'satisfied_count' : companies_house_json_dictionary.get('satisfied_count'),
            'total_count' : companies_house_json_dictionary.get('total_count'),
            'unfiltered_count' : companies_house_json_dictionary.get('unfiltered_count'),
            'part_satisfied_count' : companies_house_json_dictionary.get('part_satisfied_count'),
        }

        if row.get('etag'):
            etag_obj = eTagAudit(
                company_number=company_number,
                etag= row.get('etag'),
                type_of_change=RequestType.objects.get(code='CHARGES_LIST'),
            )
        else:
            etag_obj = eTagAudit(
                company_number=company_number,
                etag='No Charge',
                type_of_change=RequestType.objects.get(code='CHARGES_LIST'),
            )
        # if eTagAudit.objects.filter(etag=row.get('etag')):
        #     return True
        # else:
        #     count = '1'
        #     etag = row.get('etag')
        # if count:

        CompanyHouse_Charge_List(**log_rec).save()
    if eTagAudit.objects.filter(etag=etag_obj.etag):
        print('Working')
    else:
        etag_obj.save()

        agreement_number = go_agreement_index.objects.filter(company_ref_no=company_number)[0]
        datalookup = go_agreement_querydetail.objects.get(agreementnumber=agreement_number)
        customer_data = go_customers.objects.get(customernumber = datalookup.agreementcustomernumber)
        if etag_obj.etag:
            log_rec = {
                'company': datalookup.customercompany,
                'company_number': company_number,
                'contact_name': customer_data.customercontact,
                'contact_number': customer_data.customermobilenumber+" "+customer_data.customerphonenumber,
                'account_manager': datalookup.agreementauthority,
                'type_of_change': "Charges",
                'ncf_customer_number': datalookup.agreementcustomernumber,
                'link': "/company/"+company_number+"/charges",
                'checked': "Unchecked",
                'etag': etag_obj.etag,
            }
            CompanyHouse_Changes(**log_rec).save()

    return True


def Compare_Company_House_Data(**kwargs):

    # customer_data_test = go_agreement_index.objects.filter(company_ref_no__isnull=False, companies_house_status_flag__isnull=True).exclude(company_ref_no='',companies_house_status_flag="X").first()
    customer_data_test = go_agreement_index.objects.filter(Q(companies_house_status_flag__isnull=True)|Q(companies_house_status_flag='')|Q(companies_house_status_flag='G'),company_ref_no__isnull=False, ).exclude(company_ref_no='').first()

    if not customer_data_test:
        customer_data_clear = go_agreement_index.objects.filter(company_ref_no__isnull=False).exclude(company_ref_no='')
        customer_data_clear.update(companies_house_status_flag='G')

    customer_data = go_agreement_index.objects.filter(Q(companies_house_status_flag__isnull=True)|Q(companies_house_status_flag='')|Q(companies_house_status_flag='G'),company_ref_no__isnull=False, ).exclude(company_ref_no='')

    max_counts = kwargs.get('api_rate_limit_amount', 500)
    total_lookups = 0

    for row in customer_data:

        company_no=row.company_ref_no
        agreementnumber=row.agreement_id

        datalookup = go_agreement_querydetail.objects.filter(agreementnumber=agreementnumber)

        response1 = api_call("COMPANY_PROFILE", company_number=company_no)
        ___log_company_profile(response1, company_number=company_no) #1#

        # response2 = api_call("COMPANY_PROFILE", company_number=company_no)
        ___log_company_profile_company_names(response1, company_number=company_no) #1#
        total_lookups += 1
        if total_lookups >= max_counts:
            break

        response3 = api_call("REGISTERED_OFFICE_ADDRESS", company_number=company_no)
        ___log_registered_company_address(response3, company_number=company_no) #2#
        total_lookups += 1
        if total_lookups >= max_counts:
            break

        response4 = api_call("COMPANY_OFFICERS", company_number=company_no)
        ___log_company_profile_company_officers(response4, company_number=company_no) #3#
        total_lookups += 1
        if total_lookups >= max_counts:
            break

        response5 = api_call("CHARGES_LIST", company_number=company_no)
        ___log_company_profile_charge_list(response5, company_number=company_no) #4#
        total_lookups += 1
        if total_lookups >= max_counts:
            break

        row.companies_house_status_flag = "X"

        row.save()


        # company_no = request.GET.get('company_no')
        # if request.method == 'POST' and company_no:
        #     # data = api_call("COMPANY_PROFILE",company_number=company_no)
        #     data = api_call("REGISTERED_OFFICE_ADDRESS", company_number=company_no)




    # return JsonResponse(data)

    """
    customer_data = go_agreement_index.objects.filter(company_ref_no=true)  
    
    for line in c
    #
    Log the response.
    :return:
    """
    # companies_house_json_dictionary = http_client.json()

    # scheduler to grab all info for the company numbers we have
    # check each of them against the info on file
    # using the company number as a base
    # if companies_house.etag != new_companies_house.etag x 4 (charge_list, companyofficers, companyprofile, registered office _address)
    # print info to changes table
    # copy new info over to table
    # else
    # do nothing



    # for agreement in required_customer_data:



    return True


#############################
#                           #
#    EXAMPLE RESPONSES      #
#                           #
#############################
#
# Request Type: COMPANY_PROFILE
# ------------------------------
#
# {'accounts': {'accounting_reference_date': {'day': '31', 'month': '12'},
#               'last_accounts': {'made_up_to': '2017-12-31',
#                                 'period_end_on': '2017-12-31',
#                                 'period_start_on': '2017-01-01',
#                                 'type': 'small'},
#               'next_accounts': {'due_on': '2019-09-30',
#                                 'overdue': False,
#                                 'period_end_on': '2018-12-31',
#                                 'period_start_on': '2018-01-01'},
#               'next_due': '2019-09-30',
#               'next_made_up_to': '2018-12-31',
#               'overdue': False},
#  'can_file': True,
#  'company_name': 'NATIONWIDE CORPORATE FINANCE LIMITED',
#  'company_number': '04582994',
#  'company_status': 'active',
#  'confirmation_statement': {'last_made_up_to': '2018-07-01',
#                             'next_due': '2019-07-15',
#                             'next_made_up_to': '2019-07-01',
#                             'overdue': False},
#  'date_of_creation': '2002-11-06',
#  'etag': '927c2b4533f38108da1178471cb2c19850259d14',
#  'has_been_liquidated': False,
#  'has_charges': True,
#  'has_insolvency_history': False,
#  'jurisdiction': 'england-wales',
#  'last_full_members_list_date': '2015-07-01',
#  'links': {'charges': '/company/04582994/charges',
#            'filing_history': '/company/04582994/filing-history',
#            'officers': '/company/04582994/officers',
#            'persons_with_significant_control': '/company/04582994/persons-with-significant-control',
#            'self': '/company/04582994'},
#  'previous_company_names': [{'ceased_on': '2009-12-09',
#                              'effective_from': '2002-11-06',
#                              'name': 'NATIONWIDE CORPORATE FINANCE PLC'}],
#  'registered_office_address': {'address_line_1': '9 Osier Way',
#                                'address_line_2': 'Olney Business Park',
#                                'locality': 'Olney',
#                                'postal_code': 'MK46 5FP',
#                                'region': 'Bucks'},
#  'registered_office_is_in_dispute': False,
#  'sic_codes': ['64999'],
#  'type': 'ltd',
#  'undeliverable_registered_office_address': False}
#
#
# Request Type: REGISTERED_OFFICE_ADDRESS
# ----------------------------------------
#
# {'address_line_1': '9 Osier Way',
#  'address_line_2': 'Olney Business Park',
#  'etag': '6c9366d83e49c0cb45a01188ed4db49fd8415496',
#  'kind': 'registered-office-address',
#  'links': {'self': '/company/04582994/registered-office-address'},
#  'locality': 'Olney',
#  'postal_code': 'MK46 5FP',
#  'region': 'Bucks'}
#
#
# Request Type: COMPANY_OFFICERS
# -------------------------------
#
# {'active_count': 4,
#  'etag': 'a1d5506d656eb5dfd834026732edfc4980b317fe',
#  'inactive_count': 0,
#  'items': [{'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2018-04-20',
#             'country_of_residence': 'United Kingdom',
#             'date_of_birth': {'month': 6, 'year': 1968},
#             'links': {'officer': {'appointments': '/officers/djgEQQjjbL5go1a9Uosd8LFV1sM/appointments'}},
#             'name': 'BASS, Matthew James',
#             'nationality': 'British',
#             'occupation': 'Director',
#             'officer_role': 'director'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2013-01-11',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 9, 'year': 1978},
#             'links': {'officer': {'appointments': '/officers/_HRYDuehM2yCxG89VwNn_K_IxHY/appointments'}},
#             'name': 'ENGLAND, Samuel Andrew',
#             'nationality': 'British',
#             'occupation': 'Commercial Director',
#             'officer_role': 'director'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2015-03-27',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 4, 'year': 1976},
#             'links': {'officer': {'appointments': '/officers/mshpTvnFIKXVsvuWtTIe4Z6MRXI/appointments'}},
#             'name': 'ROBBINS, Kevin Anthony',
#             'nationality': 'British',
#             'occupation': 'Director',
#             'officer_role': 'director'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2017-10-16',
#             'country_of_residence': 'United Kingdom',
#             'date_of_birth': {'month': 11, 'year': 1965},
#             'links': {'officer': {'appointments': '/officers/s2B--ZsyDD9GJ8pghtnwaQOG0Hs/appointments'}},
#             'name': 'TAILBY, Gordon',
#             'nationality': 'British',
#             'occupation': 'Director',
#             'officer_role': 'director'},
#            {'address': {'address_line_1': '6 West Street',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5HR',
#                         'region': 'Buckinghamshire'},
#             'appointed_on': '2003-10-23',
#             'links': {'officer': {'appointments': '/officers/9VqjU2UjaML7TF00aJAAmqPbEBo/appointments'}},
#             'name': 'ROBBINS, Debbie',
#             'officer_role': 'secretary',
#             'resigned_on': '2013-10-17'},
#            {'address': {'address_line_1': '16 Churchill Way',
#                         'locality': 'Cardiff',
#                         'postal_code': 'CF10 2DX'},
#             'appointed_on': '2002-11-06',
#             'links': {'officer': {'appointments': '/officers/fwDCpBl85F54DmEmvcpFDLK_yUc/appointments'}},
#             'name': 'SECRETARIAL APPOINTMENTS LIMITED',
#             'officer_role': 'corporate-nominee-secretary',
#             'resigned_on': '2003-01-10'},
#            {'address': {'address_line_1': 'Regency House',
#                         'address_line_2': 'Westminster Place York '
#                                           'Business Park',
#                         'locality': 'York',
#                         'postal_code': 'YO26 6RW',
#                         'region': 'North Yorkshire'},
#             'appointed_on': '2002-11-06',
#             'links': {'officer': {'appointments': '/officers/-HycfmvXdGQ-IVcvFAQL_kPGLQ0/appointments'}},
#             'name': 'TURNER LITTLE COMPANY SECRETARIES LIMITED',
#             'officer_role': 'corporate-nominee-secretary',
#             'resigned_on': '2003-10-23'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2013-01-11',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 6, 'year': 1982},
#             'links': {'officer': {'appointments': '/officers/PMpuZg1eIaefd0oHw5F1w57eU7M/appointments'}},
#             'name': 'BEDDALL, Marc Adam Philip',
#             'nationality': 'British',
#             'occupation': 'Finance Director',
#             'officer_role': 'director',
#             'resigned_on': '2018-04-19'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2013-01-11',
#             'country_of_residence': 'United Kingdom',
#             'date_of_birth': {'month': 3, 'year': 1966},
#             'links': {'officer': {'appointments': '/officers/mP6-4zkr2oPc9A1ESLiM0TV_0h8/appointments'}},
#             'name': 'DAY, Christopher',
#             'nationality': 'British',
#             'occupation': 'Operations Director',
#             'officer_role': 'director',
#             'resigned_on': '2019-03-25'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2015-09-14',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 6, 'year': 1990},
#             'links': {'officer': {'appointments': '/officers/MynMBG-igzk3X0bXWhfIR27n7ug/appointments'}},
#             'name': 'LARKINS, Benjamin',
#             'nationality': 'British',
#             'occupation': 'Sales Director',
#             'officer_role': 'director',
#             'resigned_on': '2017-03-31'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2013-01-11',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 6, 'year': 1990},
#             'links': {'officer': {'appointments': '/officers/i5igyA3bVaU2n-qqL0tJn8-XM0A/appointments'}},
#             'name': 'LARKINS, Benjamin',
#             'nationality': 'British',
#             'occupation': 'Sales Director',
#             'officer_role': 'director',
#             'resigned_on': '2015-05-11'},
#            {'address': {'address_line_1': 'Osier Way',
#                         'address_line_2': 'Olney Office Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9',
#                         'region': 'Buckinghamshire'},
#             'appointed_on': '2015-08-25',
#             'country_of_residence': 'England',
#             'date_of_birth': {'month': 1, 'year': 1981},
#             'links': {'officer': {'appointments': '/officers/yS0-wE97siQ47a-z-yx92B0g-s8/appointments'}},
#             'name': 'MALONEY, Jonathan Patrick',
#             'nationality': 'British',
#             'occupation': 'Director',
#             'officer_role': 'director',
#             'resigned_on': '2017-03-31'},
#            {'address': {'address_line_1': 'Olney Business Park',
#                         'country': 'United Kingdom',
#                         'locality': 'Olney',
#                         'postal_code': 'MK46 5FP',
#                         'premises': '9 Osier Way',
#                         'region': 'Bucks'},
#             'appointed_on': '2002-11-06',
#             'country_of_residence': 'United Kingdom',
#             'date_of_birth': {'month': 3, 'year': 1980},
#             'links': {'officer': {'appointments': '/officers/hHQ5MbCORNZG5UcSO2ZxihND2sU/appointments'}},
#             'name': 'ROBBINS, Martin John',
#             'nationality': 'British',
#             'occupation': 'Director',
#             'officer_role': 'director',
#             'resigned_on': '2015-03-27'},
#            {'address': {'address_line_1': '16 Churchill Way',
#                         'locality': 'Cardiff',
#                         'postal_code': 'CF10 2DX'},
#             'appointed_on': '2002-11-06',
#             'links': {'officer': {'appointments': '/officers/zlFriInDEeobOsZ2xcrESHMjccE/appointments'}},
#             'name': 'CORPORATE APPOINTMENTS LIMITED',
#             'officer_role': 'corporate-nominee-director',
#             'resigned_on': '2003-01-10'},
#            {'address': {'address_line_1': '3411 Silverside Road Rodney '
#                                           'Building',
#                         'address_line_2': 'Suite 104',
#                         'country': 'Usa',
#                         'locality': 'Wilmington',
#                         'region': 'Delaware'},
#             'appointed_on': '2002-11-06',
#             'identification': {'identification_type': 'non-eea',
#                                'legal_authority': 'THE DELAWARE GENERAL '
#                                                   'CORPORATION LAW',
#                                'legal_form': 'UNITED STATES LLC',
#                                'place_registered': 'DELAWARE',
#                                'registration_number': '3592285'},
#             'links': {'officer': {'appointments': '/officers/D2Zo809Hn-1MuV28gOIBvaNG8SA/appointments'}},
#             'name': 'NATIONWIDE INVESTMENTS L L C',
#             'officer_role': 'corporate-director',
#             'resigned_on': '2011-07-04'},
#            {'address': {'address_line_1': '16 Churchill Way',
#                         'locality': 'Cardiff',
#                         'postal_code': 'CF10 2DX'},
#             'appointed_on': '2002-11-06',
#             'links': {'officer': {'appointments': '/officers/6IA0ATzRXDFWvVVGzF1SX_bvQXY/appointments'}},
#             'name': 'SECRETARIAL APPOINTMENTS LIMITED',
#             'officer_role': 'corporate-director',
#             'resigned_on': '2003-01-10'}],
#  'items_per_page': 35,
#  'kind': 'officer-list',
#  'links': {'self': '/company/04582994/officers'},
#  'resigned_count': 12,
#  'start_index': 0,
#  'total_results': 16}
#
#
# Request Type: CHARGES_LIST
# --------------------------
#
# {'items': [{'charge_number': 2,
#             'classification': {'description': 'Legal charge',
#                                'type': 'charge-description'},
#             'created_on': '2005-07-07',
#             'delivered_on': '2005-07-08',
#             'etag': 'ff2c7119738e7856bea896ad5cdbd86e9f66d3d4',
#             'links': {'self': '/company/04582994/charges/117s-7_ys419LBU-UrQ0JPDW9d0'},
#             'particulars': {'description': 'Central garage summerland '
#                                            'place minehead. By way of '
#                                            'fixed charge the benefit of '
#                                            'all covenants and rights '
#                                            'concerning the property and '
#                                            'plant machinery fixtures '
#                                            'fittings furniture equipment '
#                                            'implements and utensils the '
#                                            'goodwill of any business '
#                                            'carried on at the property '
#                                            'and the proceeds of any '
#                                            'insurance affecting the '
#                                            'property or assets.',
#                             'type': 'short-particulars'},
#             'persons_entitled': [{'name': 'National Westminster Bank PLC'}],
#             'satisfied_on': '2012-03-06',
#             'secured_details': {'description': 'All monies due or to '
#                                                'become due from the '
#                                                'company to the chargee on '
#                                                'any account whatsoever',
#                                 'type': 'amount-secured'},
#             'status': 'fully-satisfied',
#             'transactions': [{'delivered_on': '2005-07-08',
#                               'filing_type': 'create-charge-pre-2006-companies-act',
#                               'links': {'filing': '/company/04582994/filing-history/MDE1Mjc4NDk2MGFkaXF6a2N4'}},
#                              {'delivered_on': '2012-03-06',
#                               'filing_type': 'charge-satisfaction-pre-april-2013',
#                               'links': {'filing': '/company/04582994/filing-history/MzA1Mzk1MDA0NWFkaXF6a2N4'}}]},
#            {'charge_number': 1,
#             'classification': {'description': 'Debenture',
#                                'type': 'charge-description'},
#             'created_on': '2005-07-01',
#             'delivered_on': '2005-07-06',
#             'etag': 'edb0a11191a1f84d8646057ac26712b174ff873a',
#             'links': {'self': '/company/04582994/charges/D7EkoMPW0H3PGt6oZme4mD9F3mE'},
#             'particulars': {'description': 'Fixed and floating charges '
#                                            'over the undertaking and all '
#                                            'property and assets present '
#                                            'and future including goodwill '
#                                            'bookdebts uncalled capital '
#                                            'buildings fixtures fixed '
#                                            'plant and machinery.',
#                             'type': 'short-particulars'},
#             'persons_entitled': [{'name': 'National Westminster Bank PLC'}],
#             'satisfied_on': '2012-03-06',
#             'secured_details': {'description': 'All monies due or to '
#                                                'become due from the '
#                                                'company to the chargee on '
#                                                'any account whatsoever',
#                                 'type': 'amount-secured'},
#             'status': 'fully-satisfied',
#             'transactions': [{'delivered_on': '2005-07-06',
#                               'filing_type': 'create-charge-pre-2006-companies-act',
#                               'links': {'filing': '/company/04582994/filing-history/MDA0Njg2NTgwMWFkaXF6a2N4'}},
#                              {'delivered_on': '2012-03-06',
#                               'filing_type': 'charge-satisfaction-pre-april-2013',
#                               'links': {'filing': '/company/04582994/filing-history/MzA1Mzk0OTk3MmFkaXF6a2N4'}}]}],
#  'part_satisfied_count': 0,
#  'satisfied_count': 2,
#  'total_count': 2,
#  'unfiltered_count': 2}
#
#
# Request Type: CHARGE
# ---------------------
#
# {'charge_number': 2,
#  'classification': {'description': 'Legal charge',
#                     'type': 'charge-description'},
#  'created_on': '2005-07-07',
#  'delivered_on': '2005-07-08',
#  'etag': 'ff2c7119738e7856bea896ad5cdbd86e9f66d3d4',
#  'links': {'self': '/company/04582994/charges/117s-7_ys419LBU-UrQ0JPDW9d0'},
#  'particulars': {'description': 'Central garage summerland place minehead. '
#                                 'By way of fixed charge the benefit of all '
#                                 'covenants and rights concerning the '
#                                 'property and plant machinery fixtures '
#                                 'fittings furniture equipment implements '
#                                 'and utensils the goodwill of any business '
#                                 'carried on at the property and the '
#                                 'proceeds of any insurance affecting the '
#                                 'property or assets.',
#                  'type': 'short-particulars'},
#  'persons_entitled': [{'name': 'National Westminster Bank PLC'}],
#  'satisfied_on': '2012-03-06',
#  'secured_details': {'description': 'All monies due or to become due from '
#                                     'the company to the chargee on any '
#                                     'account whatsoever',
#                      'type': 'amount-secured'},
#  'status': 'fully-satisfied',
#  'transactions': [{'delivered_on': '2005-07-08',
#                    'filing_type': 'create-charge-pre-2006-companies-act',
#                    'links': {'filing': '/company/04582994/filing-history/MDE1Mjc4NDk2MGFkaXF6a2N4'}},
#                   {'delivered_on': '2012-03-06',
#                    'filing_type': 'charge-satisfaction-pre-april-2013',
#                    'links': {'filing': '/company/04582994/filing-history/MzA1Mzk1MDA0NWFkaXF6a2N4'}}]}





