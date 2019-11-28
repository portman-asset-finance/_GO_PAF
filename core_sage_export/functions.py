
from core_agreement_crud.models import go_account_transaction_detail, go_account_transaction_summary

from core_dd_drawdowns.models import BatchHeaders, DrawDown, StatusDefinition

from .models import SageBatchHeaders, SageBatchTransactions, SageBatchDetails
from core.models import client_configuration

import re
import datetime
import random
import string
import uuid
from django.db.models import Sum
from decimal import Decimal

RECEIVED = StatusDefinition.objects.get(text_code='RECEIVED')


def generate_sage_batch_reference(due_date=datetime.datetime.now()):
    while True:
        ref = "ACCOUNTS-GO-{}-{}".format(due_date.strftime('%Y%m%d'), ''.join(random.choice(string.digits) for _ in range(4)))
        # ref = "SAGE-GO-{}-{}".format(due_date.strftime('%Y%m%d'), ''.join(random.choice(string.digits) for _ in range(4)))
        if SageBatchHeaders.objects.filter(sage_batch_ref=ref).count() == 0:
            return ref


def generate_split_sage_batch_reference(original_sage_batch_ref):
    if not original_sage_batch_ref[-2] == 'A':
        new_ref = '{}-{}'.format(original_sage_batch_ref, 'A1')
        if SageBatchHeaders.objects.filter(sage_batch_ref=new_ref).exists():
            original_sage_batch_ref = new_ref
        else:
            return new_ref
    i = 1
    partial_ref = original_sage_batch_ref[:-1]
    while True:
        new_ref = '{}{}'.format(partial_ref, i)
        if not SageBatchHeaders.objects.filter(sage_batch_ref=new_ref):
            return new_ref
        i += 1


def build_sage_transactions_from_batch(sbh_rec):

    # Step 1: Validate.
    # =================
    if not sbh_rec:
        raise Exception("Missing SageBatchHeader record.")

    if sbh_rec.processed:
        raise Exception("This batch has already been processed (1).")

    if sbh_rec.processing:
        raise Exception("This batch is already being processed (2).")

    if not isinstance(sbh_rec, SageBatchHeaders):
        raise Exception("Positional argument must be a SageBatchHeaders object.")

    if not sbh_rec.batch_header:
        raise Exception("SageBatchHeader arg missing BatchHeader object.")

    # Step 2: Set to processing
    # =========================
    sbh_rec.processing = True
    sbh_rec.save()

    # Step 3: Get batch header
    # ========================
    bh_rec = sbh_rec.batch_header

    # Step 4: Find transaction records associated with this batch
    # ===========================================================
    drawdown_filter = DrawDown.objects.filter(batch_header=bh_rec.reference, status='RECEIVED')#.exclude(status='REMOVED')

    for drawdown in drawdown_filter:

        # Step 4a: Pull in the transaction summary record
        # ===============================================
        print(drawdown.agreement_id)
        trans_summary = go_account_transaction_summary.objects.get(transactiondate=bh_rec.due_date,
                                                                   agreementnumber=drawdown.agreement_id,
                                                                   transactionsourceid__in=['GO1','GO3'],
                                                                   transactionbatch_id=bh_rec.reference)

        # Step 4b: Pull in the transaction detail record
        # ==============================================
        trans_detail = go_account_transaction_detail.objects.filter(transactiondate=bh_rec.due_date,
                                                                    agreementnumber=drawdown.agreement_id,
                                                                    transactionsourceid__in=['GO1','GO3'])

        for trans_detail_rec in trans_detail:

            sage_rec = {
                'sage_batch_transaction_id': str(uuid.uuid1()),
                'agreementnumber': drawdown.agreement_id,
                'transactiondate': bh_rec.due_date,
                'transactionsourceid': trans_summary.transactionsourceid,
                'transactionsourcedesc': trans_summary.transactionsourcedesc,
                'sage_batch_typedesc': '',
                'sage_batch_netpayment': round(trans_detail_rec.transnetpayment,2),
                'sage_batch_customercompany': trans_summary.transcustomercompany,
                'sage_batch_agreementdefname': trans_summary.transagreementdefname,
                'sage_batch_ref': sbh_rec,
            }

            if trans_detail_rec.transflag == 'Pay':

                sage_rec_capital = sage_rec.copy()
                sage_rec_capital['sage_batch_typedesc'] = 'Own Book'
                sage_rec_capital['sage_batch_netpayment'] = trans_detail_rec.transpayproprincipal

                sage_rec_interest = sage_rec.copy()
                sage_rec_interest['sage_batch_transaction_id'] = str(uuid.uuid1())
                sage_rec_interest['sage_batch_typedesc'] = 'Interest'
                sage_rec_interest['sage_batch_netpayment'] = trans_detail_rec.transpayprointerest

                SageBatchTransactions(**sage_rec_capital).save()
                SageBatchTransactions(**sage_rec_interest).save()

                continue

            # Secondaries
            if trans_detail_rec.transflag == 'Sec':
                sage_rec['sage_batch_typedesc'] = 'Secondary'

            # Risk Fee
            if trans_detail_rec.transtypeid == 3:
                sage_rec['sage_batch_typedesc'] = 'Risk Fees'

            # BAMF
            if trans_detail_rec.transtypeid in (4, 5):
                sage_rec['sage_batch_typedesc'] = 'BAMF'

            SageBatchTransactions(**sage_rec).save()

    # Step 5: Set processed flag to true
    # ==================================
    sbh_rec.processing = False
    sbh_rec.processed = datetime.datetime.now()
    sbh_rec.save()

    return True


def calculate_batch_forecast(sage_batch_ref):

    sage_batch_transactions_filter_all = SageBatchTransactions.objects.filter(sage_batch_ref=sage_batch_ref)
    sage_batch_transactions_filter_removed = SageBatchTransactions.objects.filter(remove=True, sage_batch_ref=sage_batch_ref)

    original_balance_count = sage_batch_transactions_filter_all.count()
    original_balance_amount = sage_batch_transactions_filter_all.aggregate(Sum('sage_batch_netpayment'))['sage_batch_netpayment__sum']

    rebatched_count = sage_batch_transactions_filter_removed.count()
    rebatched_amount = sage_batch_transactions_filter_removed.aggregate(Sum('sage_batch_netpayment'))['sage_batch_netpayment__sum']

    forecast = {
        'original_balance': {
            'count': original_balance_count,
            'amount': "{:,.2f}".format(original_balance_amount or 0)
        },
        'rebatched': {
            'count': rebatched_count,
            'amount': "{:,.2f}".format(rebatched_amount or 0)
        },
        'count': original_balance_count - rebatched_count,
        'amount': "{:,.2f}".format((original_balance_amount or 0) - (rebatched_amount or 0))
    }

    return forecast


# def soft_delete_drawdown(request, batch_ref, dd_id):
#
#     data = {'success': True}
#
#     if request.method == 'POST':
#
#         dd_obj = DrawDown.objects.get(id=dd_id)
#         dd_obj.status = StatusDefinition.objects.get(text_code='REMOVED')
#         dd_obj.save()
#
#         qry = {
#             'batch_header': batch_ref,
#             'status': 'OPEN'
#         }
#
#         bh_obj = BatchHeaders.objects.get(reference=batch_ref)
#
#         bh_filter = DrawDown.objects.filter(**qry)
#
#         bh_obj.total_count = bh_filter.count()
#         bh_obj.total_amount = bh_filter.aggregate(Sum('amount')).get('amount__sum', 0) or 0
#
#         go_account_transaction_summary.objects.filter(transactiondate=bh_obj.due_date,
#                                                       agreementnumber=dd_obj.agreement_id).update(transactionbatch_id='')
#
#         # data.update({
#         #     'forecast': forecast_prediction(batch_ref)
#         # })
#
#     return JsonResponse(data)



# def sage_prediction(ref):
#
#     qry = {
#         # 'status': 'OPEN',
#         'sage_batch_ref_id': ref
#     }
#
#     open_filter = SageBatchTransactions.objects.filter(**qry)
#     open_count = open_filter.count()
#     open_amount = open_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     removed_filter = SageBatchTransactions.objects.filter(sage_batch_ref_id=ref, status='REMOVED')
#     removed_count = removed_filter.count()
#     removed_amount = removed_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     inactive_dd_filter = SageBatchTransactions.objects.filter(dd_reference__isnull=False, ddi_status='I', **qry)
#     inactive_dd_count = inactive_dd_filter.count()
#     inactive_dd_amount = inactive_dd_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     no_setup_filter = SageBatchTransactions.objects.filter(dd_reference__isnull=True, **qry)
#     no_setup_count = no_setup_filter.count()
#     no_setup_amount = no_setup_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     active_dd_filter = SageBatchTransactions.objects.filter(dd_reference__isnull=False, ddi_status='A', **qry)
#     active_dd_count = active_dd_filter.count()
#     active_dd_amount = active_dd_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     grand_total_filter = SageBatchTransactions.objects.filter(sage_batch_ref_id=ref)
#     grand_total_count = grand_total_filter.count()
#     grand_total_amount = grand_total_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)
#
#     total_bounce_count = inactive_dd_count + no_setup_count
#     total_bounce_amount = inactive_dd_amount + no_setup_amount
#
#     data = {
#         'open': {
#             'count': open_count,
#             'amount': '{:,.2f}'.format(open_amount)
#         },
#         'removed': {
#             'count': removed_count,
#             'amount': '{:,.2f}'.format(removed_amount)
#         },
#         'inactive': {
#             'count': inactive_dd_count,
#             'amount': '{:,.2f}'.format(inactive_dd_amount)
#         },
#         'no_setup': {
#             'count': no_setup_count,
#             'amount': '{:,.2f}'.format(no_setup_amount)
#         },
#         'active': {
#             'count': active_dd_count,
#             'amount': '{:,.2f}'.format(active_dd_amount)
#         },
#         'bounces': {
#             'count': total_bounce_count,
#             'amount': '{:,.2f}'.format(total_bounce_amount)
#         },
#         'grand_total': {
#             'count': grand_total_count,
#             'amount': '{:,.2f}'.format(grand_total_amount)
#         }
#     }
#
#     return data

# def build_sage_details_from_batch(bh_rec):
#
#     dd_call_debtor = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date).aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_ownbook_lease = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Lease Agreeement',
#                                                                   sage_batch_typedesc= 'Own Book').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_interest_lease = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Lease Agreeement',
#                                                                   sage_batch_typedesc='Interest').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_riskfee_lease = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Lease Agreeement',
#                                                                   sage_batch_typedesc='Risk Fee').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_bamf_lease = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Lease Agreeement',
#                                                                   sage_batch_typedesc='BAMF').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_secondary_lease = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Lease Agreeement',
#                                                                   sage_batch_typedesc='Secondary').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_ownbook_hp = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                      sage_batch_agreementdefname='Hire Purchase',
#                                                                      sage_batch_typedesc='Own Book').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_interest_hp = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                       sage_batch_agreementdefname='Hire Purchase',
#                                                                       sage_batch_typedesc='Interest').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_riskfee_hp = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                      sage_batch_agreementdefname='Hire Purchase',
#                                                                      sage_batch_typedesc='Risk Fee').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_bamf_hp = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                   sage_batch_agreementdefname='Hire Purchase',
#                                                                   sage_batch_typedesc='BAMF').aggregate(Sum('sage_batch_netpayment'))
#
#     sage_transactions_secondary_hp = SageBatchTransactions.objects.get(transactiondate=bh_rec.due_date,
#                                                                        sage_batch_agreementdefname='Hire Purchase',
#                                                                        sage_batch_typedesc='Secondary').aggregate(Sum('sage_batch_netpayment'))
#
#     NWCF= client_configuration.objects.get(client_id='NWCF')
#     tax= NWCF.sales_tax
#     print(tax)
#
#     sage_detail_rec_ownbook_lease = {
#         'sage_batch_detail_id':'',
#         'account_reference': 'Own Book - Lease (1102)',
#         'type':'JC',
#         'nominal_account_ref':'1102',
#         # 'department_code':'',
#         'date': bh_rec.due_date,
#         'sage_batch_details':'GoDDCall-Batch',
#         'net_amount': sage_transactions_ownbook_lease,
#         'tax_code':'T2',
#         'tax_amount': decimal(tax)*sage_transactions_ownbook_lease,
#     }
#     SageBatchDetails(**sage_detail_rec_ownbook_lease).save()
#
#     sage_detail_rec_ownbook_hp = {
#         'sage_batch_detail_id': '',
#         'account_reference': 'Own Book - HP (1102)',
#         'type': 'JC',
#         'nominal_account_ref': '1102',
#         # 'department_code':'',
#         'date': bh_rec.due_date,
#         'sage_batch_details': 'GoDDCall-Batch',
#         'net_amount': sage_transactions_ownbook_hp,
#         'tax_code': 'T2',
#         'tax_amount': decimal(tax) * sage_transactions_ownbook_hp,
#     }
#     SageBatchDetails(**sage_detail_rec_ownbook_hp).save()