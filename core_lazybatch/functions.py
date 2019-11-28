
import numpy

from datetime import date, datetime, timedelta

from .models import LazyBatchConfig, LazyBatchLog

from core.functions_go_id_selector import daysbeforecalldd

from core_dd_drawdowns.models import DrawDown
from core_dd_drawdowns.functions import sync_drawdown_table

from core_agreement_crud.functions import get_holidays
from core_agreement_crud.models import go_agreements, go_account_transaction_summary, go_agreement_index, go_funder

PRINT_DEBUG_MESSAGES = False


def _print(message):
    if PRINT_DEBUG_MESSAGES:
        print(message)


def create_batches(**kwargs):
    """
    kwargs: GoSchedulerConfig job parameters.

    """

    # Step 2: Get due date
    # ====================
    due_date = numpy.busday_offset(date.today(), daysbeforecalldd(),
                                   roll='forward', holidays=get_holidays()).astype(date)

    due_date = due_date + timedelta(days=kwargs.get('call_date_lead_days', 0) or 0)

    due_date = datetime.strptime("2019-09-28", "%Y-%m-%d") # TESTING TESTING TESTING

    _print("Due Date:")
    _print("-----------------------------------------------")

    _print("kwargs:")
    _print("-----------------------------------------------")
    _print(kwargs)

    # Step 3: Pull in batches profiles
    # ================================
    lazybatches_queryset = LazyBatchConfig.objects.filter(enabled=1).order_by('-run_date', 'priority')

    # Step 4: Loop through each batch profiles and find
    #         related drawdowns from the summary table.
    # ==================================================
    for lazybatch in lazybatches_queryset:

        _print('lazybatch:')
        _print("-----------------------------------------------")
        _print(lazybatch)

        # Step 4a: Is this a single run profile?
        # ======================================
        if not lazybatch.repeat == 1:
            if lazybatch.last_ran:
                continue

        _print('Passed test: single run.')

        if lazybatch.run_date:
            if not date.today() >= lazybatch.run_date.date():
                continue
            if lazybatch.last_ran:
                continue

        _print('Passed test: run date.')

        # Step 4b: Set batch job to 'in_progress'
        # =======================================
        lazybatch.in_progress = 1
        lazybatch.save()

        _print('Set in_progress.')

        # Step 4c: Pull in funders
        # ========================
        funders = go_funder.objects.filter(selectable=True)

        # Step 4d: Loop through each funder and get each transaction record
        # =================================================================

        for funder in funders:

            _print('funder:')
            _print("-----------------------------------------------")
            _print(funder)

            transactions_to_include = []

            # Step 4c: Build transaction query
            # ================================
            transaction_criteria = {
                'transagreementclosedflag': '901',
                'transactiondate': due_date,
                'transactionsourcedesc__in': ['Primary', 'Secondary']
            }

            # Step 4d: Is this a cleanup job?
            # ===============================
            # if kwargs.get('cleanup'):
            #     if kwargs['cleanup'] == lazybatch.batch_name:
            #         del(transaction_criteria['transactiondate'])
            #         transaction_criteria['transactiondate__lte'] = due_date
            #         continue

            # Step 4e: Fetch records.
            # =======================
            transaction_recs = go_account_transaction_summary.objects.filter(**transaction_criteria)

            _print('No of transactions')
            _print("-----------------------------------------------")
            _print(len(transaction_recs or []))

            # Step 4f: Loop through transactions
            # ==================================
            for transaction_rec in transaction_recs:

                # Step 4f.1: Does this transaction already belong in a batch?
                # ===========================================================
                drawdown_criteria = {
                    'due_date': due_date.strftime("%Y-%m-%d"),
                    'agreement_id': transaction_rec.agreementnumber
                }
                if not DrawDown.objects.filter(**drawdown_criteria).exists() or (DrawDown.objects.filter(status='REMOVED',
                                                                                                  **drawdown_criteria).exists()
                                                                                 and not DrawDown.objects.filter(status='RECEIVED',
                                                                                                                 **drawdown_criteria).exists()):

                    _print('Passed test: Not in a batch already.')

                    # Step 4f.2: Get the go_agreement_index record.
                    # =============================================
                    go_index_rec = go_agreement_index.objects.get(agreement_id=transaction_rec.agreementnumber)

                    # Step 4f.3: Get the go_agreements record.
                    # ========================================
                    go_agreements_rec = go_agreements.objects.get(agreementnumber=transaction_rec.agreementnumber)

                    # Step 4f.4: Make sure this summary record is for the correct funder.
                    # ===================================================================
                    if not go_index_rec.funder.funder_code == funder.funder_code:
                        continue

                    # Step 4f.2: Are we filtering on agreement type?
                    # ==============================================
                    if lazybatch.agreement_type:
                        if not go_agreements_rec.agreementagreementtypeid == lazybatch.agreement_type:
                            continue

                    # Step 4f.3: Are we filtering on agreement phase?
                    # ===============================================
                    if lazybatch.agreement_phase:
                        if not transaction_rec.transactionsourcedesc == lazybatch.agreement_phase:
                            continue

                    # Step 4f.4: Are we filtering on source type?
                    # ==========================================
                    if lazybatch.source_type:
                        if lazybatch.source_type == 'GO':
                            if not go_index_rec.agreement_origin_flag == 'GO':
                                continue
                        else:
                            if go_index_rec.agreement_origin_flag == 'GO':
                                continue

                    # Step 4f.5: Passed all tests. Append ready for processing.
                    # =========================================================
                    transactions_to_include.append(transaction_rec)

            # Step 5: Create batch
            # ====================

            if len(transactions_to_include) > 0:
                sync_drawdown_table(due_date.strftime("%Y-%m-%d"), recs=transactions_to_include)

        # Step 6: Update 'last_ran' and take out of 'in_progress'
        # =======================================================
        lazybatch.last_ran = datetime.now()
        lazybatch.in_progress = 0
        lazybatch.save()

        # Step 7: Log
        # ===========
        log_object = {
            'level': 'I',
            'due_date': due_date,
            'batch': lazybatch,
            'entry': '{} batches created from {} transaction entries.'.format(len(transactions_to_include),
                                                                              len(transaction_recs))
        }
        LazyBatchLog(**log_object).save()
