# django imports
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min, Max, Sum, Count, Q
from django.contrib.auth.models import User

from decimal import Decimal

# app model imports
from core_agreement_crud.models import go_agreement_querydetail,\
                                go_account_transaction_summary, \
                                go_account_transaction_detail

from core.models import ncf_udd_advices, ncf_dd_schedule, ncf_datacash_drawdowns

from core_app_worldpay.models import Collection_WorldPay

from core_payments.models import receipt_record

from core.functions_shared import write_account_history

from .models import arrears_detail_arrear_level, \
                    arrears_summary_arrear_level, \
                    arrears_summary_agreement_level, \
                    receipt_allocations_by_agreement, \
                    receipt_allocations_by_arrears, \
                    receipt_allocations_by_detail, \
                    arrears_allocation_type, \
                    arrears_status, \
                    agent_allocations_control

# Python Imports
import datetime, decimal

# Process and Update Arrears records from DD Bounce notices.
def app_process_bacs_udd_arrears():

    # retrieve active status
    active_status = arrears_status.objects.get(arr_status_code='A')

    # retrieve all udd objects not already added to arrears module
    try:
        udd_agreements = ncf_udd_advices.objects.filter(dd_in_arrears_app=False)
    except ObjectDoesNotExist:
        udd_agreements = None

    # if unloaded arrears
    if udd_agreements:

        for udd_agreement in udd_agreements:

            wip_agreement_id = udd_agreement.agreement_id
            wip_dd_reference = udd_agreement.dd_reference
            wip_dd_original_process_date = udd_agreement.dd_original_process_date
            wip_dd_value = udd_agreement.dd_value
            wip_dd_return_description = udd_agreement.dd_return_description
            wip_file_name = udd_agreement.file_name

            # Get Due Date
            wip_due_date = get_due_date(wip_agreement_id, wip_dd_original_process_date)

            # Get Customer Details
            try:
                agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id, agreementclosedflag='901')
                wip_customernumber = agreement_detail.agreementcustomernumber
                wip_customername = agreement_detail.customercompany
                wip_agreement_type = agreement_detail.agreementdefname
            except ObjectDoesNotExist:
                agreement_detail = None
                wip_customernumber = 'NOTFOUND'
                wip_customername = 'NOTFOUND'
                wip_agreement_type = 'Lease Agreement'

            if agreement_detail:
                wip_allocate_charges = True
                wip_arrears_id = process_detail_arrear_level(wip_agreement_id,
                                                                  wip_dd_reference,
                                                                  wip_customernumber,
                                                                  wip_customername,
                                                                  wip_dd_original_process_date,
                                                                  wip_dd_value,
                                                                  wip_dd_return_description,
                                                                  wip_file_name,
                                                                  wip_agreement_type,
                                                                  wip_due_date,
                                                                  active_status,
                                                                  wip_allocate_charges)

                # if new arrears written, summarise up.
                if wip_arrears_id > 0:
                    process_summary_arrear_level(wip_agreement_id, wip_arrears_id, wip_due_date)
                    process_agreement_arrear_level(wip_agreement_id, wip_arrears_id)

            udd_agreement.dd_in_arrears_app = True
            udd_agreement.save()

    return True


# Process and Update Arrears records from DD Bounce notices.
def app_process_datacash_arrears():

    # retrieve active status
    active_status = arrears_status.objects.get(arr_status_code='A')

    # retrieve all udd objects not already added to arrears module
    try:
        datacash_agreements = ncf_datacash_drawdowns.objects.filter(dd_arrears_flag=True, dd_in_arrears_app=False)
    except ObjectDoesNotExist:
        datacash_agreements = None

    # if unloaded arrears
    if datacash_agreements:

        for datacash_agreement in datacash_agreements:

            wip_agreement_id = datacash_agreement.agreement_id
            wip_dd_reference = datacash_agreement.dd_reference
            wip_dd_original_process_date = datacash_agreement.dd_request_date
            wip_dd_value = datacash_agreement.dd_amount
            wip_dd_return_description = datacash_agreement.dd_response
            wip_file_name = 'datacash_drawdowns.xlsx'

            # Get Due Date
            wip_dd_due_date = datacash_agreement.dd_due_date
            wip_due_date = get_due_date(wip_agreement_id, wip_dd_due_date)

            # Get Customer Details
            try:
                agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id, agreementclosedflag='901')
                wip_customernumber = agreement_detail.agreementcustomernumber
                wip_customername = agreement_detail.customercompany
                wip_agreement_type = agreement_detail.agreementdefname
            except ObjectDoesNotExist:
                agreement_detail = None
                wip_customernumber = 'NOTFOUND'
                wip_customername = 'NOTFOUND'
                wip_agreement_type = 'Lease Agreement'

            if agreement_detail:
                wip_allocate_charges = False
                wip_arrears_id = process_detail_arrear_level(wip_agreement_id,
                                                                  wip_dd_reference,
                                                                  wip_customernumber,
                                                                  wip_customername,
                                                                  wip_dd_original_process_date,
                                                                  wip_dd_value,
                                                                  wip_dd_return_description,
                                                                  wip_file_name,
                                                                  wip_agreement_type,
                                                                  wip_due_date,
                                                                  active_status,
                                                                  wip_allocate_charges)

                # if new arrears written, summarise up.
                if wip_arrears_id > 0:
                    process_summary_arrear_level(wip_agreement_id, wip_arrears_id, wip_due_date)
                    process_agreement_arrear_level(wip_agreement_id, wip_arrears_id)

            datacash_agreement.dd_in_arrears_app = True
            datacash_agreement.save()

    return True


# Process and Update Non DD Arrears from payment schedule
def app_process_non_dd_arrears(wip_agreement_id):

    print(wip_agreement_id)
    # Get Agreemen and Customer Details
    try:
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=wip_agreement_id,
                                                                agreementclosedflag='901')
        wip_customernumber = agreement_detail.agreementcustomernumber
        wip_customername = agreement_detail.customercompany
        wip_agreement_type = agreement_detail.agreementdefname
        wip_agreement_start = agreement_detail.agreementfirstpaymentdate
    except ObjectDoesNotExist:
        agreement_detail = None
        wip_customernumber = 'NOTFOUND'
        wip_customername = 'NOTFOUND'
        wip_agreement_type = 'Lease Agreement'
        wip_agreement_start = '2001-01-01'

    if agreement_detail:

        print(agreement_detail)

        transaction_detail_extract = go_account_transaction_detail.objects.filter(agreementnumber=wip_agreement_id,
                                                                                  transactionsourceid='GO1',
                                                                                  transactiondate__lt=wip_agreement_start)

        if transaction_detail_extract:

            for transaction_detail in transaction_detail_extract:

                wip_dd_value = transaction_detail.transgrosspayment
                wip_dd_return_description = transaction_detail.transtypedesc
                wip_due_date = transaction_detail.transactiondate
                active_status = arrears_status.objects.get(arr_status_code='A')

                wip_allocate_charges = False
                wip_arrears_id = process_detail_non_dd_level(wip_agreement_id,
                                                             wip_customernumber,
                                                             wip_customername,
                                                             wip_dd_value,
                                                             wip_dd_return_description,
                                                             wip_agreement_type,
                                                             wip_due_date,
                                                             active_status,
                                                             wip_allocate_charges)

                # if new arrears written, summarise up.
                if wip_arrears_id > 0:
                    process_summary_non_dd_level(wip_agreement_id, wip_arrears_id, wip_due_date)
                    process_agreement_non_dd_level(wip_agreement_id, wip_arrears_id)


# Get Due Date associated with current arrears
def get_due_date(wip_agreement_id, wip_dd_original_process_date):

    # try:
    #     dict_due_date = ncf_dd_schedule.objects.filter(
    #         dd_process_date01__lte=wip_dd_original_process_date,
    #         dd_bounce_date01__gte=wip_dd_original_process_date
    #     ).aggregate(Min('dd_calendar_due_date'))
    #     wip_due_date = dict_due_date["dd_calendar_due_date__min"]
    # except ObjectDoesNotExist:
    #     wip_due_date = wip_dd_original_process_date

    wip_due_date = wip_dd_original_process_date

    # validate due date
    if wip_due_date:
        test_due_date = go_account_transaction_summary.objects. \
            filter(agreementnumber=wip_agreement_id,
                   transactiondate=wip_due_date,
                   transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')).first()
        try:
            wip_test_due_date = test_due_date.transactionsourceid
        except:
            # if an invalid due date for this agreement - allocate to the closest future due date
            dict_due_date = go_account_transaction_summary.objects. \
                filter(agreementnumber=wip_agreement_id,
                       transactiondate__gte=wip_dd_original_process_date,
                       transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')) \
                .aggregate(Min('transactiondate'))
            wip_due_date = dict_due_date["transactiondate__min"]

    # if still no due date to allocate against, get the nearest previous due date
    if not wip_due_date:
        dict_due_date = go_account_transaction_summary.objects. \
            filter(agreementnumber=wip_agreement_id,
                   transactiondate__lte=wip_dd_original_process_date,
                   transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')) \
            .aggregate(Max('transactiondate'))
        wip_due_date = dict_due_date["transactiondate__max"]

    return wip_due_date

# Process and write arrear detail objects
def process_detail_arrear_level(wip_agreement_id,
                                     wip_dd_reference,
                                     wip_customernumber,
                                     wip_customername,
                                     wip_dd_original_process_date,
                                     wip_dd_value,
                                     wip_dd_return_description,
                                     wip_file_name,
                                     wip_agreement_type,
                                     wip_due_date,
                                     active_status,
                                     wip_allocate_charges):


    # set tax rate based pn agreement type for now
    # TODO save as a system/agreement type parameter
    if wip_agreement_type == 'Hire Purchase':
        sales_tax_rate = 1.0
    else:
        sales_tax_rate = 1.2

    wip_next_id = 0

    print('Processing Arrears')
    # double check for object already processed
    try:
        arrears_details = arrears_detail_arrear_level.objects.filter(
            ard_agreement_id=wip_agreement_id,
            ard_effective_date=wip_dd_original_process_date,
            ard_reference=wip_dd_reference,
            ard_arrears_count='1',
            ard_file_name=wip_file_name)
    except ObjectDoesNotExist:
        arrears_details = None

    # if definitely not already written then write out the required arrears details
    if not arrears_details:

        # get the next arrears_id
        try:
            dict_last_id = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id) \
                .aggregate(Max('ard_arrears_id'))
            wip_last_id = dict_last_id["ard_arrears_id__max"]
        except ObjectDoesNotExist:
            wip_last_id = 0

        if not wip_last_id:
            wip_last_id = 0

        wip_next_id = wip_last_id + 1

        # get agreement phase - PRIMARY (SP1) or SECONDARY (SP2)
        try:
            agreement_phases = go_account_transaction_summary.objects. \
                filter(agreementnumber=wip_agreement_id,
                       transactiondate=wip_due_date,
                       transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')).first()
            agreement_phase = agreement_phases.transactionsourceid
        except ObjectDoesNotExist:
            agreement_phase = None


        # read through active profile allocations (value_gross = 0) for SP1 or SP2
        try:
            arrears_allocations = arrears_allocation_type.objects. \
                filter(arr_allocation_src_id=agreement_phase,
                       arr_allocation_applied_auto=True,
                       arr_allocation_status='A',
                       arr_allocation_value_gross__isnull=True). \
                order_by('arr_allocation_src_type_01')
        except ObjectDoesNotExist:
            arrears_allocations = None

        if arrears_allocations:

            wip_total_element_value = 0

            for arrears_allocation in arrears_allocations:

                wip_src_type1 = arrears_allocation.arr_allocation_src_type_01
                wip_src_type2 = arrears_allocation.arr_allocation_src_type_02

                try:
                    # get the expected profile value and write it
                    if arrears_allocation.arr_allocation_src_type_max == 1:
                        dict_profile_element_value1 = go_account_transaction_detail.objects. \
                            filter(agreementnumber=wip_agreement_id,
                                   transactiondate=wip_due_date,
                                   transactionsourceid=arrears_allocation.arr_allocation_src_id,
                                   transtypeid=wip_src_type1). \
                            aggregate(Sum('transnetpayment'), Sum('transgrosspayment') )
                        wip_element_value = dict_profile_element_value1["transnetpayment__sum"]
                        wip_gross_element_value = dict_profile_element_value1["transgrosspayment__sum"]
                    if arrears_allocation.arr_allocation_src_type_max == 2:
                            dict_profile_element_value2 = go_account_transaction_detail.objects. \
                                filter(agreementnumber=wip_agreement_id,
                                       transactiondate=wip_due_date,
                                       transactionsourceid=arrears_allocation.arr_allocation_src_id,
                                       transtypeid__in=[wip_src_type1,wip_src_type2]). \
                                aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
                            wip_element_value = dict_profile_element_value2["transnetpayment__sum"]
                            wip_gross_element_value = dict_profile_element_value2["transgrosspayment__sum"]
                except ObjectDoesNotExist:
                    wip_element_value = 0

                if not wip_element_value:
                    wip_element_value = 0

                if not wip_gross_element_value:
                    wip_gross_element_value = 0

                wrt_ard_agreement_id = wip_agreement_id
                wrt_ard_customernumber = wip_customernumber
                wrt_ard_customercompanyname = wip_customername
                wrt_ard_return_description = wip_dd_return_description
                wrt_ard_arrears_id = wip_next_id
                wrt_ard_arrears_charge_type = arrears_allocation
                wrt_ard_effective_date = wip_dd_original_process_date
                wrt_ard_due_date = wip_due_date
                wrt_ard_reference = wip_dd_reference
                wrt_ard_referencestrip = wip_dd_reference
                wrt_ard_arrears_count = 1
                wrt_ard_arrears_value_netofvat = wip_element_value
                # wrt_ard_arrears_value_grossofvat = wip_element_value * decimal.Decimal(sales_tax_rate)
                wrt_ard_arrears_value_grossofvat = wip_gross_element_value
                wrt_ard_arrears_last_date = datetime.date.today()
                wrt_ard_collected_count = 0
                wrt_ard_collected_value_netofvat = 0
                wrt_ard_collected_value_grossofvat = 0
                wrt_ard_collected_last_date = '2000-01-01'
                wrt_ard_writtenoff_count = 0
                wrt_ard_writtenoff_value_netofvat = 0
                wrt_ard_writtenoff_value_grossofvat = 0
                wrt_ard_writtenoff_last_date = '2000-01-01'
                wrt_ard_balance_value_netofvat = wrt_ard_arrears_value_netofvat - wrt_ard_collected_value_netofvat \
                                                 - wrt_ard_writtenoff_value_netofvat
                wrt_ard_balance_value_grossofvat = wrt_ard_arrears_value_grossofvat - wrt_ard_collected_value_grossofvat \
                                                   - wrt_ard_writtenoff_value_grossofvat
                wrt_ard_balance_last_date = datetime.date.today()
                wrt_ard_agent_id = None
                wrt_ard_status = active_status
                wrt_ard_status_date = datetime.date.today()
                wrt_ard_file_name = wip_file_name

                wip_total_element_value += wrt_ard_arrears_value_grossofvat

                # write object/row
                if wrt_ard_arrears_value_netofvat != 0:
                    arrears_detail_arrear_level.objects.create(
                        ard_agreement_id=wrt_ard_agreement_id,
                        ard_customernumber=wrt_ard_customernumber,
                        ard_customercompanyname=wrt_ard_customercompanyname,
                        ard_return_description = wrt_ard_return_description,
                        ard_arrears_id=wrt_ard_arrears_id,
                        ard_arrears_charge_type=wrt_ard_arrears_charge_type,
                        ard_effective_date=wrt_ard_effective_date,
                        ard_due_date=wrt_ard_due_date,
                        ard_reference=wrt_ard_reference,
                        ard_referencestrip=wrt_ard_referencestrip,
                        ard_arrears_count=wrt_ard_arrears_count,
                        ard_arrears_value_netofvat=wrt_ard_arrears_value_netofvat,
                        ard_arrears_value_grossofvat=wrt_ard_arrears_value_grossofvat,
                        ard_arrears_last_date=wrt_ard_arrears_last_date,
                        ard_collected_count=wrt_ard_collected_count,
                        ard_collected_value_netofvat=wrt_ard_collected_value_netofvat,
                        ard_collected_value_grossofvat=wrt_ard_collected_value_grossofvat,
                        ard_collected_last_date=wrt_ard_collected_last_date,
                        ard_writtenoff_count=wrt_ard_writtenoff_count,
                        ard_writtenoff_value_netofvat=wrt_ard_writtenoff_value_netofvat,
                        ard_writtenoff_value_grossofvat=wrt_ard_writtenoff_value_grossofvat,
                        ard_writtenoff_last_date=wrt_ard_writtenoff_last_date,
                        ard_balance_value_netofvat=wrt_ard_balance_value_netofvat,
                        ard_balance_value_grossofvat=wrt_ard_balance_value_grossofvat,
                        ard_balance_last_date=wrt_ard_balance_last_date,
                        ard_agent_id=wrt_ard_agent_id,
                        ard_status=wrt_ard_status,
                        ard_status_date=wrt_ard_status_date,
                        ard_file_name=wrt_ard_file_name
                    )

            # if variance between profile and dd bounce value
            wip_variance = wip_total_element_value - wip_dd_value
            if wip_variance != 0:

                try:
                    charge_allocation = arrears_allocation_type.objects. \
                        get(arr_allocation_code='PROFILE_VARIANCE')
                except ObjectDoesNotExist:
                    charge_allocation = None

                wrt_ard_agreement_id = wip_agreement_id
                wrt_ard_customernumber = wip_customernumber
                wrt_ard_customercompanyname = wip_customername
                wrt_ard_return_description = wip_dd_return_description
                wrt_ard_arrears_id = wip_next_id
                wrt_ard_arrears_charge_type = charge_allocation
                wrt_ard_effective_date = wip_dd_original_process_date
                wrt_ard_due_date = wip_due_date
                wrt_ard_reference = wip_dd_reference
                wrt_ard_referencestrip = wip_dd_reference
                wrt_ard_arrears_count = 0
                wrt_ard_arrears_value_netofvat = round((wip_variance/decimal.Decimal(sales_tax_rate)),2)
                wrt_ard_arrears_value_grossofvat = wip_variance
                wrt_ard_arrears_last_date = datetime.date.today()
                wrt_ard_collected_count = 0
                wrt_ard_collected_value_netofvat = 0
                wrt_ard_collected_value_grossofvat = 0
                wrt_ard_collected_last_date = '2000-01-01'
                wrt_ard_writtenoff_count = 0
                wrt_ard_writtenoff_value_netofvat = 0
                wrt_ard_writtenoff_value_grossofvat = 0
                wrt_ard_writtenoff_last_date = '2000-01-01'
                wrt_ard_balance_value_netofvat = wrt_ard_arrears_value_netofvat - wrt_ard_collected_value_netofvat \
                                                 - wrt_ard_writtenoff_value_netofvat
                wrt_ard_balance_value_grossofvat = wrt_ard_arrears_value_grossofvat - wrt_ard_collected_value_grossofvat \
                                                   - wrt_ard_writtenoff_value_grossofvat
                wrt_ard_balance_last_date = datetime.date.today()
                wrt_ard_agent_id = None
                wrt_ard_status = active_status
                wrt_ard_status_date = datetime.date.today()
                wrt_ard_file_name = wip_file_name

                # write object/row
                if wrt_ard_arrears_value_netofvat != 0:
                    arrears_detail_arrear_level.objects.create(
                        ard_agreement_id=wrt_ard_agreement_id,
                        ard_customernumber=wrt_ard_customernumber,
                        ard_customercompanyname=wrt_ard_customercompanyname,
                        ard_arrears_id=wrt_ard_arrears_id,
                        ard_arrears_charge_type=wrt_ard_arrears_charge_type,
                        ard_return_description=wrt_ard_return_description,
                        ard_effective_date=wrt_ard_effective_date,
                        ard_due_date=wrt_ard_due_date,
                        ard_reference=wrt_ard_reference,
                        ard_referencestrip=wrt_ard_referencestrip,
                        ard_arrears_count=wrt_ard_arrears_count,
                        ard_arrears_value_netofvat=wrt_ard_arrears_value_netofvat,
                        ard_arrears_value_grossofvat=wrt_ard_arrears_value_grossofvat,
                        ard_arrears_last_date=wrt_ard_arrears_last_date,
                        ard_collected_count=wrt_ard_collected_count,
                        ard_collected_value_netofvat=wrt_ard_collected_value_netofvat,
                        ard_collected_value_grossofvat=wrt_ard_collected_value_grossofvat,
                        ard_collected_last_date=wrt_ard_collected_last_date,
                        ard_writtenoff_count=wrt_ard_writtenoff_count,
                        ard_writtenoff_value_netofvat=wrt_ard_writtenoff_value_netofvat,
                        ard_writtenoff_value_grossofvat=wrt_ard_writtenoff_value_grossofvat,
                        ard_writtenoff_last_date=wrt_ard_writtenoff_last_date,
                        ard_balance_value_netofvat=wrt_ard_balance_value_netofvat,
                        ard_balance_value_grossofvat=wrt_ard_balance_value_grossofvat,
                        ard_balance_last_date=wrt_ard_balance_last_date,
                        ard_agent_id=wrt_ard_agent_id,
                        ard_status=wrt_ard_status,
                        ard_status_date=wrt_ard_status_date,
                        ard_file_name=wrt_ard_file_name
                    )

        # now read through active charge allocations (value_gross <> 0) for SP1 or SP2
        if wip_allocate_charges:

            try:
                charge_allocations = arrears_allocation_type.objects. \
                    filter(arr_allocation_src_id=agreement_phase,
                           arr_allocation_applied_auto=True,
                           arr_allocation_status='A',
                           arr_allocation_value_gross__isnull=False)
            except ObjectDoesNotExist:
                charge_allocations = None

            if charge_allocations:

                wip_charge_total = 0

                for charge_allocation in charge_allocations:

                    wrt_ard_agreement_id = wip_agreement_id
                    wrt_ard_customernumber = wip_customernumber
                    wrt_ard_customercompanyname = wip_customername
                    wrt_ard_return_description = wip_dd_return_description
                    wrt_ard_arrears_id = wip_next_id
                    wrt_ard_arrears_charge_type = charge_allocation
                    wrt_ard_effective_date = wip_dd_original_process_date
                    wrt_ard_due_date = wip_due_date
                    wrt_ard_reference = wip_dd_reference
                    wrt_ard_referencestrip = wip_dd_reference
                    wrt_ard_arrears_count = 0
                    wrt_ard_arrears_value_netofvat = charge_allocation.arr_allocation_value_net
                    wrt_ard_arrears_value_grossofvat = charge_allocation.arr_allocation_value_gross
                    wrt_ard_arrears_last_date = datetime.date.today()
                    wrt_ard_collected_count = 0
                    wrt_ard_collected_value_netofvat = 0
                    wrt_ard_collected_value_grossofvat = 0
                    wrt_ard_collected_last_date = '2000-01-01'
                    wrt_ard_writtenoff_count = 0
                    wrt_ard_writtenoff_value_netofvat = 0
                    wrt_ard_writtenoff_value_grossofvat = 0
                    wrt_ard_writtenoff_last_date = '2000-01-01'
                    wrt_ard_balance_value_netofvat = wrt_ard_arrears_value_netofvat - wrt_ard_collected_value_netofvat \
                                                     - wrt_ard_writtenoff_value_netofvat
                    wrt_ard_balance_value_grossofvat = wrt_ard_arrears_value_grossofvat - wrt_ard_collected_value_grossofvat \
                                                       - wrt_ard_writtenoff_value_grossofvat
                    wrt_ard_balance_last_date = datetime.date.today()
                    wrt_ard_agent_id = None
                    wrt_ard_status = active_status
                    wrt_ard_status_date = datetime.date.today()
                    wrt_ard_file_name = wip_file_name

                    # write object/row
                    if wrt_ard_arrears_value_netofvat != 0:

                        arrears_detail_arrear_level.objects.create(
                            ard_agreement_id=wrt_ard_agreement_id,
                            ard_customernumber=wrt_ard_customernumber,
                            ard_customercompanyname=wrt_ard_customercompanyname,
                            ard_arrears_id=wrt_ard_arrears_id,
                            ard_arrears_charge_type=wrt_ard_arrears_charge_type,
                            ard_return_description = wrt_ard_return_description,
                            ard_effective_date=wrt_ard_effective_date,
                            ard_due_date=wrt_ard_due_date,
                            ard_reference=wrt_ard_reference,
                            ard_referencestrip=wrt_ard_referencestrip,
                            ard_arrears_count=wrt_ard_arrears_count,
                            ard_arrears_value_netofvat=wrt_ard_arrears_value_netofvat,
                            ard_arrears_value_grossofvat=wrt_ard_arrears_value_grossofvat,
                            ard_arrears_last_date=wrt_ard_arrears_last_date,
                            ard_collected_count=wrt_ard_collected_count,
                            ard_collected_value_netofvat=wrt_ard_collected_value_netofvat,
                            ard_collected_value_grossofvat=wrt_ard_collected_value_grossofvat,
                            ard_collected_last_date=wrt_ard_collected_last_date,
                            ard_writtenoff_count=wrt_ard_writtenoff_count,
                            ard_writtenoff_value_netofvat=wrt_ard_writtenoff_value_netofvat,
                            ard_writtenoff_value_grossofvat=wrt_ard_writtenoff_value_grossofvat,
                            ard_writtenoff_last_date=wrt_ard_writtenoff_last_date,
                            ard_balance_value_netofvat=wrt_ard_balance_value_netofvat,
                            ard_balance_value_grossofvat=wrt_ard_balance_value_grossofvat,
                            ard_balance_last_date=wrt_ard_balance_last_date,
                            ard_agent_id=wrt_ard_agent_id,
                            ard_status=wrt_ard_status,
                            ard_status_date=wrt_ard_status_date,
                            ard_file_name=wrt_ard_file_name
                        )

                        wip_charge_total = wip_charge_total + wrt_ard_balance_value_grossofvat

                #   Write History
                if wip_charge_total != 0:
                    if not isinstance(wip_due_date, datetime.datetime):
                        my_time = datetime.datetime.min.time()
                        wip_due_date = datetime.datetime.combine(wip_due_date, my_time)

                    wip_due_date_text = wip_due_date.strftime('%d/%m/%Y')

                    # Call Function to write Account History
                    write_account_history(wip_agreement_id,
                                          wip_due_date,
                                          'GO9',
                                          '0',
                                          'Col',
                                          wip_charge_total,
                                          'GROSS',
                                          0,
                                          0,
                                          None,
                                          'Bounce Fees for ' + wip_due_date_text)

    return wip_next_id

def process_summary_arrear_level(wip_agreement_id, wip_arrears_id, wip_due_date):

    # Get aggregate values for this arrears id
    try:
        dict_arrears_totals = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                         ard_arrears_id=wip_arrears_id) \
            .aggregate(Sum('ard_arrears_value_netofvat'),
                       Sum('ard_arrears_value_grossofvat'),
                       Sum('ard_collected_value_netofvat'),
                       Sum('ard_collected_value_grossofvat'),
                       Sum('ard_writtenoff_value_netofvat'),
                       Sum('ard_writtenoff_value_grossofvat'),
                       Sum('ard_balance_value_netofvat'),
                       Sum('ard_balance_value_grossofvat'))
        wip_arrears_value_netofvat = dict_arrears_totals["ard_arrears_value_netofvat__sum"]
        wip_arrears_value_grossofvat = dict_arrears_totals["ard_arrears_value_grossofvat__sum"]
        wip_collected_value_netofvat = dict_arrears_totals["ard_collected_value_netofvat__sum"]
        wip_collected_value_grossofvat = dict_arrears_totals["ard_collected_value_grossofvat__sum"]
        wip_writtenoff_value_netofvat = dict_arrears_totals["ard_writtenoff_value_netofvat__sum"]
        wip_writtenoff_value_grossofvat = dict_arrears_totals["ard_writtenoff_value_grossofvat__sum"]
        wip_balance_value_netofvat = dict_arrears_totals["ard_balance_value_netofvat__sum"]
        wip_balance_value_grossofvat = dict_arrears_totals["ard_balance_value_grossofvat__sum"]

    except ObjectDoesNotExist:

        wip_arrears_value_netofvat = 0
        wip_arrears_value_grossofvat = 0
        wip_collected_value_netofvat = 0
        wip_collected_value_grossofvat = 0
        wip_writtenoff_value_netofvat = 0
        wip_writtenoff_value_grossofvat = 0
        wip_balance_value_netofvat = 0
        wip_balance_value_grossofvat = 0

    if wip_arrears_value_netofvat != 0:

        # Get baseline values for this arrears id
        try:
            baseline = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                             ard_arrears_id=wip_arrears_id) \
                                    .first()
        except ObjectDoesNotExist:
            baseline = None

        if baseline:

            # get agreement phase - PRIMARY (SP1) or SECONDARY (SP2)
            try:
                agreement_phases = go_account_transaction_summary.objects. \
                    filter(agreementnumber=wip_agreement_id,
                           transactiondate=wip_due_date,
                           transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')).first()
                wip_agreement_phase = agreement_phases.transactionsourceid
            except ObjectDoesNotExist:
                wip_agreement_phase = None

            wrt_ara_agreement_id = baseline.ard_agreement_id
            wrt_ara_customernumber = baseline.ard_customernumber
            wrt_ara_customercompanyname = baseline.ard_customercompanyname
            wrt_ara_return_description = baseline.ard_return_description
            wrt_ara_arrears_id = baseline.ard_arrears_id
            wrt_ara_effective_date = baseline.ard_effective_date
            wrt_ara_due_date = baseline.ard_due_date
            wrt_ara_transactionsourceid = wip_agreement_phase
            wrt_ara_reference = baseline.ard_reference
            wrt_ara_referencestrip = baseline.ard_referencestrip
            wrt_ara_arrears_last_date = baseline.ard_arrears_last_date
            wrt_ara_collected_count = baseline.ard_collected_count
            wrt_ara_collected_last_date = baseline.ard_collected_last_date
            wrt_ara_writtenoff_count = baseline.ard_writtenoff_count
            wrt_ara_writtenoff_last_date = baseline.ard_writtenoff_last_date
            wrt_ara_balance_last_date = baseline.ard_balance_last_date
            wrt_ara_agent_id = baseline.ard_agent_id
            wrt_ara_status = baseline.ard_status
            wrt_ara_status_date = baseline.ard_status_date
            wrt_ara_file_name = baseline.ard_file_name

            arrears_summary_arrear_level.objects.create(
                ara_agreement_id=wrt_ara_agreement_id,
                ara_customernumber=wrt_ara_customernumber,
                ara_customercompanyname=wrt_ara_customercompanyname,
                ara_arrears_id=wrt_ara_arrears_id,
                ara_return_description=wrt_ara_return_description,
                ara_effective_date=wrt_ara_effective_date,
                ara_due_date=wrt_ara_due_date,
                ara_transactionsourceid=wrt_ara_transactionsourceid,
                ara_reference=wrt_ara_reference,
                ara_referencestrip=wrt_ara_referencestrip,
                ara_arrears_value_netofvat=wip_arrears_value_netofvat,
                ara_arrears_value_grossofvat=wip_arrears_value_grossofvat,
                ara_arrears_last_date=wrt_ara_arrears_last_date,
                ara_collected_count=wrt_ara_collected_count,
                ara_collected_value_netofvat=wip_collected_value_netofvat,
                ara_collected_value_grossofvat=wip_collected_value_grossofvat,
                ara_collected_last_date=wrt_ara_collected_last_date,
                ara_writtenoff_count=wrt_ara_writtenoff_count,
                ara_writtenoff_value_netofvat=wip_writtenoff_value_netofvat,
                ara_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat,
                ara_writtenoff_last_date=wrt_ara_writtenoff_last_date,
                ara_balance_value_netofvat=wip_balance_value_netofvat,
                ara_balance_value_grossofvat=wip_balance_value_grossofvat,
                ara_balance_last_date=wrt_ara_balance_last_date,
                ara_agent_id=wrt_ara_agent_id,
                ara_status=wrt_ara_status,
                ara_status_date=wrt_ara_status_date,
                ara_file_name=wrt_ara_file_name
            )


def process_agreement_arrear_level(wip_agreement_id, wip_arrears_id):

    # Get values for this arrears id
    try:
        arrears_level_totals = arrears_summary_arrear_level.objects.get(ara_agreement_id=wip_agreement_id,
                                                                         ara_arrears_id=wip_arrears_id)

    except ObjectDoesNotExist:

        arrears_level_totals = None

    if arrears_level_totals:

        # get base info for arrears - used when creating new agreement level object
        wip_agreement_id = arrears_level_totals.ara_agreement_id
        wip_customernumber = arrears_level_totals.ara_customernumber
        wip_customercompanyname = arrears_level_totals.ara_customercompanyname
        wip_arrears_last_date = arrears_level_totals.ara_arrears_last_date
        wip_status_date = arrears_level_totals.ara_status_date
        # wip_agent_id_id = arrears_level_totals.ara_agent_id
        wip_status_id = arrears_level_totals.ara_status

        # get totals from arrears details
        dict_arrears_totals = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id) \
            .aggregate(Sum('ard_arrears_value_netofvat'),
                       Sum('ard_arrears_value_grossofvat'),
                       Sum('ard_collected_value_netofvat'),
                       Sum('ard_collected_value_grossofvat'),
                       Sum('ard_writtenoff_value_netofvat'),
                       Sum('ard_writtenoff_value_grossofvat'),
                       Sum('ard_balance_value_netofvat'),
                       Sum('ard_balance_value_grossofvat'),
                       Sum('ard_arrears_count'),
                       Sum('ard_collected_count'),
                       Sum('ard_writtenoff_count')
                       )

        wip_arrears_value_netofvat = dict_arrears_totals["ard_arrears_value_netofvat__sum"]
        wip_arrears_value_grossofvat = dict_arrears_totals["ard_arrears_value_grossofvat__sum"]
        wip_collected_value_netofvat = dict_arrears_totals["ard_collected_value_netofvat__sum"]
        wip_collected_value_grossofvat = dict_arrears_totals["ard_collected_value_grossofvat__sum"]
        wip_writtenoff_value_netofvat = dict_arrears_totals["ard_writtenoff_value_netofvat__sum"]
        wip_writtenoff_value_grossofvat = dict_arrears_totals["ard_writtenoff_value_grossofvat__sum"]
        wip_balance_value_netofvat = dict_arrears_totals["ard_balance_value_netofvat__sum"]
        wip_balance_value_grossofvat = dict_arrears_totals["ard_balance_value_grossofvat__sum"]
        wip_arrears_count = dict_arrears_totals["ard_arrears_count__sum"]
        wip_collected_count = dict_arrears_totals["ard_collected_count__sum"]
        wip_writtenoff_count = dict_arrears_totals["ard_writtenoff_count__sum"]

        try:
            existing_agreement_level_arrear = arrears_summary_agreement_level.objects\
                                                            .get(arr_agreement_id=wip_agreement_id)
        except ObjectDoesNotExist:
            existing_agreement_level_arrear = None

        # Get Unallocated receipts
        unallocated_by_agreement = receipt_allocations_by_agreement.objects.filter(
            rag_agreement_id=wip_agreement_id).first()
        if unallocated_by_agreement:
            xip_unallocated_value_netofvat = unallocated_by_agreement.unallocated_value_netofvat
            xip_unallocated_value_grossofvat = unallocated_by_agreement.unallocated_value_grossofvat
            xip_unallocated_last_date = unallocated_by_agreement.unallocated_last_date
        else:
            xip_unallocated_value_netofvat = 0
            xip_unallocated_value_grossofvat = 0
            xip_unallocated_last_date = wip_status_date

        if existing_agreement_level_arrear:

            existing_agreement_level_arrear.arr_arrears_count=wip_arrears_count
            existing_agreement_level_arrear.arr_arrears_value_netofvat=wip_arrears_value_netofvat
            existing_agreement_level_arrear.arr_arrears_value_grossofvat=wip_arrears_value_grossofvat
            existing_agreement_level_arrear.arr_arrears_last_date=wip_arrears_last_date
            existing_agreement_level_arrear.arr_collected_count=wip_collected_count
            existing_agreement_level_arrear.arr_collected_value_netofvat=wip_collected_value_netofvat
            existing_agreement_level_arrear.arr_collected_value_grossofvat=wip_collected_value_grossofvat
            existing_agreement_level_arrear.arr_writtenoff_count=wip_writtenoff_count
            existing_agreement_level_arrear.arr_writtenoff_value_netofvat=wip_writtenoff_value_netofvat
            existing_agreement_level_arrear.arr_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat
            existing_agreement_level_arrear.arr_balance_value_netofvat=wip_balance_value_netofvat
            existing_agreement_level_arrear.arr_balance_value_grossofvat=wip_balance_value_grossofvat
            existing_agreement_level_arrear.arr_balance_last_date=wip_arrears_last_date
            existing_agreement_level_arrear.arr_status_date=wip_status_date
            existing_agreement_level_arrear.arr_unallocated_value_netofvat = xip_unallocated_value_netofvat
            existing_agreement_level_arrear.arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat
            existing_agreement_level_arrear.arr_unallocated_last_date = xip_unallocated_last_date
            existing_agreement_level_arrear.arr_status_id=1
            existing_agreement_level_arrear.save()

        else:

            arrears_summary_agreement_level.objects.create(
                arr_agreement_id=wip_agreement_id,
                arr_customernumber=wip_customernumber,
                arr_customercompanyname=wip_customercompanyname,
                arr_arrears_count=wip_arrears_count,
                arr_arrears_value_netofvat=wip_arrears_value_netofvat,
                arr_arrears_value_grossofvat=wip_arrears_value_grossofvat,
                arr_arrears_last_date=wip_arrears_last_date,
                arr_collected_count=wip_collected_count,
                arr_collected_value_netofvat=wip_collected_value_netofvat,
                arr_collected_value_grossofvat=wip_collected_value_grossofvat,
                arr_collected_last_date='2000-01-01',
                arr_writtenoff_count=wip_writtenoff_count,
                arr_writtenoff_value_netofvat=wip_writtenoff_value_netofvat,
                arr_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat,
                arr_writtenoff_last_date='2000-01-01',
                arr_balance_value_netofvat=wip_balance_value_netofvat,
                arr_balance_value_grossofvat=wip_balance_value_grossofvat,
                arr_balance_last_date=wip_arrears_last_date,
                arr_status_date=wip_status_date,
                arr_unallocated_value_netofvat = xip_unallocated_value_netofvat,
                arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat,
                arr_unallocated_last_date = xip_unallocated_last_date,
                # arr_agent_id_id=wip_agent_id_id,
                arr_status_id=1
            )


def process_detail_non_dd_level(wip_agreement_id,
                                     wip_customernumber,
                                     wip_customername,
                                     wip_dd_value,
                                     wip_dd_return_description,
                                     wip_agreement_type,
                                     wip_due_date,
                                     active_status,
                                     wip_allocate_charges):


    # set tax rate based pn agreement type for now
    # TODO save as a system/agreement type parameter
    if wip_agreement_type == 'Hire Purchase':
        sales_tax_rate = 1.0
    else:
        sales_tax_rate = 1.2

    wip_next_id = 0

    # double check for object already processed
    try:
        arrears_details = arrears_detail_arrear_level.objects.filter(
            ard_agreement_id=wip_agreement_id,
            ard_effective_date=wip_due_date,
            ard_return_description=wip_dd_return_description,
            ard_reference='',
            ard_arrears_count='1')
    except ObjectDoesNotExist:
        arrears_details = None

    # if definitely not already written then write out the required arrears details
    if not arrears_details:

        # get the next arrears_id
        try:
            dict_last_id = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id) \
                .aggregate(Max('ard_arrears_id'))
            wip_last_id = dict_last_id["ard_arrears_id__max"]
        except ObjectDoesNotExist:
            wip_last_id = 0

        if not wip_last_id:
            wip_last_id = 0

        wip_next_id = wip_last_id + 1

        # get agreement phase - PRIMARY (SP1) or SECONDARY (SP2)
        try:
            agreement_phases = go_account_transaction_summary.objects. \
                filter(agreementnumber=wip_agreement_id,
                       transactiondate=wip_due_date,
                       transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')).first()
            agreement_phase = agreement_phases.transactionsourceid
        except ObjectDoesNotExist:
            agreement_phase = None


        # read through active profile allocations (value_gross = 0) for SP1 or SP2
        try:
            arrears_allocations = arrears_allocation_type.objects. \
                filter(arr_allocation_description=wip_dd_return_description,
                       arr_allocation_applied_auto=True,
                       arr_allocation_status='A',
                       arr_allocation_value_gross__isnull=True). \
                order_by('arr_allocation_src_type_01')
        except ObjectDoesNotExist:
            arrears_allocations = None

        if arrears_allocations:

            wip_total_element_value = 0

            for arrears_allocation in arrears_allocations:

                wip_src_type1 = arrears_allocation.arr_allocation_src_type_01
                wip_src_type2 = arrears_allocation.arr_allocation_src_type_02

                try:
                    dict_profile_element_value1 = go_account_transaction_detail.objects. \
                        filter(agreementnumber=wip_agreement_id,
                               transactiondate=wip_due_date,
                               transactionsourceid='GO1',
                               transtypedesc=wip_dd_return_description). \
                        aggregate(Sum('transnetpayment'), Sum('transgrosspayment'))
                    wip_element_value = dict_profile_element_value1["transnetpayment__sum"]
                    wip_gross_element_value = dict_profile_element_value1["transgrosspayment__sum"]
                except ObjectDoesNotExist:
                    wip_element_value = 0
                    wip_gross_element_value = 0

                if not wip_element_value:
                    wip_element_value = 0

                if not wip_gross_element_value:
                    wip_gross_element_value = 0

                wrt_ard_agreement_id = wip_agreement_id
                wrt_ard_customernumber = wip_customernumber
                wrt_ard_customercompanyname = wip_customername
                wrt_ard_return_description = wip_dd_return_description
                wrt_ard_arrears_id = wip_next_id
                wrt_ard_arrears_charge_type = arrears_allocation
                wrt_ard_effective_date = wip_due_date
                wrt_ard_due_date = wip_due_date
                wrt_ard_reference = ''
                wrt_ard_referencestrip = ''
                wrt_ard_arrears_count = 1
                wrt_ard_arrears_value_netofvat = wip_element_value
                # wrt_ard_arrears_value_grossofvat = wip_element_value * decimal.Decimal(sales_tax_rate)
                wrt_ard_arrears_value_grossofvat = wip_gross_element_value
                wrt_ard_arrears_last_date = datetime.date.today()
                wrt_ard_collected_count = 0
                wrt_ard_collected_value_netofvat = 0
                wrt_ard_collected_value_grossofvat = 0
                wrt_ard_collected_last_date = '2000-01-01'
                wrt_ard_writtenoff_count = 0
                wrt_ard_writtenoff_value_netofvat = 0
                wrt_ard_writtenoff_value_grossofvat = 0
                wrt_ard_writtenoff_last_date = '2000-01-01'
                wrt_ard_balance_value_netofvat = wrt_ard_arrears_value_netofvat - wrt_ard_collected_value_netofvat \
                                                 - wrt_ard_writtenoff_value_netofvat
                wrt_ard_balance_value_grossofvat = wrt_ard_arrears_value_grossofvat - wrt_ard_collected_value_grossofvat \
                                                   - wrt_ard_writtenoff_value_grossofvat
                wrt_ard_balance_last_date = datetime.date.today()
                wrt_ard_agent_id = None
                wrt_ard_status = active_status
                wrt_ard_status_date = datetime.date.today()
                wrt_ard_file_name = ''

                wip_total_element_value += wrt_ard_arrears_value_grossofvat
                wrt_ard_agent_id = User.objects.filter(username='accounts.admin').first()

                # write object/row
                if wrt_ard_arrears_value_netofvat != 0:
                    arrears_detail_arrear_level.objects.create(
                        ard_agreement_id=wrt_ard_agreement_id,
                        ard_customernumber=wrt_ard_customernumber,
                        ard_customercompanyname=wrt_ard_customercompanyname,
                        ard_return_description = wrt_ard_return_description,
                        ard_arrears_id=wrt_ard_arrears_id,
                        ard_arrears_charge_type=wrt_ard_arrears_charge_type,
                        ard_effective_date=wrt_ard_effective_date,
                        ard_due_date=wrt_ard_due_date,
                        ard_reference=wrt_ard_reference,
                        ard_referencestrip=wrt_ard_referencestrip,
                        ard_arrears_count=wrt_ard_arrears_count,
                        ard_arrears_value_netofvat=wrt_ard_arrears_value_netofvat,
                        ard_arrears_value_grossofvat=wrt_ard_arrears_value_grossofvat,
                        ard_arrears_last_date=wrt_ard_arrears_last_date,
                        ard_collected_count=wrt_ard_collected_count,
                        ard_collected_value_netofvat=wrt_ard_collected_value_netofvat,
                        ard_collected_value_grossofvat=wrt_ard_collected_value_grossofvat,
                        ard_collected_last_date=wrt_ard_collected_last_date,
                        ard_writtenoff_count=wrt_ard_writtenoff_count,
                        ard_writtenoff_value_netofvat=wrt_ard_writtenoff_value_netofvat,
                        ard_writtenoff_value_grossofvat=wrt_ard_writtenoff_value_grossofvat,
                        ard_writtenoff_last_date=wrt_ard_writtenoff_last_date,
                        ard_balance_value_netofvat=wrt_ard_balance_value_netofvat,
                        ard_balance_value_grossofvat=wrt_ard_balance_value_grossofvat,
                        ard_balance_last_date=wrt_ard_balance_last_date,
                        ard_agent_id=wrt_ard_agent_id,
                        ard_status=wrt_ard_status,
                        ard_status_date=wrt_ard_status_date,
                        ard_file_name=wrt_ard_file_name
                    )

            # if variance between profile and dd bounce value
            wip_variance = wip_total_element_value - wip_dd_value
            if wip_variance != 0:

                try:
                    charge_allocation = arrears_allocation_type.objects. \
                        get(arr_allocation_code='PROFILE_VARIANCE')
                except ObjectDoesNotExist:
                    charge_allocation = None

                wrt_ard_agreement_id = wip_agreement_id
                wrt_ard_customernumber = wip_customernumber
                wrt_ard_customercompanyname = wip_customername
                wrt_ard_return_description = wip_dd_return_description
                wrt_ard_arrears_id = wip_next_id
                wrt_ard_arrears_charge_type = charge_allocation
                wrt_ard_effective_date = wip_due_date
                wrt_ard_due_date = wip_due_date
                wrt_ard_reference = ''
                wrt_ard_referencestrip = ''
                wrt_ard_arrears_count = 0
                wrt_ard_arrears_value_netofvat = round((wip_variance/decimal.Decimal(sales_tax_rate)),2)
                wrt_ard_arrears_value_grossofvat = wip_variance
                wrt_ard_arrears_last_date = datetime.date.today()
                wrt_ard_collected_count = 0
                wrt_ard_collected_value_netofvat = 0
                wrt_ard_collected_value_grossofvat = 0
                wrt_ard_collected_last_date = '2000-01-01'
                wrt_ard_writtenoff_count = 0
                wrt_ard_writtenoff_value_netofvat = 0
                wrt_ard_writtenoff_value_grossofvat = 0
                wrt_ard_writtenoff_last_date = '2000-01-01'
                wrt_ard_balance_value_netofvat = wrt_ard_arrears_value_netofvat - wrt_ard_collected_value_netofvat \
                                                 - wrt_ard_writtenoff_value_netofvat
                wrt_ard_balance_value_grossofvat = wrt_ard_arrears_value_grossofvat - wrt_ard_collected_value_grossofvat \
                                                   - wrt_ard_writtenoff_value_grossofvat
                wrt_ard_balance_last_date = datetime.date.today()
                wrt_ard_agent_id = None
                wrt_ard_status = active_status
                wrt_ard_status_date = datetime.date.today()
                wrt_ard_file_name = ''

                wrt_ard_agent_id = User.objects.filter(username='accounts.admin').first()

                # write object/row
                if wrt_ard_arrears_value_netofvat != 0:
                    arrears_detail_arrear_level.objects.create(
                        ard_agreement_id=wrt_ard_agreement_id,
                        ard_customernumber=wrt_ard_customernumber,
                        ard_customercompanyname=wrt_ard_customercompanyname,
                        ard_arrears_id=wrt_ard_arrears_id,
                        ard_arrears_charge_type=wrt_ard_arrears_charge_type,
                        ard_return_description=wrt_ard_return_description,
                        ard_effective_date=wrt_ard_effective_date,
                        ard_due_date=wrt_ard_due_date,
                        ard_reference=wrt_ard_reference,
                        ard_referencestrip=wrt_ard_referencestrip,
                        ard_arrears_count=wrt_ard_arrears_count,
                        ard_arrears_value_netofvat=wrt_ard_arrears_value_netofvat,
                        ard_arrears_value_grossofvat=wrt_ard_arrears_value_grossofvat,
                        ard_arrears_last_date=wrt_ard_arrears_last_date,
                        ard_collected_count=wrt_ard_collected_count,
                        ard_collected_value_netofvat=wrt_ard_collected_value_netofvat,
                        ard_collected_value_grossofvat=wrt_ard_collected_value_grossofvat,
                        ard_collected_last_date=wrt_ard_collected_last_date,
                        ard_writtenoff_count=wrt_ard_writtenoff_count,
                        ard_writtenoff_value_netofvat=wrt_ard_writtenoff_value_netofvat,
                        ard_writtenoff_value_grossofvat=wrt_ard_writtenoff_value_grossofvat,
                        ard_writtenoff_last_date=wrt_ard_writtenoff_last_date,
                        ard_balance_value_netofvat=wrt_ard_balance_value_netofvat,
                        ard_balance_value_grossofvat=wrt_ard_balance_value_grossofvat,
                        ard_balance_last_date=wrt_ard_balance_last_date,
                        ard_agent_id=wrt_ard_agent_id,
                        ard_status=wrt_ard_status,
                        ard_status_date=wrt_ard_status_date,
                        ard_file_name=wrt_ard_file_name
                    )

    return wip_next_id

def process_summary_non_dd_level(wip_agreement_id, wip_arrears_id, wip_due_date):

    # Get aggregate values for this arrears id
    try:
        dict_arrears_totals = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                         ard_arrears_id=wip_arrears_id) \
            .aggregate(Sum('ard_arrears_value_netofvat'),
                       Sum('ard_arrears_value_grossofvat'),
                       Sum('ard_collected_value_netofvat'),
                       Sum('ard_collected_value_grossofvat'),
                       Sum('ard_writtenoff_value_netofvat'),
                       Sum('ard_writtenoff_value_grossofvat'),
                       Sum('ard_balance_value_netofvat'),
                       Sum('ard_balance_value_grossofvat'))
        wip_arrears_value_netofvat = dict_arrears_totals["ard_arrears_value_netofvat__sum"]
        wip_arrears_value_grossofvat = dict_arrears_totals["ard_arrears_value_grossofvat__sum"]
        wip_collected_value_netofvat = dict_arrears_totals["ard_collected_value_netofvat__sum"]
        wip_collected_value_grossofvat = dict_arrears_totals["ard_collected_value_grossofvat__sum"]
        wip_writtenoff_value_netofvat = dict_arrears_totals["ard_writtenoff_value_netofvat__sum"]
        wip_writtenoff_value_grossofvat = dict_arrears_totals["ard_writtenoff_value_grossofvat__sum"]
        wip_balance_value_netofvat = dict_arrears_totals["ard_balance_value_netofvat__sum"]
        wip_balance_value_grossofvat = dict_arrears_totals["ard_balance_value_grossofvat__sum"]

    except ObjectDoesNotExist:

        wip_arrears_value_netofvat = 0
        wip_arrears_value_grossofvat = 0
        wip_collected_value_netofvat = 0
        wip_collected_value_grossofvat = 0
        wip_writtenoff_value_netofvat = 0
        wip_writtenoff_value_grossofvat = 0
        wip_balance_value_netofvat = 0
        wip_balance_value_grossofvat = 0

    if wip_arrears_value_netofvat != 0:

        # Get baseline values for this arrears id
        try:
            baseline = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id,
                                                                             ard_arrears_id=wip_arrears_id) \
                                    .first()
        except ObjectDoesNotExist:
            baseline = None

        if baseline:

            # get agreement phase - PRIMARY (SP1) or SECONDARY (SP2)
            try:
                agreement_phases = go_account_transaction_summary.objects. \
                    filter(agreementnumber=wip_agreement_id,
                           transactiondate=wip_due_date,
                           transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3')).first()
                wip_agreement_phase = agreement_phases.transactionsourceid
            except ObjectDoesNotExist:
                wip_agreement_phase = None

            wrt_ara_agreement_id = baseline.ard_agreement_id
            wrt_ara_customernumber = baseline.ard_customernumber
            wrt_ara_customercompanyname = baseline.ard_customercompanyname
            wrt_ara_return_description = baseline.ard_return_description
            wrt_ara_arrears_id = baseline.ard_arrears_id
            wrt_ara_effective_date = baseline.ard_effective_date
            wrt_ara_due_date = baseline.ard_due_date
            wrt_ara_transactionsourceid = wip_agreement_phase
            wrt_ara_reference = baseline.ard_reference
            wrt_ara_referencestrip = baseline.ard_referencestrip
            wrt_ara_arrears_last_date = baseline.ard_arrears_last_date
            wrt_ara_collected_count = baseline.ard_collected_count
            wrt_ara_collected_last_date = baseline.ard_collected_last_date
            wrt_ara_writtenoff_count = baseline.ard_writtenoff_count
            wrt_ara_writtenoff_last_date = baseline.ard_writtenoff_last_date
            wrt_ara_balance_last_date = baseline.ard_balance_last_date
            wrt_ara_agent_id = baseline.ard_agent_id
            wrt_ara_status = baseline.ard_status
            wrt_ara_status_date = baseline.ard_status_date
            wrt_ara_file_name = baseline.ard_file_name

            arrears_summary_arrear_level.objects.create(
                ara_agreement_id=wrt_ara_agreement_id,
                ara_customernumber=wrt_ara_customernumber,
                ara_customercompanyname=wrt_ara_customercompanyname,
                ara_arrears_id=wrt_ara_arrears_id,
                ara_return_description=wrt_ara_return_description,
                ara_effective_date=wrt_ara_effective_date,
                ara_due_date=wrt_ara_due_date,
                ara_transactionsourceid=wrt_ara_transactionsourceid,
                ara_reference=wrt_ara_reference,
                ara_referencestrip=wrt_ara_referencestrip,
                ara_arrears_value_netofvat=wip_arrears_value_netofvat,
                ara_arrears_value_grossofvat=wip_arrears_value_grossofvat,
                ara_arrears_last_date=wrt_ara_arrears_last_date,
                ara_collected_count=wrt_ara_collected_count,
                ara_collected_value_netofvat=wip_collected_value_netofvat,
                ara_collected_value_grossofvat=wip_collected_value_grossofvat,
                ara_collected_last_date=wrt_ara_collected_last_date,
                ara_writtenoff_count=wrt_ara_writtenoff_count,
                ara_writtenoff_value_netofvat=wip_writtenoff_value_netofvat,
                ara_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat,
                ara_writtenoff_last_date=wrt_ara_writtenoff_last_date,
                ara_balance_value_netofvat=wip_balance_value_netofvat,
                ara_balance_value_grossofvat=wip_balance_value_grossofvat,
                ara_balance_last_date=wrt_ara_balance_last_date,
                ara_agent_id=wrt_ara_agent_id,
                ara_status=wrt_ara_status,
                ara_status_date=wrt_ara_status_date,
                ara_file_name=wrt_ara_file_name
            )

def process_agreement_non_dd_level(wip_agreement_id, wip_arrears_id):

    # Get values for this arrears id
    try:
        arrears_level_totals = arrears_summary_arrear_level.objects.get(ara_agreement_id=wip_agreement_id,
                                                                         ara_arrears_id=wip_arrears_id)

    except ObjectDoesNotExist:

        arrears_level_totals = None

    if arrears_level_totals:

        # get base info for arrears - used when creating new agreement level object
        wip_agreement_id = arrears_level_totals.ara_agreement_id
        wip_customernumber = arrears_level_totals.ara_customernumber
        wip_customercompanyname = arrears_level_totals.ara_customercompanyname
        wip_arrears_last_date = arrears_level_totals.ara_arrears_last_date
        wip_status_date = arrears_level_totals.ara_status_date
        # wip_agent_id_id = arrears_level_totals.ara_agent_id
        wip_status_id = arrears_level_totals.ara_status

        # get totals from arrears details
        dict_arrears_totals = arrears_detail_arrear_level.objects.filter(ard_agreement_id=wip_agreement_id) \
            .aggregate(Sum('ard_arrears_value_netofvat'),
                       Sum('ard_arrears_value_grossofvat'),
                       Sum('ard_collected_value_netofvat'),
                       Sum('ard_collected_value_grossofvat'),
                       Sum('ard_writtenoff_value_netofvat'),
                       Sum('ard_writtenoff_value_grossofvat'),
                       Sum('ard_balance_value_netofvat'),
                       Sum('ard_balance_value_grossofvat'),
                       Sum('ard_arrears_count'),
                       Sum('ard_collected_count'),
                       Sum('ard_writtenoff_count')
                       )

        wip_arrears_value_netofvat = dict_arrears_totals["ard_arrears_value_netofvat__sum"]
        wip_arrears_value_grossofvat = dict_arrears_totals["ard_arrears_value_grossofvat__sum"]
        wip_collected_value_netofvat = dict_arrears_totals["ard_collected_value_netofvat__sum"]
        wip_collected_value_grossofvat = dict_arrears_totals["ard_collected_value_grossofvat__sum"]
        wip_writtenoff_value_netofvat = dict_arrears_totals["ard_writtenoff_value_netofvat__sum"]
        wip_writtenoff_value_grossofvat = dict_arrears_totals["ard_writtenoff_value_grossofvat__sum"]
        wip_balance_value_netofvat = dict_arrears_totals["ard_balance_value_netofvat__sum"]
        wip_balance_value_grossofvat = dict_arrears_totals["ard_balance_value_grossofvat__sum"]
        wip_arrears_count = dict_arrears_totals["ard_arrears_count__sum"]
        wip_collected_count = dict_arrears_totals["ard_collected_count__sum"]
        wip_writtenoff_count = dict_arrears_totals["ard_writtenoff_count__sum"]

        try:
            existing_agreement_level_arrear = arrears_summary_agreement_level.objects\
                                                            .get(arr_agreement_id=wip_agreement_id)
        except ObjectDoesNotExist:
            existing_agreement_level_arrear = None

        # Get Unallocated receipts
        unallocated_by_agreement = receipt_allocations_by_agreement.objects.filter(
            rag_agreement_id=wip_agreement_id).first()
        if unallocated_by_agreement:
            xip_unallocated_value_netofvat = unallocated_by_agreement.unallocated_value_netofvat
            xip_unallocated_value_grossofvat = unallocated_by_agreement.unallocated_value_grossofvat
            xip_unallocated_last_date = unallocated_by_agreement.unallocated_last_date
        else:
            xip_unallocated_value_netofvat = 0
            xip_unallocated_value_grossofvat = 0
            xip_unallocated_last_date = wip_status_date

        if existing_agreement_level_arrear:

            existing_agreement_level_arrear.arr_arrears_count=wip_arrears_count
            existing_agreement_level_arrear.arr_arrears_value_netofvat=wip_arrears_value_netofvat
            existing_agreement_level_arrear.arr_arrears_value_grossofvat=wip_arrears_value_grossofvat
            existing_agreement_level_arrear.arr_arrears_last_date=wip_arrears_last_date
            existing_agreement_level_arrear.arr_collected_count=wip_collected_count
            existing_agreement_level_arrear.arr_collected_value_netofvat=wip_collected_value_netofvat
            existing_agreement_level_arrear.arr_collected_value_grossofvat=wip_collected_value_grossofvat
            existing_agreement_level_arrear.arr_writtenoff_count=wip_writtenoff_count
            existing_agreement_level_arrear.arr_writtenoff_value_netofvat=wip_writtenoff_value_netofvat
            existing_agreement_level_arrear.arr_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat
            existing_agreement_level_arrear.arr_balance_value_netofvat=wip_balance_value_netofvat
            existing_agreement_level_arrear.arr_balance_value_grossofvat=wip_balance_value_grossofvat
            existing_agreement_level_arrear.arr_balance_last_date=wip_arrears_last_date
            existing_agreement_level_arrear.arr_status_date=wip_status_date
            existing_agreement_level_arrear.arr_unallocated_value_netofvat = xip_unallocated_value_netofvat
            existing_agreement_level_arrear.arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat
            existing_agreement_level_arrear.arr_unallocated_last_date = xip_unallocated_last_date
            existing_agreement_level_arrear.arr_status_id=1
            existing_agreement_level_arrear.save()

        else:

            arrears_summary_agreement_level.objects.create(
                arr_agreement_id=wip_agreement_id,
                arr_customernumber=wip_customernumber,
                arr_customercompanyname=wip_customercompanyname,
                arr_arrears_count=wip_arrears_count,
                arr_arrears_value_netofvat=wip_arrears_value_netofvat,
                arr_arrears_value_grossofvat=wip_arrears_value_grossofvat,
                arr_arrears_last_date=wip_arrears_last_date,
                arr_collected_count=wip_collected_count,
                arr_collected_value_netofvat=wip_collected_value_netofvat,
                arr_collected_value_grossofvat=wip_collected_value_grossofvat,
                arr_collected_last_date='2000-01-01',
                arr_writtenoff_count=wip_writtenoff_count,
                arr_writtenoff_value_netofvat=wip_writtenoff_value_netofvat,
                arr_writtenoff_value_grossofvat=wip_writtenoff_value_grossofvat,
                arr_writtenoff_last_date='2000-01-01',
                arr_balance_value_netofvat=wip_balance_value_netofvat,
                arr_balance_value_grossofvat=wip_balance_value_grossofvat,
                arr_balance_last_date=wip_arrears_last_date,
                arr_status_date=wip_status_date,
                arr_unallocated_value_netofvat = xip_unallocated_value_netofvat,
                arr_unallocated_value_grossofvat = xip_unallocated_value_grossofvat,
                arr_unallocated_last_date = xip_unallocated_last_date,
                # arr_agent_id_id=wip_agent_id_id,
                arr_status_id=1
            )


def process_agent_allocations():

    # add new primary collection agents to allocations control
    collection_agents_extract = User.objects.filter(groups__name='NCF_Collections_PrimaryAgents')
    if collection_agents_extract:
        for collection_agent in collection_agents_extract:
            agent_allocation = agent_allocations_control.objects.filter(aac_agent_id=collection_agent,
                                                                        aac_agent_phase='primary').first()
            if not agent_allocation:
                agent_allocations_control.objects.create(
                    aac_agent_id=collection_agent,
                    aac_agent_phase='primary',
                    aac_status=''
                )

    # remove old primary collection agents from allocations control
    agent_allocation_extract = agent_allocations_control.objects.filter(aac_agent_phase='primary')
    if agent_allocation_extract:
        for agent_allocation in agent_allocation_extract:
            collection_agent = User.objects.filter(groups__name='NCF_Collections_PrimaryAgents', id=agent_allocation.aac_agent_id_id).first()
            if not collection_agent:
                agent_allocation.delete()

    # add new secondary collection agents to allocations control
    collection_agents_extract = User.objects.filter(groups__name='NCF_Collections_SecondaryAgents')
    if collection_agents_extract:
        for collection_agent in collection_agents_extract:
            agent_allocation = agent_allocations_control.objects.filter(aac_agent_id=collection_agent,
                                                                        aac_agent_phase='secondary').first()
            if not agent_allocation:
                agent_allocations_control.objects.create(
                    aac_agent_id=collection_agent,
                    aac_agent_phase='secondary',
                    aac_status=''
                )

    # remove old secondary collection agents from allocations control
    agent_allocation_extract = agent_allocations_control.objects.filter(aac_agent_phase='secondary')
    if agent_allocation_extract:
        for agent_allocation in agent_allocation_extract:
            collection_agent = User.objects.filter(groups__name='NCF_Collections_SecondaryAgents',
                                                   id=agent_allocation.aac_agent_id_id).first()
            if not collection_agent:
                agent_allocation.delete()

    # Allocate Agents to Primary Arrears
    arrears_summary_arrears_extract = arrears_summary_arrear_level.objects.filter(ara_agent_id__isnull=True,
                                                                                  ara_transactionsourceid__in=[
                                                                                      'SP1', 'GO1'])

    if arrears_summary_arrears_extract:

        for arrears_summary_arrears in arrears_summary_arrears_extract:

            # get next agent
            new_agent_extract = agent_allocations_control.objects.filter(aac_status='', aac_agent_phase='primary') \
                .first()
            if not new_agent_extract:
                new_agent_clear = agent_allocations_control.objects.filter(aac_agent_phase='primary')
                new_agent_clear.update(aac_status='')
                new_agent_extract = agent_allocations_control.objects.filter(aac_status='',
                                                                             aac_agent_phase='primary') \
                    .first()

            new_agent = new_agent_extract.aac_agent_id
            new_agent_extract.aac_status = 'X'
            new_agent_extract.save()

            if new_agent:
                arrears_summary_arrears.ara_agent_id = new_agent
                arrears_summary_arrears.save()

    # Allocate Agents to Secondary Arrears
    arrears_summary_arrears_extract = arrears_summary_arrear_level.objects.filter(ara_agent_id__isnull=True,
                                                                                  ara_transactionsourceid__in=[
                                                                                      'SP2', 'SP3', 'GO3'])
    print('Secondary')
    if arrears_summary_arrears_extract:

        for arrears_summary_arrears in arrears_summary_arrears_extract:
            print(arrears_summary_arrears.ara_agreement_id)
            # get next agent
            new_agent_extract = agent_allocations_control.objects.filter(aac_status='', aac_agent_phase='secondary') \
                .first()
            if not new_agent_extract:
                new_agent_clear = agent_allocations_control.objects.filter(aac_agent_phase='secondary')
                new_agent_clear.update(aac_status='')
                new_agent_extract = agent_allocations_control.objects.filter(aac_status='',
                                                                             aac_agent_phase='secondary') \
                    .first()

            new_agent = new_agent_extract.aac_agent_id
            new_agent_extract.aac_status = 'X'
            new_agent_extract.save()

            if new_agent:
                arrears_summary_arrears.ara_agent_id = new_agent
                arrears_summary_arrears.save()


