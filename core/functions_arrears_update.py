import datetime
from decimal import Decimal

from .models import ncf_collection_agents, \
                    ncf_dd_call_arrears, \
                    ncf_dd_schedule, \
                    ncf_arrears_summary_uuid_xref, \
                    ncf_arrears_summary, \
                    ncf_arrears_phase, \
                    ncf_arrears_status, \
                    ncf_arrears_detail_txn, \
                    ncf_arrears_detail

from anchorimport.models import AnchorimportAccountTransactionDetail, \
                                AnchorimportAgreement_QueryDetail


def app_allocate_agents():

    # Build Primary Agent Collection
    arr_primary_agents = []
    primary_collection_agents = ncf_collection_agents.objects.filter(bd_agent_primary_active=True)
    for collection_agent in primary_collection_agents:
        arr_primary_agents.append(collection_agent.id)

    # Build Secondary Agent Collection
    arr_secondary_agents = []
    secondary_collection_agents = ncf_collection_agents.objects.filter(bd_agent_secondary_active=True)
    for collection_agent in secondary_collection_agents:
        arr_secondary_agents.append(collection_agent.id)

    # Allocate Primary Arrears
    primary_arrears_rows = ncf_dd_call_arrears.objects.filter(ar_agreement_phase='Primary',ar_agent_id_id__isnull=True).order_by('ar_agreement_id')
    agent_counter = -1
    agent_counter_max = len(arr_primary_agents)-1
    for arrear_row in primary_arrears_rows:
        agent_name = ''
        if (arrear_row.ar_exclude_reason == '') or (arrear_row.ar_exclude_reason == 'Advance Paid in Part'):
            agent_counter = agent_counter + 1

            if agent_counter > agent_counter_max:
                agent_counter = 0

            agent_id = arr_primary_agents[agent_counter]
            agent_name = primary_collection_agents.get(id=agent_id)

            arrear_row.ar_agent_id_id = agent_id
            arrear_row.ar_agent_name = agent_name.bd_collection_agent.username
            arrear_row.save()

        else:

            arrear_row.ar_agent_id_id = None
            arrear_row.ar_agent_name = None
            arrear_row.save()

    # Allocate Secondary Arrears
    secondary_arrears_rows = ncf_dd_call_arrears.objects.filter(ar_agreement_phase='Secondary', ar_agent_id_id__isnull=True).order_by('ar_agreement_id')
    agent_counter = -1
    agent_counter_max = len(arr_secondary_agents) - 1
    for arrear_row in secondary_arrears_rows:
        agent_name = ''
        if (arrear_row.ar_exclude_reason == '') or (arrear_row.ar_exclude_reason == 'Advance Paid in Part'):
            agent_counter = agent_counter + 1

            if agent_counter > agent_counter_max:
                agent_counter = 0

            agent_id = arr_secondary_agents[agent_counter]
            agent_name = secondary_collection_agents.get(id=agent_id)

            arrear_row.ar_agent_id_id = agent_id
            arrear_row.ar_agent_name = agent_name.bd_collection_agent.username
            arrear_row.save()

        else:

            arrear_row.ar_agent_id_id = None
            arrear_row.ar_agent_name = None
            arrear_row.save()


def app_process_bounce_arrears():

    control = ncf_dd_schedule.objects.filter(dd_status_id=999).first()

    # Process current DD call
    if control:

        process_dd_calendar_due_date = control.dd_calendar_due_date

        # Get all arrears for current DD call
        dd_arrears = ncf_dd_call_arrears.objects.filter(ar_calendar_due_date=process_dd_calendar_due_date,
                                                        ar_agent_id_id__isnull=False)

        for dd_arrear in dd_arrears:

            # Check to see if current arrears already processed.
            if not ncf_arrears_summary_uuid_xref.objects.filter(col_agreement_id=dd_arrear.ar_agreement_id,
                                                                     col_uuid=dd_arrear.ar_uuid).\
                                                                        exists():

                # Get Status Variables
                phase = ncf_arrears_phase.objects.get(col_phase_code="CURR")
                status = ncf_arrears_status.objects.get(col_status_code="OPEN")

                # Get Agreement detail
                sentinel_row = AnchorimportAgreement_QueryDetail.objects.get(
                    agreementnumber=dd_arrear.ar_agreement_id)

                # Check to see if an open arrears summary exists
                if not ncf_arrears_summary.objects.filter(col_agreement_id=dd_arrear.ar_agreement_id,
                                                          col_arrears_sum_status=status.id).\
                                                                        exists():

                    ncf_arrears_summary.objects.create(
                    col_agreement_id = dd_arrear.ar_agreement_id,
                    col_agent_id = dd_arrear.ar_agent_id,
                    col_arrears_gross_rental = dd_arrear.ar_arrears_rental,
                    col_arrears_gross_fee = dd_arrear.ar_arrears_fee,
                    col_arrears_gross_total = dd_arrear.ar_arrears_total,
                    col_collected_gross_rental=0,
                    col_collected_gross_fee=0,
                    col_collected_gross_total=0,
                    col_outstanding_gross_rental=dd_arrear.ar_arrears_rental,
                    col_outstanding_gross_fee=dd_arrear.ar_arrears_fee,
                    col_outstanding_gross_total=dd_arrear.ar_arrears_total,
                    col_arrears_startdate = dd_arrear.ar_calendar_due_date,
                    col_arrears_latestdate = dd_arrear.ar_calendar_due_date,
                    col_arrears_sum_status = status,
                    col_arrears_sum_phase = phase,
                    col_arrears_sum_changedate = datetime.datetime.now())

                # Check to see if an open arrears detail exists
                if not ncf_arrears_detail.objects.filter(col_agreement_id=dd_arrear.ar_agreement_id,
                                                         col_uuid=dd_arrear.ar_uuid). \
                                                            exists():
                    ncf_arrears_detail.objects.create(
                        col_agreement_id = dd_arrear.ar_agreement_id,
                        col_arrears_duedate = dd_arrear.ar_calendar_due_date,
                        col_agent_id = dd_arrear.ar_agent_id,
                        col_arrears_gross_rental = dd_arrear.ar_arrears_rental,
                        col_arrears_gross_fee = dd_arrear.ar_arrears_fee,
                        col_arrears_gross_total = dd_arrear.ar_arrears_total,
                        col_collected_gross_rental = 0,
                        col_collected_gross_fee = 0,
                        col_collected_gross_total = 0,
                        col_outstanding_gross_rental = dd_arrear.ar_arrears_rental,
                        col_outstanding_gross_fee = dd_arrear.ar_arrears_fee,
                        col_outstanding_gross_total = dd_arrear.ar_arrears_total,
                        col_arrears_startdate = dd_arrear.ar_calendar_due_date,
                        col_arrears_latestdate = dd_arrear.ar_calendar_due_date,
                        col_arrears_detl_status = status,
                        col_arrears_detl_phase = phase,
                        col_arrears_detl_changedate = datetime.datetime.now(),
                        col_uuid = dd_arrear.ar_uuid)

                # Check for and write new detail transactions
                profile_txns = AnchorimportAccountTransactionDetail.objects\
                                                    .filter(agreementnumber=dd_arrear.ar_agreement_id,
                                                            transactiondate__date=process_dd_calendar_due_date,
                                                            transactionsourceid__in=['SP1', 'SP2', 'SP3'])\
                                                    .order_by('-transtypedesc')

                for profile_txn in profile_txns:

                    if not ncf_arrears_detail_txn.objects.filter(col_agreement_id = dd_arrear.ar_agreement_id,
                                                                          col_arrears_duedate=dd_arrear.ar_calendar_due_date,
                                                                          col_arrears_type_desc=profile_txn.transtypedesc,
                                                                          col_uuid=dd_arrear.ar_uuid).exists():

                        val_scheduled_value = profile_txn.transnetpayment
                        if sentinel_row.agreementdefname != 'Hire Purchase':
                            val_scheduled_value = val_scheduled_value * Decimal('1.2')

                        ncf_arrears_detail_txn.objects.create(
                            col_agreement_id = dd_arrear.ar_agreement_id,
                            col_arrears_duedate = dd_arrear.ar_calendar_due_date,
                            col_agent_id = dd_arrear.ar_agent_id,
                            col_arrears_type_id = profile_txn.transtypeid,
                            col_arrears_type_desc = profile_txn.transtypedesc,
                            col_arrears_gross_rental = val_scheduled_value,
                            col_arrears_gross_fee = 0,
                            col_arrears_gross_total = 0,
                            col_collected_gross_rental = 0,
                            col_collected_gross_fee = 0,
                            col_collected_gross_total = 0,
                            col_outstanding_gross_rental = 0,
                            col_outstanding_gross_fee = 0,
                            col_outstanding_gross_total = 0,
                            col_arrears_startdate = dd_arrear.ar_calendar_due_date,
                            col_arrears_latestdate = dd_arrear.ar_calendar_due_date,
                            col_arrears_txn_status = status,
                            col_arrears_txn_phase = phase,
                            col_arrears_txn_changedate = datetime.datetime.now(),
                            col_uuid = dd_arrear.ar_uuid)
