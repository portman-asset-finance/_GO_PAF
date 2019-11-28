from django.core.exceptions import ObjectDoesNotExist
from dateutil.relativedelta import *
from decimal import Decimal
import uuid, pytz, datetime

from .functions_arrears_update import app_allocate_agents, app_process_bounce_arrears

from .models import ncf_dd_call_arrears, \
    ncf_dd_call_rejections, \
    ncf_datacash_drawdowns, \
    ncf_settled_agreements, \
    ncf_agreement_titles, \
    ncf_global_terminations, \
    ncf_global_terminations, \
    ncf_advanced_payments, \
    ncf_arrears_collected, \
    ncf_udd_advices, \
    ncf_dd_schedule, \
    go_extensions

from anchorimport.models import AnchorimportAgreement_QueryDetail ,\
                                AnchorimportAccountTransactionSummary


def app_process_bounce_days():

    control = ncf_dd_schedule.objects.filter(dd_status_id=999).first()

    # for control in all_controls:

    process_dd_calendar_due_date = control.dd_calendar_due_date
    process_dd_process_date01 = control.dd_process_date01
    process_dd_bounce_date02 = control.dd_bounce_date02
    process_dd_bounce_date01 = control.dd_bounce_date01
    first_bounceday_processed = control.dd_firstbounce_processed

    val_processed = False

    # Process DataCash Errors - Once Only.
    if not first_bounceday_processed:
        datacash_errors = ncf_datacash_drawdowns.objects.filter(dd_due_date=process_dd_calendar_due_date)
        for datacash_error in datacash_errors:

            val_processed = True

            if datacash_error.dd_response != 'Ok':

                val_exclude_reason = ''
                if not ncf_settled_agreements.objects.filter(agreement_id=datacash_error.agreement_id):
                    if not ncf_global_terminations.objects.filter(agreement_id=datacash_error.agreement_id):
                        if not ncf_agreement_titles.objects.filter(agreement_id=datacash_error.agreement_id):
                            pass
                        else:
                            val_exclude_reason = 'Gone To Title'
                    else:
                        val_exclude_reason = 'Globally Terminated'
                else:
                    val_exclude_reason = 'Settled'

                test_duplicate = datacash_error.dd_reference

                if not ncf_datacash_drawdowns.objects.filter(dd_reference=test_duplicate, dd_response='Ok',
                                                             dd_request_date=process_dd_calendar_due_date):

                    val_account_name = 'NOT FOUND'
                    val_salesperson = 'TBA'
                    val_term = 'TBA'
                    val_agreement_phase = 'TBA'

                    # Retrieve Advance Payment.
                    val_advance_value = 0
                    advance_rows = ncf_advanced_payments.objects.filter(agreement_id=datacash_error.agreement_id,
                                                                        advance_date=process_dd_calendar_due_date)
                    for advance_row in advance_rows:
                        val_advance_value = val_advance_value + advance_row.advance_value

                    # Retrieve and collccted payments.
                    collected_rows = ncf_arrears_collected.objects.filter(ac_agreement_id=datacash_error.agreement_id,
                                                                          ac_collected_date=process_dd_calendar_due_date)

                    for collected_row in collected_rows:
                        val_advance_value = val_advance_value + collected_row.ac_arrears_collected

                    # Retrieve Sentinel Details
                    val_scheduled_value = 0
                    try:

                        sentinel_row = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=datacash_error.agreement_id)
                        val_agreement_enddate_query = AnchorimportAccountTransactionSummary.objects.\
                            filter(agreementnumber=datacash_error.agreement_id, transactionsourceid='SP1').\
                            latest('transactiondate')
                        val_agreement_value_query = AnchorimportAccountTransactionSummary.objects. \
                            filter(agreementnumber=datacash_error.agreement_id, transactiondate__date=process_dd_calendar_due_date).\
                                   exclude(transactionsourceid='SP9' ).first()
                        val_account_name = sentinel_row.customercompany
                        val_salesperson = sentinel_row.agreementauthority
                        val_term = "( " + str(sentinel_row.agreementnumpayments) + " months )"
                        val_agreement_enddate = val_agreement_enddate_query.transactiondate.date()
                        val_scheduled_value = val_agreement_value_query.transnetpayment
                        if sentinel_row.agreementdefname != 'Hire Purchase':
                            val_scheduled_value = val_scheduled_value * Decimal('1.2')
                        val_draw_error = ''
                        val_risk_message = ''
                        val_bamf_message = ''

                        if process_dd_calendar_due_date > val_agreement_enddate:
                            val_agreement_phase = 'Secondary'
                        else:
                            val_agreement_phase = 'Primary'

                        test_draw_error = datacash_error.dd_amount - val_scheduled_value
                        if test_draw_error < -1:
                            val_draw_error = ' - DD VALUE DEFICIT'
                        if test_draw_error > 1:
                            val_draw_error = ' - DD VALUE EXCESS'

                    except ObjectDoesNotExist:
                        pass
                    else:
                        pass

                    # Write Arrears Record
                    if val_advance_value > 0:
                        val_arrear_value = datacash_error.dd_amount - val_advance_value
                        if val_arrear_value <= 0:
                            val_arrear_value = 0
                            val_arrears_fee = 0
                            val_arrears_total = 0
                            val_exclude_reason = 'Advance/Collected Paid in Full'
                        else:
                            val_exclude_reason = 'Advance/Collected Paid in Part'
                            val_arrears_fee = 360
                            val_arrears_total = val_arrear_value + val_arrears_fee
                    else:
                        val_arrear_value = datacash_error.dd_amount
                        val_arrears_fee = 360
                        val_arrears_total = val_arrear_value + val_arrears_fee

                    if val_exclude_reason in ('Gone To Title', 'Globally Terminated', 'Settled'):
                        val_arrear_value = 0
                        val_arrears_fee = 0
                        val_arrears_total = 0

                    if not ncf_dd_call_rejections.objects.filter(ar_agreement_id=datacash_error.agreement_id,
                                                                 ar_calendar_due_date=process_dd_calendar_due_date).\
                                                                    exists():
                        val_uuid = uuid.uuid4()

                        ncf_dd_call_arrears.objects.create(
                            ar_agreement_id=datacash_error.agreement_id,
                            ar_calendar_due_date=process_dd_calendar_due_date,
                            ar_account_name=val_account_name,
                            ar_salesperson=val_salesperson,
                            ar_arrears_rental=val_arrear_value,
                            ar_arrears_fee=val_arrears_fee,
                            ar_arrears_total=val_arrears_total,
                            ar_term=val_term,
                            ar_date=process_dd_calendar_due_date,
                            ar_days=999999,
                            ar_notes='DC ERROR : ' + datacash_error.dd_response + val_draw_error
                                     + val_bamf_message + val_risk_message,
                            ar_agreement_phase=val_agreement_phase,
                            ar_exclude_reason=val_exclude_reason,
                            ar_dd_original_value=datacash_error.dd_amount,
                            ar_schedule_value = val_scheduled_value,
                            ar_uuid=val_uuid
                        )

                        # Write Cancelled DD record
                        ncf_dd_call_rejections.objects.create(
                            ar_agreement_id=datacash_error.agreement_id,
                            ar_calendar_due_date=process_dd_calendar_due_date,
                            ar_account_name=val_account_name,
                            ar_salesperson=val_salesperson,
                            ar_date_cancelled=process_dd_calendar_due_date,
                            ar_term=val_term,
                            ar_reason_cancelled='DC ERROR',
                            ar_days_cancelled=999999,
                            ar_next_dd_due=process_dd_calendar_due_date + relativedelta(months=+1),
                            ar_days_until_dd=999999,
                            ar_notes=datacash_error.dd_response + val_draw_error
                                                                + val_bamf_message + val_risk_message,
                            ar_agreement_phase=val_agreement_phase,
                            ar_exclude_reason=val_exclude_reason,
                            ar_dd_original_value=datacash_error.dd_amount,
                            ar_schedule_value=val_scheduled_value,
                            ar_uuid=val_uuid
                        )

    # Process BACS UDD Bounces
    bacs_bounces = ncf_udd_advices.objects.filter(dd_original_process_date__gte=process_dd_process_date01,
                                                  dd_original_process_date__lte=process_dd_bounce_date02,
                                                  ).order_by('file_name')
    save_file_name = ''

    for bacs_bounce in bacs_bounces:

        if save_file_name != bacs_bounce.file_name:
            process_bacs_bounces = ncf_dd_call_arrears.objects.filter(ar_file_name=bacs_bounce.file_name).first()
            save_file_name = bacs_bounce.file_name


        if not process_bacs_bounces:

            val_processed = True

            val_exclude_reason = ''
            if not ncf_settled_agreements.objects.filter(agreement_id=bacs_bounce.agreement_id):
                if not ncf_global_terminations.objects.filter(agreement_id=bacs_bounce.agreement_id):
                    if not ncf_agreement_titles.objects.filter(agreement_id=bacs_bounce.agreement_id):
                        pass
                    else:
                        val_exclude_reason = 'Gone To Title'
                else:
                    val_exclude_reason = 'Globally Terminated'
            else:
                val_exclude_reason = 'Settled'

            val_account_name = 'NOT FOUND'
            val_salesperson = 'TBA'
            val_term = 'TBA'
            val_agreement_phase = 'TBA'

            # Retrieve Advance Payment
            val_advance_value = 0
            advance_rows = ncf_advanced_payments.objects.filter(agreement_id=bacs_bounce.agreement_id,
                                                                advance_date=process_dd_calendar_due_date)
            for advance_row in advance_rows:
                val_advance_value = val_advance_value + advance_row.advance_value

            # Retrieve and collccted payments.
            collected_rows = ncf_arrears_collected.objects.filter(ac_agreement_id=bacs_bounce.agreement_id,
                                                                  ac_collected_date=process_dd_calendar_due_date)

            for collected_row in collected_rows:
                val_advance_value = val_advance_value + collected_row.ac_arrears_collected

            # Retrieve Props & Payouts
            val_scheduled_value = 0
            try:
                sentinel_row = AnchorimportAgreement_QueryDetail.objects.get(
                    agreementnumber=bacs_bounce.agreement_id)
                val_agreement_enddate_query = AnchorimportAccountTransactionSummary.objects. \
                    filter(agreementnumber=bacs_bounce.agreement_id, transactionsourceid='SP1'). \
                    latest('transactiondate')
                val_agreement_value_query = AnchorimportAccountTransactionSummary.objects. \
                    filter(agreementnumber=bacs_bounce.agreement_id,
                           transactiondate=process_dd_calendar_due_date).\
                                   exclude(transactionsourceid='SP9' ).first()

                val_account_name = sentinel_row.customercompany
                val_salesperson = sentinel_row.agreementauthority
                val_term = "( " + str(sentinel_row.agreementnumpayments) + " months )"
                val_agreement_enddate = val_agreement_enddate_query.transactiondate.date()
                val_scheduled_value = val_agreement_value_query.transnetpayment
                if sentinel_row.agreementdefname != 'Hire Purchase':
                    val_scheduled_value = val_scheduled_value * Decimal('1.2')
                val_draw_error = ''
                val_risk_message = ''
                val_bamf_message = ''

                if process_dd_calendar_due_date > val_agreement_enddate:
                    val_agreement_phase = 'Secondary'
                else:
                    val_agreement_phase = 'Primary'

                test_draw_error = bacs_bounce.dd_value - val_scheduled_value
                if test_draw_error < -1:
                    val_draw_error = ' - DD VALUE DEFICIT'
                if test_draw_error > 1:
                    val_draw_error = ' - DD VALUE EXCESS'

            except ObjectDoesNotExist:
                pass
            else:
                pass

                # Write Arrears Record
                if val_advance_value > 0:
                    val_arrear_value = bacs_bounce.dd_value - val_advance_value
                    if val_arrear_value <= 0:
                        val_arrear_value = 0
                        val_arrears_fee = 0
                        val_arrears_total = 0
                        val_exclude_reason = 'Advance Paid in Full'
                    else:
                        val_exclude_reason = 'Advance Paid in Part'
                        val_arrears_fee = 360
                        val_arrears_total = val_arrear_value + val_arrears_fee
                else:
                    val_arrear_value = bacs_bounce.dd_value
                    val_arrears_fee = 360
                    val_arrears_total = val_arrear_value + val_arrears_fee

            if bacs_bounce.dd_return_description == 'REFER TO PAYER':
                val_message_text = 'RTP'
            elif bacs_bounce.dd_return_description == 'INSTRUCTION CANCELLED':
                val_message_text = 'IC'
            else:
                val_message_text = bacs_bounce.dd_return_description

            if val_exclude_reason in ('Gone To Title', 'Globally Terminated', 'Settled'):
                val_arrear_value = 0
                val_arrears_fee = 0
                val_arrears_total = 0

            val_uuid = uuid.uuid4()

            ncf_dd_call_arrears.objects.create(
                ar_agreement_id=bacs_bounce.agreement_id,
                ar_calendar_due_date=process_dd_calendar_due_date,
                ar_account_name=val_account_name,
                ar_salesperson=val_salesperson,
                ar_arrears_rental=val_arrear_value,
                ar_arrears_fee=val_arrears_fee,
                ar_arrears_total=val_arrears_total,
                ar_term=val_term,
                ar_date=process_dd_calendar_due_date,
                ar_days=999999,
                ar_notes=val_message_text + val_draw_error
                                          + val_bamf_message + val_risk_message,
                ar_agreement_phase=val_agreement_phase,
                ar_exclude_reason=val_exclude_reason,
                ar_dd_original_value=bacs_bounce.dd_value,
                ar_schedule_value=val_scheduled_value,
                ar_file_name=bacs_bounce.file_name,
                ar_uuid=val_uuid
            )

            # Write Cancelled DD record
            if bacs_bounce.dd_return_description != 'REFER TO PAYER':
                ncf_dd_call_rejections.objects.create(
                    ar_agreement_id=bacs_bounce.agreement_id,
                    ar_calendar_due_date=process_dd_calendar_due_date,
                    ar_account_name=val_account_name,
                    ar_salesperson=val_salesperson,
                    ar_date_cancelled=bacs_bounce.dd_original_process_date,
                    ar_term=val_term,
                    ar_reason_cancelled=bacs_bounce.dd_return_description,
                    ar_days_cancelled=999999,
                    ar_next_dd_due=process_dd_calendar_due_date + relativedelta(months=+1),
                    ar_days_until_dd=999999,
                    ar_notes=val_draw_error + val_bamf_message + val_risk_message,
                    ar_agreement_phase=val_agreement_phase,
                    ar_exclude_reason=val_exclude_reason,
                    ar_file_name=bacs_bounce.file_name,
                    ar_dd_original_value=bacs_bounce.dd_value,
                    ar_schedule_value=val_scheduled_value,
                    ar_uuid=val_uuid
                )

    allocated_arrears_agents = app_allocate_agents()

    arrears_update = app_process_bounce_arrears()

    # if records processed
    if val_processed:

        # Bounce Day 2, since Bounce Day 1 already done
        if first_bounceday_processed:

            d = process_dd_bounce_date02
            go_extension = go_extensions.objects.get(ap_extension_code='bounceday2')

            val_effective_datetime = datetime.date(d.year, d.month, d.day)
            val_max_due_date = val_effective_datetime

            if go_extension.ap_extension_last_interface_run < val_max_due_date:
                go_extension.ap_extension_last_interface_run = val_max_due_date
                go_extension.save()

        # Bounce Day 1
        else:

            d = process_dd_bounce_date01
            go_extension = go_extensions.objects.get(ap_extension_code='bounceday1')

            val_effective_datetime = datetime.date(d.year, d.month, d.day)
            val_max_due_date = val_effective_datetime

            if go_extension.ap_extension_last_interface_run < val_max_due_date:
                go_extension.ap_extension_last_interface_run = val_max_due_date
                go_extension.save()







