
import random
import string
import datetime
import inspect
import re

from django.db.models import Sum, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from decimal import Decimal

from .models import DrawDown, BatchHeaders, StatusDefinition, BatchLock, SyncDrawdowns

from core_direct_debits.models import DDHistory

from core.models import ncf_dd_status_text

from core_dd_datacash.functions import batch_drawdowns
from core.functions_go_id_selector import client_configuration

from core_sage_export.models import SageBatchHeaders
from core_sage_export.functions import generate_sage_batch_reference

from core_agreement_crud.models import go_agreement_querydetail, go_agreements, go_account_transaction_detail, \
                                       go_account_transaction_summary, go_agreement_index, go_funder

from core_eazycollect.functions import send_bulk_payments

OPEN = None
RECEIVED = None
PROCESSING = None

try:
    OPEN = StatusDefinition.objects.get(text_code='OPEN')
    RECEIVED = StatusDefinition.objects.get(text_code='RECEIVED')
    PROCESSING = StatusDefinition.objects.get(text_code='PROCESSING')
except:
    pass


def generate_batch_reference(batch_prefix, due_date=datetime.datetime.now()):
    while True:
        # go_id = go_agreement_index.objects.get(agreement_id=rec.agreementnumber)
        # # if go_id.funder_id == 1:
        ref = "GO-{}-{}-{}".format(batch_prefix, due_date.strftime('%Y%m%d'), ''.join(random.choice(string.digits) for _ in range(6)))
        if BatchHeaders.objects.filter(reference=ref).count() == 0:
            return ref


def get_batches(request, context):

    query = {}
    for k in ('reference__contains', 'due_date', 'total_amount', 'status', 'funder'):
        if request.GET.get(k):
            query[k] = request.GET[k]
    if 'status' in query:
        query['status'] = StatusDefinition.objects.get(text_code=query['status'])

    if query:
        recs = BatchHeaders.objects.filter(**query).order_by('-id')
    else:
        recs = BatchHeaders.objects.all().order_by('-id')

    # Get BatchLocks
    new_recs = []
    for rec in recs:
        new_rec = {
            'id': rec.id,
            'reference': rec.reference,
            'total_count': rec.total_count,
            'total_amount': rec.total_amount,
            'due_date': rec.due_date,
            'call_date': rec.call_date,
            'status': rec.status,
            'created': rec.created,
            'user': rec.user,
            'info': rec.info,
            'sent': rec.sent,
            'response': rec.response,
            'funder_id': rec.funder.funder_code,
            'sagewisdom_processed': rec.sagewisdom_processed,
            'batch_lock': BatchLock.objects.filter(released__isnull=True, batch_header=rec.id).exists()
        }
        if new_rec['batch_lock']:
            new_batch_filter = BatchLock.objects.filter(released__isnull=True,
                                                        batch_header=rec.id).order_by('-id')
            if new_batch_filter.count() > 0:
                new_rec['batch_lock'] = new_batch_filter[:1][0]

        new_recs.append(new_rec)

    recs = new_recs

    paginator = Paginator(recs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    context['records'] = pub
    context['filter'] = query
    context['statuses'] = StatusDefinition.objects.all()
    context['created'] = request.GET.get('created')
    context['open'] = request.GET.get('open')

    return pub


def sync_drawdown_table(due_date, user=None, recs=None, call_date=None, funders=None):
    """
    Syncs the agreement table with the drawdowns table, creates a batch_header record
    :return:
    """

    # Step 1: Get agreements
    ########################
    # if not recs:
    #     correct_agreements = go_agreement_querydetail.objects.filter(Q(go_id__manual_payments=0) |
    #                                                                  Q(go_id__manual_payments__isnull=True),
    #                                                                  agreement_stage=4, agreementclosedflag_id='901')
    #     agreements = [row.agreementnumber for row in correct_agreements]
    #     search_obj = {
    #         'agreementnumber__in': agreements,
    #         'transagreementclosedflag': '901',
    #         'transactiondate': datetime.datetime.strptime(due_date, "%Y-%m-%d")
    #     }
    #     customer_recs = go_account_transaction_summary.objects.filter(**search_obj)
    # else:
    #     customer_recs = recs

    new_batches = []
    existing_batches = []

    # Step 1: Get funders.
    # ====================
    funders = go_funder.objects.filter(selectable=True)

    # Step 2: Loop through each funder
    # ================================
    for row in funders:

        # Step 3: Is there already an open batch for this funder?
        # =======================================================
        try:
            bh_rec = BatchHeaders.objects.get(status='OPEN', funder=row, due_date=due_date)
            existing_batches.append(bh_rec.id)
            continue
        except:
            pass

        # Step 4: Get records from the transaction summary table
        # ======================================================
        if not recs:
            search_obj = {
                'transagreementclosedflag': '901',
                'transactionstatus': '901',
                'transactiondate': datetime.datetime.strptime(due_date, "%Y-%m-%d"),
                'transactionsourcedesc__in': ['Primary', 'Secondary']
            }
            # customer_recs = AnchorimportAccountTransactionSummary.objects.filter(**search_obj)
            customer_recs = go_account_transaction_summary.objects.filter(**search_obj)
        else:
            customer_recs = recs

        if not call_date:
            call_date = due_date

        # Step 5: Build BatchHeader dict
        # ==============================
        bh_rec = {
            'due_date': due_date,
            'reference': generate_batch_reference(row.batch_prefix, due_date=datetime.datetime.strptime(due_date, "%Y-%m-%d")),
            'total_amount': Decimal(0),
            'total_count': 0,
            'status': StatusDefinition.objects.get(text_code='OPEN'),
            'user': user,
            'call_date': call_date,
            'funder': row
        }

        bh_obj = None

        try:

            # Step 6: Loop through each transaction and build drawdowns
            # =========================================================
            for rec in customer_recs:

                go_id = go_agreement_index.objects.get(agreement_id=rec.agreementnumber)

                if not go_id.funder_id == row.id:
                    continue

                if go_id.manual_payments or not go_id.agreement_origin_flag:
                    continue

                agreement_rec = go_agreements.objects.get(agreementnumber=rec.agreementnumber)
                if rec.transactiondate < agreement_rec.agreementfirstpaymentdate:
                    continue

                search_obj = {
                    'agreement_id': rec.agreementnumber,
                    'due_date': datetime.datetime.strptime(due_date, "%Y-%m-%d")
                }

                # Step 7: Does a drawdown record already exist?
                # =============================================
                if not DrawDown.objects.filter(**search_obj).exists() or (DrawDown.objects.filter(status='REMOVED',
                                                                                                  **search_obj).exists()
                                                                          and not DrawDown.objects.filter(status='RECEIVED',
                                                                                                          **search_obj).exists()):

                    try:
                        dd_status = ncf_dd_status_text.objects.get(dd_text_code=rec.transagreementddstatus_id)
                    except:
                        dd_status = None

                    dd_rec = {
                        'due_date': due_date,
                        'agreement_id': rec.agreementnumber,
                        'customer_name': rec.transcustomercompany,
                        'agreement_type': rec.transagreementdefname,
                        'agreement_phase': rec.transactionsourcedesc,
                        'status': StatusDefinition.objects.get(text_code='OPEN'),
                        #'amount': Decimal('{:.2f}'.format(rec.transgrosspayment)),
                        'amount': rec.transgrosspayment,
                        'user': user,
                        'ddi_status':  dd_status
                    }

                    bh_rec['total_count'] += 1
                    bh_rec['total_amount'] += rec.transgrosspayment

                    dd_history = DDHistory.objects.filter(agreement_no=rec.agreementnumber,
                                                          sequence=9999).order_by('-created')[:1]

                    if dd_history:
                        dd_rec.update({
                            'sort_code': dd_history[0].sort_code,
                            'account_name': dd_history[0].account_name,
                            'account_number': dd_history[0].account_number,
                            'reference': dd_history[0].reference,
                            'dd_reference': dd_history[0].dd_reference
                        })

                    try:
                        go_id = go_agreement_index.objects.get(agreement_id=rec.agreementnumber)
                        dd_rec['agreement_origin_flag'] = go_id.agreement_origin_flag
                        dd_rec['funder_id'] = go_id.funder_id

                    except:
                        pass

                    dd_obj = DrawDown(**dd_rec)
                    dd_obj.save()

                    if bh_rec['total_count'] == 1:
                        bh_obj = BatchHeaders(**bh_rec)
                        bh_obj.save()

                    dd_obj.batch_header = bh_obj
                    dd_obj.save()

                    rec.transactionbatch_id = bh_obj.reference
                    rec.save()
                    go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

            if bh_rec['total_count'] > 0 and bh_obj:
                bh_obj.total_count = bh_rec['total_count']
                bh_obj.total_amount = bh_rec['total_amount']
                bh_obj.funder_id = row
                bh_obj.save()
                bh_rec['id'] = bh_obj.id

        except Exception as e:
            if bh_obj:
                bh_obj.delete()
            raise e

        if bh_rec.get('id'):
            new_batches.append(bh_rec['id'])

    retval = {
        'new_batches': new_batches,
        'existing_batches': existing_batches
    }

    return retval


def process_batch(batch_ref):

    config = client_configuration.objects.get(client_id='NWCF')

    data = []

    bh_rec = BatchHeaders.objects.get(reference=batch_ref)
    if bh_rec.status != OPEN:
        raise Exception('Processing failed due to incorrect status. ' +
                        'Please ensure a batch has not already been sent for this due date.')

    bh_rec.status = PROCESSING
    bh_rec.save()

    # Check for additions to the batch.
    changes = resync_drawdowns_with_dd_history(batch_ref)
    if len(changes) > 0:
        # Return changes
        bh_rec.status = OPEN
        bh_rec.save()
        return changes

    # raise Exception("Returning")
    recs = DrawDown.objects.filter(batch_header=batch_ref, status=OPEN)

    for rec in recs:

        # Check STATUS is still OPEN
        if rec.status != OPEN:
            raise Exception('Processing failed due to incorrect status. ' +
                            'Please ensure a batch has not already been sent for this due date.')

        # Update status to PROCESSING
        rec.status = PROCESSING
        rec.save()

        data.append({
            'agreement_id': rec.agreement_id,
            'account_name': rec.account_name,
            'sort_code': rec.sort_code,
            'account_number': rec.account_number,
            'reference': rec.reference,
            'dd_reference': rec.dd_reference,
            'amount': rec.amount,
            'drawdown': rec,
            'due_date': rec.due_date.strftime("%Y%m%d"),
            'call_date': bh_rec.call_date.strftime("%Y%m%d"),
        })

    bh_rec = BatchHeaders.objects.get(reference=batch_ref)  # <- Values have changed via resync. Get record again.

    try:

        sent_dt = datetime.datetime.now()

        dd_args = {
            'recs': data,
            'batch_ref': batch_ref,
            'total_count': bh_rec.total_count,
            'total_amount': bh_rec.total_amount
        }

        if bh_rec.funder.provider == 'datacash':
            batch_drawdowns(**dd_args)

        elif bh_rec.funder.provider == 'eazycollect':
            send_bulk_payments(**dd_args)

        res_dt = datetime.datetime.now()

        bh_rec.sent = sent_dt
        bh_rec.info = 'ACCEPTED'
        bh_rec.status = RECEIVED
        bh_rec.response = res_dt
        bh_rec.save()

        for rec in recs:
            rec.status = RECEIVED
            rec.save()

            go_id = go_agreement_index.objects.get(agreement_id=rec.agreement_id)
            agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=rec.agreement_id)

            history_rec = {'go_id': go_id,
                           'agreementnumber': rec.agreement_id,
                           'transtypeid': '12',
                           'transactiondate': rec.due_date,
                           'transactionsourceid': 'GO9',
                           'transtypedesc': 'Direct Debit',
                           'transflag': 'Col',
                           'transfallendue': '1',
                           'transnetpayment': -round((rec.amount) / Decimal(config.other_sales_tax),2),
                           'transgrosspayment': -rec.amount,
                           'transvatpayment': -(round(round((rec.amount) / Decimal(config.other_sales_tax),2) * Decimal(config.sales_tax), 2)),
                           }



            ats_history_rec = {'go_id': go_id,
                               'agreementnumber': go_id,
                               'transtypeid': '12',
                               'transactiondate': rec.due_date,
                               'transactionsourceid': 'GO9',
                               'transtypedesc': 'Direct Debit',
                               'transflag': 'Col',
                               'transfallendue': '0',
                               'transnetpayment': -round((rec.amount) / Decimal(1.2),2),
                               'transgrosspayment': -round(rec.amount,2),
                               'transactionsourcedesc': 'HISTORY',
                               'transagreementagreementdate': agreement_detail.agreementagreementdate,
                               'transagreementauthority': agreement_detail.agreementauthority,
                               'transagreementclosedflag_id': '901',
                               'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                               'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                               'transagreementdefname': 'Lease Agreement',
                               'transcustomercompany': agreement_detail.customercompany,
                               'transddpayment': '1',
                               # TODO: 'transnetpaymentcapital': -round(transactionsummary.transnetpaymentcapital,2),
                               # 'transnetpaymentinterest': -round(transactionsummary.transnetpaymentinterest,2),
                               }

            if agreement_detail.agreementdefname == 'Hire Purchase':
                ats_history_rec['transagreementdefname'] = 'Hire Purchase'
                ats_history_rec['transnetpayment'] = -rec.amount
                history_rec['transnetpayment'] = -rec.amount
                history_rec['transgrosspayment'] = -round((rec.amount) / Decimal(config.other_sales_tax),2)
                history_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

            go_account_transaction_detail(**history_rec).save()
            go_account_transaction_summary(**ats_history_rec).save()

            # Create Sage Batch Header
            sage_header_details = {
                'batch_header': bh_rec,
                'sage_batch_ref': generate_sage_batch_reference(bh_rec.due_date),
                'sage_batch_type': 'Due Day Batch',
                'total_debit_amount': round((bh_rec.total_amount)/config.other_sales_tax, 2),
                'total_credit_amount': round((-bh_rec.total_amount)/config.other_sales_tax, 2),
                'status': 'NOT RECORDED',
                'sage_batch_date': bh_rec.due_date
            }
            SageBatchHeaders(**sage_header_details).save()

            # History Posting

    except Exception as e:

        bh_rec.status = OPEN
        bh_rec.info = str(e)

        for rec in recs:
            rec.status = OPEN
            rec.save()

        bh_rec.save()

        print(e)

        raise e

    return bh_rec.id


def forecast_prediction(batch_header_reference):

    qry = {
        'status': 'OPEN',
        'batch_header': batch_header_reference
    }

    open_filter = DrawDown.objects.filter(**qry)
    open_count = open_filter.count()
    open_amount = open_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    removed_filter = DrawDown.objects.filter(batch_header=batch_header_reference, status='REMOVED')
    removed_count = removed_filter.count()
    removed_amount = removed_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    inactive_dd_filter = DrawDown.objects.filter(dd_reference__isnull=False, ddi_status='I', **qry)
    inactive_dd_count = inactive_dd_filter.count()
    inactive_dd_amount = inactive_dd_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    no_setup_filter = DrawDown.objects.filter(dd_reference__isnull=True, **qry)
    no_setup_count = no_setup_filter.count()
    no_setup_amount = no_setup_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    active_dd_filter = DrawDown.objects.filter(dd_reference__isnull=False, ddi_status='A', **qry)
    active_dd_count = active_dd_filter.count()
    active_dd_amount = active_dd_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    grand_total_filter = DrawDown.objects.filter(batch_header=batch_header_reference)
    grand_total_count = grand_total_filter.count()
    grand_total_amount = grand_total_filter.aggregate(Sum('amount')).get('amount__sum', Decimal(0)) or Decimal(0)

    total_bounce_count = inactive_dd_count + no_setup_count
    total_bounce_amount = inactive_dd_amount + no_setup_amount

    data = {
        'open': {
            'count': open_count,
            'amount': '{:,.2f}'.format(open_amount)
        },
        'removed': {
            'count': removed_count,
            'amount': '{:,.2f}'.format(removed_amount)
        },
        'inactive': {
            'count': inactive_dd_count,
            'amount': '{:,.2f}'.format(inactive_dd_amount)
        },
        'no_setup': {
            'count': no_setup_count,
            'amount': '{:,.2f}'.format(no_setup_amount)
        },
        'active': {
            'count': active_dd_count,
            'amount': '{:,.2f}'.format(active_dd_amount)
        },
        'bounces': {
            'count': total_bounce_count,
            'amount': '{:,.2f}'.format(total_bounce_amount)
        },
        'grand_total': {
            'count': grand_total_count,
            'amount': '{:,.2f}'.format(grand_total_amount)
        }
    }

    return data


def resync_drawdowns_with_dd_history(batch_header_reference, user=None):
    """
    Updates a DrawDown record attached to a given batch_header_reference
    with a DD History record (if there is one)
    """
    # return []

    bh_rec = BatchHeaders.objects.get(reference=batch_header_reference)

    recs = SyncDrawdowns.objects.filter(batch_reference=batch_header_reference, funder_id=bh_rec.funder.funder_code, )
    import pprint
    pprint.pprint(recs)
    updated = False

    changes = []
    removed = 0
    additions = 0

    for rec in recs:
        print(rec.agreement_id)

        if not rec.agreement_id:
            continue

        if rec.extract_type == 'T2' and rec.extract_count == 2:

            update_rec = {}

            if rec.drawdown_gross_value != rec.txn_gross_value:
                update_rec['amount'] = rec.txn_gross_value

            if rec.drawdown_reference != rec.txn_reference:
                update_rec.update({
                    'reference': rec.txn_reference,
                    'sort_code': rec.txn_sort_code,
                    'account_name': rec.txn_account_name,
                    'account_number': rec.txn_account_number,
                    'dd_reference' : rec.dd_reference,
                })

            if update_rec:
                updated = True
                dd_rec = DrawDown.objects.get(batch_header=batch_header_reference,
                                              due_date=rec.due_date, agreement_id=rec.agreement_id)
                for k in update_rec:
                    setattr(dd_rec, k, update_rec[k])
                go_id = go_agreement_index.objects.get(agreement_id=rec.agreement_id)
                go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')
                dd_rec.save()

        elif rec.extract_type == 'T1' and rec.extract_count == 1:
            updated = True
            DrawDown.objects.get(agreement_id=rec.agreement_id,
                                 due_date=rec.due_date, batch_header=batch_header_reference).delete()
            removed += 1

        elif rec.extract_type == 'T2' and rec.extract_count == 1:
            try:
                txn_rec = go_account_transaction_summary.objects.get(transactiondate=rec.due_date,
                                                                     transagreementclosedflag='901',
                                                                     transactionsourceid__in=('SP1', 'SP2', 'SP3', 'GO1', 'GO3'),
                                                                     agreementnumber=rec.agreement_id)
            except Exception as e:
                print(e)
                continue
            go_id = go_agreement_index.objects.get(agreement_id=rec.agreement_id)
            agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=rec.agreement_id)
            updated = True
            customer_recs = go_account_transaction_summary.objects.filter(agreementnumber=rec.agreement_id)
            # dd_status = ncf_dd_status_text.objects.get(dd_text_code=rec.transagreementddstatus_id)
            for record in customer_recs:
                try:
                    dd_status = ncf_dd_status_text.objects.get(dd_text_code=rec.transagreementddstatus_id)
                except:
                    dd_status = None

            dd_rec = {
                'due_date': rec.due_date,
                'agreement_id': rec.agreement_id,
                'customer_name': txn_rec.transcustomercompany,
                'agreement_type': txn_rec.transagreementdefname,
                'agreement_phase': txn_rec.transactionsourcedesc,
                'status': OPEN,
                'amount': Decimal('{:.2f}'.format(txn_rec.transgrosspayment)),
                'batch_header': bh_rec,
                'reference': rec.txn_reference,
                'sort_code': rec.txn_sort_code,
                'account_name': rec.txn_account_name,
                'account_number': rec.txn_account_number,
                'dd_reference': rec.dd_reference,
                'ddi_status': ncf_dd_status_text.objects.get(dd_text_code=record.transagreementddstatus_id),
                'user': bh_rec.user,
                'funder_id': go_id.funder_id,
            }

            try:
                go_id = go_agreement_index.objects.get(agreement_id=rec.agreement_id)
                dd_rec['agreement_origin_flag'] = 'GO'
            except:
                pass

            changes.append({
                'agreement_id': rec.agreement_id,
                'amount': rec.txn_gross_value
            })
            additions += 1

            DrawDown(**dd_rec).save()
            txn_rec.transactionbatch_id = batch_header_reference
            go_id = go_agreement_index.objects.get(agreement_id=rec.agreement_id)
            go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

            txn_rec.save()

    bh_rec.total_count = DrawDown.objects.filter(batch_header=batch_header_reference, status='OPEN').count()
    bh_rec.total_amount = DrawDown.objects.filter(batch_header=batch_header_reference,
                                                  status='OPEN').aggregate(Sum('amount')).get('amount__sum', 0) or 0

    bh_rec.save()

        # print(bh_rec.total_count)

    return changes

    # T1, 1: Remove from batch
    # for rec for recs:
    #     print(rec)

    # T2, 1: Creating a batch

    # bh_rec = BatchHeaders.objects.get(reference=batch_header_reference)

    recs = DrawDown.objects.filter(batch_header=batch_header_reference)

    i = 1

    for rec in recs:

        if False:

            dd_history = DDHistory.objects.get(agreement_no=rec.agreement_id, sequence=9999)

            if dd_history:
                rec.sort_code = dd_history.sort_code
                rec.account_name = dd_history.account_name
                rec.account_number = dd_history.account_number
                rec.reference = dd_history.reference
                rec.dd_reference = dd_history.dd_reference
                rec.save()

            # if i == 1:
            #     print(datetime.datetime.now())

        transaction_rec = go_account_transaction_summary.objects.get(transactiondate=rec.due_date,
                                                                     agreementnumber=rec.agreement_id)

        rec.amount = transaction_rec
        rec.save()

        i = i + 1


    return True
