import math
import re
from django.db.models import Sum
import decimal
import datetime
from datetime import timedelta
from dateutil.relativedelta import *
from django.shortcuts import render, redirect
from decimal import Decimal
from datetime import datetime
import getpass

from anchorimport.models import AnchorimportAccountTransactionSummary

from core.models import client_configuration, holiday_dates

from core.functions_go_id_selector import requiredtabs, client_configuration, riskfeenetamount

from core_agreement_crud.models import go_customers, go_agreement_querydetail, go_agreements, go_broker, go_account_transaction_detail, go_account_transaction_summary, \
                    go_agreement_definitions, go_profile_types, go_agreement_id_definitions, go_agreement_index, go_sales_authority
from core_agreement_editor.models import go_editor_history


def change_single_date_function(request,agreement_id):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer= agreement_detail.customercompany

    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate

    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:
        history_change_date = {'go_id': go_id,
                               'agreement_id': agreement_id,
                               'user': request.user,
                               'updated': datetime.now(),
                               'action': 'Changed Single Date',
                               'transaction': format(transaction_date,'%d/%m/%Y'),
                               'customercompany': customer
                               }
        go_editor_history(**history_change_date).save()
        changed_date = request.POST.get('changed_date')


        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      ,transactiondate = transaction_date
                                                      ).update(transactiondate= changed_date)
        go_account_transaction_detail.objects.filter(go_id=go_id
                                                     , transactiondate=transaction_date
                                                     ).update(transactiondate=changed_date)
        go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

        if agreement_detail.agreementfirstpaymentdate == transaction_date:
            go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementfirstpaymentdate= changed_date)

        if agreement_detail.agreementresidualdate == transaction_date:
            go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementresidualdate= changed_date)

    return batch_error


def change_future_dates_function(request,agreement_id):
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany

    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate

    changed_date = request.POST.get('changed_date')

    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:

        history_change_dates = {'go_id': go_id,
                               'agreement_id': agreement_id,
                               'user': request.user,
                               'updated': datetime.now(),
                               'action': 'Changed Future Dates',
                               'transaction': 'All dates after '+ format(transaction_date,'%d/%m/%Y'),
                               'customercompany': customer
                               }
        go_editor_history(**history_change_dates).save()

        all_future_dates_change_summary  = go_account_transaction_summary.objects.filter(go_id=go_id
                                                                               , transactiondate__gte=transaction_date)\
                                                                                .order_by('transactiondate')
        all_future_dates_change_detail = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                      transactiondate__gte=transaction_date)\
                                                                                      .order_by('transactiondate')
        go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

        changed_date = datetime.strptime(changed_date, "%Y-%m-%d")

        if agreement_detail.agreementfirstpaymentdate == transaction_date:
            go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementfirstpaymentdate=changed_date)

        if agreement_detail.agreementresidualdate == transaction_date:
            go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementresidualdate=changed_date)

        i = 0
        for row in all_future_dates_change_summary:
            wip_transaction_date = changed_date + relativedelta(months=+i)
            wip_get_date = row.transactiondate
            print(row.transactiondate)
            if agreement_detail.agreementresidualdate == row.transactiondate :
                go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementresidualdate=wip_transaction_date)
            row.transactiondate = wip_transaction_date
            row.save()

            for row2 in all_future_dates_change_detail:
                if row2.transactiondate == wip_get_date:
                    row2.transactiondate = wip_transaction_date
                    row2.save()
            i += 1

    return batch_error


def remove_single_risk_fee_function(request,agreement_id):
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')

    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany
    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate
    rf = request.POST.get('rf')
    payment_amount_extract = go_account_transaction_summary.objects.get(go_id=go_id
                                                  , transactiondate=transaction_date, transnetpayment__gte=0, transactionsourceid__in=['GO1','GO2','GO3']
                                                  )
    payment_amount = payment_amount_extract.transnetpayment
    negativeriskfee = -decimal.Decimal(rf)
    noriskfeenet =decimal.Decimal(payment_amount) + negativeriskfee

    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:
        history_change_date_rf = {'go_id': go_id,
                                  'agreement_id': agreement_id,
                                  'user': request.user,
                                  'updated': datetime.now(),
                                  'action': 'Removed Single Risk Fee',
                                  'transaction': format(transaction_date,'%d/%m/%Y'),
                                'customercompany': customer
                               }
        go_editor_history(**history_change_date_rf).save()

        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      , transactiondate=transaction_date
                                                      ).update(transnetpayment=(noriskfeenet), transnetpaymentinterest=(transaction_summary_extract.transnetpaymentinterest+negativeriskfee))
        noriskfeevat=round(noriskfeenet*decimal.Decimal(config.other_sales_tax),2)
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      , transactiondate=transaction_date
                                                      ).update(transgrosspayment=(noriskfeevat))

        if agreement_detail.agreementdefname == 'Hire Purchase':
            go_account_transaction_summary.objects.filter(go_id=go_id
                                                          , transactiondate=transaction_date
                                                          ).update(transgrosspayment=(noriskfeenet))

        go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

        atd_risk_rec = {'go_id': go_id,
                        'agreementnumber': agreement_id,
                        'transtypeid': '3',
                        'transactiondate': transaction_date,
                        'transactionsourceid': 'GO1',
                        'transtypedesc': 'Risk Fee',
                        'transflag': 'Fee',
                        'transfallendue': '0',
                        'transnetpayment': negativeriskfee,
                        'transgrosspayment': round(Decimal(negativeriskfee) * Decimal(config.other_sales_tax), 2),
                        'transvatpayment': round(Decimal(negativeriskfee) * Decimal(config.sales_tax), 2),
                        # TODO: GO#110 - Start
                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                        'transpayprointerest': round(Decimal(negativeriskfee) * Decimal(config.other_sales_tax), 2),
                        }
                        # TODO: GO#110 - End
        if agreement_detail.agreementdefname == 'Hire Purchase':
            atd_risk_rec['transgrosspayment'] = Decimal(negativeriskfee)
            atd_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
        go_account_transaction_detail(**atd_risk_rec).save()
    return batch_error


def remove_future_risk_fee_function(request,agreement_id):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany
    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate
    rf = request.POST.get('rf')
    negativeriskfee = -decimal.Decimal(rf)
    # Card 69 Issue with Risk Fee on agreements with history. Because the update does not filter just GO1 and GO3s.
    all_future_dates_change_summary = go_account_transaction_summary.objects.filter(go_id=go_id,
                                                                                    transactiondate__gte=transaction_date, transactionsourceid__in=['GO1','GO3'])
    for row in all_future_dates_change_summary:
        print(row.transactiondate, row.transactionsourceid)

    all_future_dates_change_detail = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                  transtypedesc='Risk Fee',
                                                                                  transactiondate__gte=transaction_date).order_by('transactiondate')
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:
        history_change_dates_rf = {'go_id': go_id,
                                  'agreement_id': agreement_id,
                                  'user': request.user,
                                  'updated': datetime.now(),
                                  'action': 'Removed Future Risk Fees',
                                  'transaction': 'All dates after '+ format(transaction_date,'%d/%m/%Y'),
                                  'customercompany': customer
                               }
        go_editor_history(**history_change_dates_rf).save()


        for row in all_future_dates_change_detail:
            wip_get_date = row.transactiondate
            all_future_dates_change_detail_indepth = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                                  transtypedesc='Risk Fee',
                                                                                                  transactiondate=wip_get_date).aggregate(Sum('transnetpayment'))
            wip_element_value = all_future_dates_change_detail_indepth["transnetpayment__sum"]
            if wip_element_value != 0:
                for row2 in all_future_dates_change_summary:
                    if row2.transactiondate == wip_get_date:
                        # TODO: GO#110 - Start
                        # if agreement_detail.agreementdefname == 'Lease Agreement':
                        row2.transgrosspayment = row2.transgrosspayment + round(negativeriskfee * decimal.Decimal(config.other_sales_tax), 2)

                        # if agreement_detail.agreementdefname == 'Hire Purchase':
                        #     row2.transgrosspayment = row2.transgrosspayment + negativeriskfee
                        # TODO: GO#110 - End
                        row2.transnetpayment = row2.transnetpayment + negativeriskfee
                        row2.transnetpaymentinterest = row2.transnetpaymentinterest + negativeriskfee
                        row2.save()
                        atd_risk_rec = {'go_id': go_id,
                                        'agreementnumber': agreement_id,
                                        'transtypeid': '3',
                                        'transactiondate': wip_get_date,
                                        'transactionsourceid': 'GO1',
                                        'transtypedesc': 'Risk Fee',
                                        'transflag': 'Fee',
                                        'transfallendue': '0',
                                        'transnetpayment': negativeriskfee,
                                        'transgrosspayment': round(Decimal(negativeriskfee) * Decimal(config.other_sales_tax), 2),
                                        'transvatpayment': round(Decimal(negativeriskfee) * Decimal(config.sales_tax), 2),
                                        # TODO: GO#110 - Start
                                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                        'transpayprointerest': round(Decimal(negativeriskfee) * Decimal(config.other_sales_tax), 2)
                                        }

                        # if agreement_detail.agreementdefname == 'Hire Purchase':
                        #     atd_risk_rec['transgrosspayment'] = Decimal(negativeriskfee)
                        #     atd_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                        # TODO: GO#110 - End

                        go_account_transaction_detail(**atd_risk_rec).save()
    return batch_error


def remove_single_bamf_fee_function(request,agreement_id):
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany
    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate
    bamf = request.POST.get('bamf')
    # Card 71 Issue with Refund. The error was created from removing BAMF and there was a refund on the same day. Similar to issue with risk fee, need to add, 'GO1, GO3' in the get.
    # TODO: GO#110 - Start

    payment_amount_extract = go_account_transaction_summary.objects.get(go_id=go_id, transactiondate=transaction_date, transactionsourceid__in=['GO1', 'GO3'])
    payment_amount_extract_detail = go_account_transaction_detail.objects.get(go_id=go_id, transactiondate=transaction_date, transactionsourceid__in=['GO1', 'GO3'], transflag='Pay')
    rental_amount = payment_amount_extract_detail.transnetpayment
    payment_amount = payment_amount_extract.transnetpayment
    negativebamffee = -decimal.Decimal(bamf)
    nobamffeenet = decimal.Decimal(payment_amount) + negativebamffee
    batch_error = False
    # TODO: GO#110 - End
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:

        history_change_date_bamf = {'go_id': go_id,
                                   'agreement_id': agreement_id,
                                   'user': request.user,
                                   'updated': datetime.now(),
                                   'action': 'Removed Single BAMF',
                                   'transaction': format(transaction_date,'%d/%m/%Y'),
                                   'customercompany': customer
                               }
        go_editor_history(**history_change_date_bamf).save()


        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      , transactiondate=transaction_date
                                                      ).update(transnetpayment=(nobamffeenet), transnetpaymentinterest=(transaction_summary_extract.transnetpaymentinterest+negativebamffee))

        nobamffeevat = round(nobamffeenet * decimal.Decimal(config.other_sales_tax), 2)
        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      , transactiondate=transaction_date
                                                      ).update(transgrosspayment=(nobamffeevat))
        # TODO: GO#110 - Start
        if agreement_detail.agreementdefname == 'Hire Purchase':
            wip_nobamffeevat = (round((Decimal(nobamffeenet) - Decimal(rental_amount)) * Decimal(config.other_sales_tax), 2)) + Decimal(rental_amount)
            go_account_transaction_summary.objects.filter(go_id=go_id
                                                          , transactiondate=transaction_date
                                                          ).update(transgrosspayment=(wip_nobamffeevat))
        # TODO: GO#110 - End

        go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

        atd_BAMF_rec = {'go_id': go_id,
                        'agreementnumber': agreement_id,
                        'transtypeid': '5',
                        'transactiondate': transaction_date,
                        'transactionsourceid': 'GO1',
                        'transtypedesc': 'Bi-Annual Management Fee',
                        'transflag': 'Fee',
                        'transfallendue': '0',
                        'transnetpayment': negativebamffee,
                        'transgrosspayment': round(Decimal(negativebamffee) * Decimal(config.other_sales_tax), 2),
                        'transvatpayment': round(Decimal(negativebamffee) * Decimal(config.sales_tax), 2),
                        # TODO: GO#110 - Start
                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                        'transpayprointerest': round(Decimal(negativebamffee) * Decimal(config.other_sales_tax), 2),
                        }
        # if agreement_detail.agreementdefname == 'Hire Purchase':
        #     atd_BAMF_rec['transgrosspayment'] = Decimal(nobamffeenet)
        #     atd_BAMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                        # TODO: GO#110 - End

        go_account_transaction_detail(**atd_BAMF_rec).save()
    return batch_error


def remove_future_bamf_fee_function(request,agreement_id):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany
    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate
    bamf = request.POST.get('bamf')
    negativebamffee = -decimal.Decimal(bamf)
    # Card 69 Issue with Risk Fee on agreements with history. Because the update does not filter just GO1 and GO3s.
    all_future_dates_change_summary = go_account_transaction_summary.objects.filter(go_id=go_id,
                                                                                    transactiondate__gte=transaction_date, transactionsourceid__in=['GO1','GO3'])

    all_future_dates_change_detail = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                    transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                    transactiondate__gte=transaction_date).order_by('transactiondate')
    go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:
        history_change_dates_bamf = {'go_id': go_id,
                                    'agreement_id': agreement_id,
                                    'user': request.user,
                                    'updated': datetime.now(),
                                    'action': 'Removed Future BAMFs',
                                    'transaction': 'All dates after '+ format(transaction_date,'%d/%m/%Y'),
                                    'customercompany': customer
                               }
        go_editor_history(**history_change_dates_bamf).save()

        for row in all_future_dates_change_detail:
            wip_get_date = row.transactiondate
            all_future_dates_change_detail_indepth = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                                  transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                                  transactiondate=wip_get_date).aggregate(Sum('transnetpayment'))
            wip_element_value = all_future_dates_change_detail_indepth["transnetpayment__sum"]
            if wip_element_value != 0:
                for row2 in all_future_dates_change_summary:
                    if row2.transactiondate == wip_get_date:
                        # TODO: GO#110 - Start
                        # if agreement_detail.agreementdefname == 'Lease Agreement':
                        row2.transgrosspayment = row2.transgrosspayment + round(negativebamffee * decimal.Decimal(config.other_sales_tax), 2)
                        # if agreement_detail.agreementdefname == 'Hire Purchase':
                        #     row2.transgrosspayment = row2.transgrosspayment + negativebamffee
                        # TODO: GO#110 - End
                        row2.transnetpayment = row2.transnetpayment + negativebamffee
                        row2.transnetpaymentinterest = row2.transnetpaymentinterest + negativebamffee
                        row2.save()
                        atd_BAMF_rec = {'go_id': go_id,
                                        'agreementnumber': agreement_id,
                                        'transtypeid': '5',
                                        'transactiondate': wip_get_date,
                                        'transactionsourceid': 'GO1',
                                        'transtypedesc': 'Bi-Annual Management Fee',
                                        'transflag': 'Fee',
                                        'transfallendue': '0',
                                        'transnetpayment': negativebamffee,
                                        'transgrosspayment': round(Decimal(negativebamffee) * Decimal(config.other_sales_tax), 2),
                                        'transvatpayment': round(Decimal(negativebamffee) * Decimal(config.sales_tax), 2),
                                        # TODO: GO#110 - Start
                                        'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                        'transpayprointerest': round(Decimal(negativebamffee) * Decimal(config.other_sales_tax), 2),
                                        }

                        # if agreement_detail.agreementdefname == 'Hire Purchase':
                        #     atd_BAMF_rec['transgrosspayment'] = Decimal(negativebamffee)
                        #     atd_BAMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                        # TODO: GO#110 - End

                        go_account_transaction_detail(**atd_BAMF_rec).save()
    return batch_error


def reschedule_function(request,agreement_id):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    customer = agreement_detail.customercompany

    rescheduled_date = request.POST.get('rescheduled_date')
    rescheduled_instalment_net = request.POST.get('rescheduled_instalment_net')
    new_term = request.POST.get('new_term')
    new_term= int(new_term)
    go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')
    # transaction_summary_extract = go_account_transaction_summary.objects.get(transactiondate__gt=rescheduled_date )
    # transaction_date = transaction_summary_extract.transactiondate
    #
    # batch_error = False
    # if transaction_summary_extract.transactionbatch_id:
    #     batch_error = transaction_summary_extract.transactionbatch_id
    # else:

    history_change_reschedule = {'go_id': go_id,
                                 'agreement_id': agreement_id,
                                 'user': request.user,
                                 'updated': datetime.now(),
                                 'action': 'Rescheduled',
                                 'transaction': 'All dates after '+ rescheduled_date,
                                 'customercompany': customer
                               }
    go_editor_history(**history_change_reschedule).save()


    all_future_dates_change_summary  = go_account_transaction_summary.objects.filter(go_id=go_id,
                                                                                     transactiondate__gte=rescheduled_date, transactionsourceid__in=['GO1', 'GO3'])\
                                                                                     .delete()

    all_future_dates_change_detail = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                transactiondate__gte=rescheduled_date, transactionsourceid__in=['GO1', 'GO3'])\
                                                                                .delete()

    rescheduled_date = datetime.strptime(rescheduled_date, "%Y-%m-%d")

    principal = str(agreement_detail.agreementoriginalprincipal)

    Interest = go_id.term * Decimal(re.sub(',', '', rescheduled_instalment_net)) - Decimal(re.sub(',', '', principal))
    multiplier = (go_id.term) * (go_id.term + 1) / 2
    multiplier2 = Decimal(Interest) / Decimal(multiplier)

    for i in range(new_term):
        ats_rentals_rec = {'go_id': go_id,
                           'agreementnumber': agreement_id,
                           'transtypeid': '0',
                           'transactiondate': rescheduled_date + relativedelta(months=+i),
                           'transactionsourceid': 'GO1',
                           'transtypedesc': '',
                           'transflag': '',
                           'transfallendue': '0',
                           'transnetpayment': round(Decimal(re.sub(',', '', rescheduled_instalment_net)),2),
                           'transgrosspayment': round(Decimal(re.sub(',', '', rescheduled_instalment_net))*Decimal(config.other_sales_tax),2),
                           'transactionsourcedesc': 'Primary',
                           'transagreementagreementdate': agreement_detail.agreementagreementdate,
                           'transagreementauthority': agreement_detail.agreementauthority,
                           'transagreementclosedflag_id': '901',
                           'transactionstatus': '901',
                           'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                           'transcustomercompany': agreement_detail.customercompany,
                           'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                           'transagreementdefname': 'Lease Agreement',
                           'transddpayment': '1',
                           'transnetpaymentinterest': (new_term - i) * Decimal(multiplier2),
                           'transnetpaymentcapital': Decimal(re.sub(',', '', rescheduled_instalment_net)) - (
                                       new_term - i) * Decimal(multiplier2),
                           }
        if agreement_detail.agreementdefname == 'Hire Purchase':
            ats_rentals_rec['transagreementdefname'] = 'Hire Purchase'
            ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', rescheduled_instalment_net))


        go_account_transaction_summary(**ats_rentals_rec).save()

        atd_rentals_rec = {'go_id': go_id,
                           'agreementnumber': agreement_id,
                           'transactiondate': rescheduled_date + relativedelta(months=+i),
                           'transactionsourceid': 'GO1',
                           'transflag': 'Pay',
                           'transfallendue': '0',
                           'transnetpayment': Decimal(re.sub(',', '', rescheduled_instalment_net)),
                           'transgrosspayment': (round(Decimal(re.sub(',', '', rescheduled_instalment_net)) * Decimal(config.other_sales_tax), 2)),
                           'transvatpayment': (round(Decimal(re.sub(',', '', rescheduled_instalment_net)) * Decimal(config.sales_tax), 2)),
                           }
        if agreement_detail.agreementdefname == 'Hire Purchase':
            atd_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', rescheduled_instalment_net))
            atd_rentals_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
        go_account_transaction_detail(**atd_rentals_rec).save()

    # for i in range(3):
    #     ats_secondary_rec = {'go_id': go_id,
    #                          'agreementnumber': agreement_id,
    #                          'transtypeid': '0',
    #                          'transactiondate': rescheduled_date + relativedelta(months=+(i+new_term)),
    #                          'transactionsourceid': 'GO3',
    #                          'transtypedesc': '',
    #                          'transflag': '',
    #                          'transfallendue': '0',
    #                          'transnetpayment': Decimal(re.sub(',', '', rescheduled_instalment_net)),
    #                          'transgrosspayment': Decimal(re.sub(',', '', rescheduled_instalment_net))*Decimal(config.other_sales_tax),
    #                          'transactionsourcedesc': 'Secondary',
    #                          'transagreementagreementdate': agreement_detail.agreementagreementdate,
    #                          'transagreementauthority': agreement_detail.agreementauthority,
    #                          'transagreementclosedflag_id': '901',
    #                          'transactionstatus': '901',
    #                          'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
    #                          'transcustomercompany': agreement_detail.customercompany,
    #                          'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
    #                          'transagreementdefname': 'Lease Agreement',
    #                          'transddpayment': '1',
    #                          'transnetpaymentcapital' : Decimal(re.sub(',', '', '0.00')),
    #                          'transnetpaymentinterest' : Decimal(re.sub(',', '', '0.00')),
    #                          }
    #
    #     go_account_transaction_summary(**ats_secondary_rec).save()
    #     atd_secondary_rentals_rec = {'go_id': go_id,
    #                                  'agreementnumber': agreement_id,
    #                                  'transactiondate': rescheduled_date + relativedelta(months=+(i+new_term)),
    #                                  'transactionsourceid': 'GO3',
    #                                  'transflag': 'Sec',
    #                                  'transfallendue': '0',
    #                                  'transnetpayment': Decimal(re.sub(',', '', rescheduled_instalment_net)),
    #                                  }
    #
    #     go_account_transaction_detail(**atd_secondary_rentals_rec).save()


def change_single_value_function(request,agreement_id):
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany

    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate

    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:

        history_change_changed_value = {'go_id': go_id,
                                     'agreement_id': agreement_id,
                                     'user': request.user,
                                     'updated': datetime.now(),
                                     'action': 'Changed Single Value',
                                     'transaction': format(transaction_date,'%d/%m/%Y'),
                                     'customercompany': customer
                               }
        go_editor_history(**history_change_changed_value).save()

        if request.POST.get('changed_rental'):changed_rental= decimal.Decimal(request.POST.get('changed_rental'))
        else: changed_rental = Decimal(re.sub(',', '', '0.00'))

        if request.POST.get('changed_risk_fee'): changed_risk_fee = decimal.Decimal(request.POST.get('changed_risk_fee'))
        else: changed_risk_fee = Decimal(re.sub(',', '','0.00'))

        if request.POST.get('changed_bamf_fee'): changed_bamf_fee = decimal.Decimal(request.POST.get('changed_bamf_fee'))
        else: changed_bamf_fee = Decimal(re.sub(',', '','0.00'))

        if request.POST.get('changed_doc_fee'): changed_doc_fee = decimal.Decimal(request.POST.get('changed_doc_fee'))
        else: changed_doc_fee = Decimal(re.sub(',', '','0.00'))

        if request.POST.get('changed_doc_fee2'): changed_doc_fee2 = decimal.Decimal(request.POST.get('changed_doc_fee2'))
        else: changed_doc_fee2 = Decimal(re.sub(',', '','0.00'))



        changed_transaction = changed_rental + changed_risk_fee + changed_bamf_fee + changed_doc_fee + changed_doc_fee2
        changed_transaction_vat = changed_transaction * decimal.Decimal(config.other_sales_tax)

        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      ,transactiondate = transaction_date
                                                      ).update(transnetpayment=changed_transaction)

        go_account_transaction_summary.objects.filter(go_id=go_id
                                                      , transactiondate=transaction_date
                                                      ).update(transgrosspayment=changed_transaction_vat)
        if agreement_detail.agreementdefname == 'Hire Purchase':
            go_account_transaction_summary.objects.filter(go_id=go_id
                                                          , transactiondate=transaction_date
                                                          ).update(transgrosspayment=changed_transaction)


        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate=transaction_date,
                                                     transtypedesc__isnull=True
                                                     ).update(transnetpayment=changed_rental)

        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate=transaction_date,
                                                     transtypedesc ='Risk Fee'
                                                     ).update(transnetpayment=changed_risk_fee)

        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate=transaction_date,
                                                     transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee']
                                                     ).update(transnetpayment=changed_bamf_fee)

        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate=transaction_date,
                                                     transtypedesc='Documentation Fee'
                                                     ).update(transnetpayment=changed_doc_fee)

        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate=transaction_date,
                                                     transtypedesc='Documentation Fee 2'
                                                     ).update(transnetpayment=changed_doc_fee2)
    go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')

    return batch_error


def change_future_values_function(request,agreement_id):
    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    config = client_configuration.objects.get(client_id='NWCF')
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    customer = agreement_detail.customercompany
    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    transaction_date = transaction_summary_extract.transactiondate
    batch_error = False
    if transaction_summary_extract.transactionbatch_id:
        batch_error = transaction_summary_extract.transactionbatch_id
    else:

        history_change_changed_values = {'go_id': go_id,
                                        'agreement_id': agreement_id,
                                        'user': request.user,
                                        'updated': datetime.now(),
                                        'action': 'Changed Future Value',
                                        'transaction': 'All dates after '+ format(transaction_date,'%d/%m/%Y'),
                                        'customercompany': customer
                               }
        go_editor_history(**history_change_changed_values).save()


        changed_rental = decimal.Decimal(request.POST.get('changed_rental'))
        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate__gte=transaction_date,
                                                     transtypedesc__isnull=True
                                                     ).update(transnetpayment=changed_rental)
        if request.POST.get('changed_risk_fee'):
            changed_risk_fee = decimal.Decimal(request.POST.get('changed_risk_fee'))
            all_future_dates_change_detail_rf = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                             transactiondate__gte=transaction_date,
                                                                                             transtypedesc='Risk Fee'
                                                                                             ).update(transnetpayment=changed_risk_fee)
        else:
            changed_risk_fee = Decimal(re.sub(',', '', '0.00'))

        all_future_dates_change_detail_bamf = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                           transactiondate__gte=transaction_date,
                                                                                           transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee']
                                                                                           ).last()
        all_future_dates_change_summary = go_account_transaction_summary.objects.filter(go_id=go_id,
                                                                                        transactiondate__gte=transaction_date)
        if all_future_dates_change_detail_bamf:
            old_bamf = decimal.Decimal(all_future_dates_change_detail_bamf.transnetpayment)

        if request.POST.get('changed_bamf_fee'):
            changed_bamf_fee = decimal.Decimal(request.POST.get('changed_bamf_fee'))
            all_future_dates_change_detail_bamf = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                               transactiondate__gte=transaction_date,
                                                                                               transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee']
                                                                                               ).update(transnetpayment=changed_bamf_fee)
        else:
            changed_bamf_fee = Decimal(re.sub(',', '', '0.00'))
        go_agreement_index.objects.filter(go_id=go_id).update(agreement_origin_flag='GO')
        changed_transaction_with_bamf = changed_rental + changed_risk_fee + changed_bamf_fee
        changed_transaction_without_bamf = changed_rental + changed_risk_fee
        if all_future_dates_change_detail_bamf:
            changed_old_bamf_fee = changed_rental + old_bamf

        changed_transaction_without_bamf_gross = changed_transaction_without_bamf * decimal.Decimal(config.other_sales_tax)

        go_account_transaction_detail.objects.filter(go_id=go_id,
                                                     transactiondate__gte=transaction_date,
                                                     transtypedesc__isnull=True
                                                     ).update(transnetpayment=changed_rental)

        go_account_transaction_summary.objects.filter(go_id=go_id,
                                                      transactiondate__gte=transaction_date
                                                      ).update(transnetpayment=changed_transaction_without_bamf)

        go_account_transaction_summary.objects.filter(go_id=go_id,
                                                      transactiondate__gte=transaction_date
                                                      ).update(transgrosspayment=changed_transaction_without_bamf_gross)

        if agreement_detail.agreementdefname == 'Hire Purchase':
            go_account_transaction_summary.objects.filter(go_id=go_id
                                                          , transactiondate=transaction_date
                                                          ).update(transgrosspayment=changed_transaction_without_bamf_gross)


        all_future_dates_change_summary = go_account_transaction_summary.objects.filter(go_id=go_id,
                                                                                        transactiondate__gte=transaction_date)
        all_future_dates_change_detail_bamf = go_account_transaction_detail.objects.filter(go_id=go_id,
                                                                                           transactiondate__gte=transaction_date,
                                                                                           transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'])

        if request.POST.get('changed_bamf_fee'):
            for row in all_future_dates_change_detail_bamf:
                wip_get_date = row.transactiondate
                for row2 in all_future_dates_change_summary:
                    if row2.transactiondate == wip_get_date:
                        if agreement_detail.agreementdefname == 'Lease Agreement':
                            row2.transgrosspayment = round(changed_transaction_with_bamf * decimal.Decimal(config.other_sales_tax), 2)
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            row2.transgrosspayment = changed_transaction_with_bamf
                        row2.transnetpayment = changed_transaction_with_bamf
                        row2.save()

        else:
            for row in all_future_dates_change_detail_bamf:
                wip_get_date = row.transactiondate
                for row2 in all_future_dates_change_summary:
                    if row2.transactiondate == wip_get_date:
                        if agreement_detail.agreementdefname == 'Lease Agreement':
                            row2.transgrosspayment = round(changed_old_bamf_fee * decimal.Decimal(config.other_sales_tax), 2)
                        if agreement_detail.agreementdefname == 'Hire Purchase':
                            row2.transgrosspayment = changed_old_bamf_fee
                        row2.transnetpayment = changed_old_bamf_fee
                        row2.save()
    return batch_error


def recalculate_function(agreement_id):

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    riskfee = str(go_id.agreement_risk_fee)
    bamffee = str(go_id.agreement_bamf_fee)
    docfee = str(go_id.agreement_doc_fee)
    principal = str(agreement_detail.agreementoriginalprincipal)
    instalmentnet = str(agreement_detail.agreementinstalmentnet)
    go_account_transaction_summary.objects.filter(go_id=go_id, transactionsourceid='GO1').delete()
    go_account_transaction_summary.objects.filter(go_id=go_id, transactionsourceid='GO3').delete()
    go_account_transaction_detail.objects.filter(go_id=go_id, transactionsourceid='GO1').delete()
    go_account_transaction_detail.objects.filter(go_id=go_id, transactionsourceid='GO3').delete()
    config = client_configuration.objects.get(client_id='NWCF')

    if Decimal(agreement_detail.agreement_stage) >= 3:
    # Risk Fee
        instalmentnet2 = (agreement_detail.agreementinstalmentnet)

        if agreement_detail.agreementinstalmentnet < 500:
            risk_fee = '0'
        if instalmentnet2 >= 500:
            risk_fee = '100'
        if instalmentnet2 > 2000:
            risk_fee = '200'
        if instalmentnet2 > 3000:
            risk_fee = '300'
        # if go_id.prof#ile_id in (3, 4):
        #     risk_fee = '0'
        if go_id.risk_flag == 0:
            risk_fee = '0'
        # risk_fee = '100'
        riskfeecorrection = go_agreement_index.objects.get(agreement_id=agreement_id)
        riskfeecorrection.agreement_risk_fee = Decimal(risk_fee)
        riskfeecorrection.save();
    # TODO: GO#110 - Start

    #     if agreement_detail.agreementdefname == 'Hire Purchase':
    #         risk_fee = str(Decimal(risk_fee))
    #     else :
        risk_fee = str(Decimal(risk_fee) / Decimal(config.other_sales_tax))
    # TODO: GO#110 - End
        riskfee = risk_fee

        print(riskfee)

        # go_agreement_querydetail.objects.filter(go_id=go_id).update(agreement_stage=stage)
        docfee_rec = {'go_id': go_id,
                      'agreementnumber': go_id,
                      'transtypeid' : '1',
                      'transactiondate': agreement_detail.agreementupfrontdate,
                      'transactionsourceid' : 'GO1',
                      'transtypedesc' : 'Documentation Fee',
                      'transflag' : 'Fee',
                      'transfallendue' : '1',
                      'transnetpayment': docfee,
                      'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                      'transpayprointerest': Decimal(re.sub(',', '', docfee)),
                      'transgrosspayment': round(Decimal(re.sub(',', '', docfee)) * Decimal(config.other_sales_tax), 2),
                      'transvatpayment': round(Decimal(re.sub(',', '', docfee)) * Decimal(config.sales_tax), 2),
                      }
    # TODO: GO#110 - Start
    # if agreement_detail.agreementdefname == 'Hire Purchase':
    #     docfee_rec['transgrosspayment'] = Decimal(re.sub(',', '', docfee))
    #     docfee_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
    # TODO: GO#110 - End
        ats_docfee_rec = {'go_id': go_id,
                          'agreementnumber': go_id,
                          'transtypeid': '0',
                          'transactiondate': agreement_detail.agreementupfrontdate,
                          'transactionsourceid': 'GO1',
                          'transtypedesc': '',
                          'transflag': '',
                          'transfallendue': '1',
                          'transnetpayment': Decimal(re.sub(',', '', docfee)),
                          'transgrosspayment': round(Decimal(re.sub(',', '', docfee))*Decimal(config.other_sales_tax),2),
                          'transactionsourcedesc' : 'Primary',
                          'transagreementagreementdate' : agreement_detail.agreementagreementdate,
                          'transagreementauthority' : agreement_detail.agreementauthority,
                          'transagreementclosedflag_id' : '901',
                          'transactionstatus': '901',
                          'transagreementcustomernumber' : agreement_detail.agreementcustomernumber,
                          'transagreementddstatus_id' : agreement_detail.agreementddstatus_id,
                          'transagreementdefname' : 'Lease Agreement',
                          'transcustomercompany': agreement_detail.customercompany,
                          'transddpayment' : '0' ,
                          # 'transgrosspayment':,
                          'transnetpaymentcapital': Decimal(re.sub(',', '', '0.00')),
                          'transnetpaymentinterest': Decimal(re.sub(',', '', docfee)),
                          }
    # TODO: GO#110 - Start
    # if agreement_detail.agreementdefname == 'Hire Purchase':
    #     ats_docfee_rec['transagreementdefname'] = 'Hire Purchase'
    #     ats_docfee_rec['transgrosspayment'] = Decimal(re.sub(',', '', docfee))
    # TODO: GO#110 - End

        go_account_transaction_detail(**docfee_rec).save()
        go_account_transaction_summary(**ats_docfee_rec).save()

        if go_id.broker_id == 2:

            docfee2_rec = {'go_id': go_id,
                           'agreementnumber': go_id,
                           'transtypeid': '4',
                           'transactiondate': agreement_detail.agreementupfrontdate + timedelta(seconds=1),
                           'transactionsourceid': 'GO1',
                           'transtypedesc': 'Documentation Fee 2',
                           'transflag': 'Fee',
                           'transfallendue': '1',
                           'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                           'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                           'transpayprointerest': Decimal(re.sub(',', '', instalmentnet)),
                           'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                           'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                           }
            if agreement_detail.agreementdefname == 'Hire Purchase':
                docfee2_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                docfee2_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))


            ats_docfee2_rec = {'go_id': go_id,
                               'agreementnumber': go_id,
                               'transtypeid': '0',
                               'transactiondate': agreement_detail.agreementupfrontdate + timedelta(seconds=1),
                               'transactionsourceid': 'GO1',
                               'transtypedesc': '',
                               'transflag': '',
                               'transfallendue': '0',
                               'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                               'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet))*Decimal(config.other_sales_tax), 2),
                               'transactionsourcedesc': 'Primary',
                               'transagreementagreementdate': agreement_detail.agreementagreementdate,
                               'transagreementauthority': agreement_detail.agreementauthority,
                               'transagreementclosedflag_id': '901',
                               'transactionstatus': '901',
                               'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                               'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                               'transagreementdefname': 'Lease Agreement',
                               'transcustomercompany': agreement_detail.customercompany,
                               'transddpayment': '0',
                               # 'transgrosspayment':,
                               'transnetpaymentcapital': Decimal(re.sub(',', '', '0.00')),
                               'transnetpaymentinterest': Decimal(re.sub(',', '', instalmentnet)),
                               }
            if agreement_detail.agreementdefname == 'Hire Purchase':
                ats_docfee2_rec['transagreementdefname'] = 'Hire Purchase'
                ats_docfee2_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))

            go_account_transaction_detail(**docfee2_rec).save()
            go_account_transaction_summary(**ats_docfee2_rec).save()

        Interest = go_id.term* Decimal(re.sub(',', '', instalmentnet)) -  Decimal(re.sub(',', '', principal))
        multiplier=(go_id.term)*(go_id.term+1)/2
        multiplier2= Decimal(Interest)/Decimal(multiplier)

        for i in range(go_id.term):
            ats_rentals_rec = {'go_id': go_id,
                               'agreementnumber': agreement_id,
                               'transtypeid': '0',
                               'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                               'transactionsourceid': 'GO1',
                               'transtypedesc': '',
                               'transflag': '',
                               'transfallendue': '0',
                               'transnetpayment': Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(riskfee))),
                               'transgrosspayment': round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', str(riskfee))))*Decimal(config.other_sales_tax), 2),
                               'transactionsourcedesc' : 'Primary',
                               'transagreementagreementdate': agreement_detail.agreementagreementdate,
                               'transagreementauthority': agreement_detail.agreementauthority,
                               'transagreementclosedflag_id': '901',
                               'transactionstatus': '901',
                               'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                               'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                               'transagreementdefname': 'Lease Agreement',
                               'transcustomercompany': agreement_detail.customercompany,
                               'transddpayment': '1',
                               # 'transgrosspayment':,
                               'transnetpaymentinterest': (go_id.term - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(riskfee))),
                               'transnetpaymentcapital': Decimal(re.sub(',', '', instalmentnet))-(go_id.term - i) * Decimal(multiplier2),
                               }
            # TODO: GO#110 - Start
            if agreement_detail.agreementdefname == 'Hire Purchase':
                ats_rentals_rec['transagreementdefname'] = 'Hire Purchase'
                ats_rentals_rec['transgrosspayment'] = round(
                    Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) * Decimal(
                        config.other_sales_tax), 2)
            # TODO: GO#110 - End

            if go_id.broker_id == 1:
                if i > 0 and (i + 1) % 6 == 0 and go_id.bamf_flag == 1 and go_id.risk_flag == 1:
                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transnetpaymentinterest'] = (go_id.term - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(riskfee)))+ Decimal(
                        re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', riskfee))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                    # TODO: GO#110 - Start
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + (
                                Decimal(re.sub(',', '', riskfee)) + Decimal(
                            re.sub(',', '', str(config.bamf_fee_amount_net)))) * Decimal(config.other_sales_tax), 2)
                # TODO: GO#110 - End
            else:
                if i > 0 and (i + 1) % 12 == 0:
                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', riskfee)) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transnetpaymentinterest'] = (go_id.term - i) * Decimal(multiplier2) + Decimal(
                        re.sub(',', '', str(riskfee))) + Decimal(
                        re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', riskfee))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                    # TODO: GO#110 - Start
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + (
                                Decimal(re.sub(',', '', riskfee)) + Decimal(
                            re.sub(',', '', str(config.bamf_fee_amount_net)))) * Decimal(config.other_sales_tax), 2)
                    # TODO: GO#110 - End
            if go_id.bamf_flag == 0 and go_id.risk_flag == 1:
                ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                    re.sub(',', '', riskfee))
                ats_rentals_rec['transnetpaymentinterest'] = (go_id.term - i) * Decimal(multiplier2) + Decimal(
                    re.sub(',', '', str(riskfee)))

                ats_rentals_rec['transgrosspayment'] = round((Decimal(re.sub(',', '', instalmentnet)) * Decimal(
                    config.other_sales_tax) + Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax)), 2)
                if agreement_detail.agreementdefname == 'Hire Purchase':
                    ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', riskfee))

            if go_id.broker_id == 1:
                if i > 0 and (i + 1) % 6 == 0 and go_id.bamf_flag == 1 and go_id.risk_flag == 0:
                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transnetpaymentinterest'] = round((go_id.term - i) * Decimal(multiplier2) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                    ats_rentals_rec['transgrosspayment'] = round(
                        (Decimal(re.sub(',', '', instalmentnet))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                            re.sub(',', '', str(config.bamf_fee_amount_net)))
            else:
                if i > 0 and (i + 1) % 12 == 0 :
                    ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                        re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transnetpaymentinterest'] = (go_id.term - i) * Decimal(multiplier2) + Decimal(
                        re.sub(',', '', str(config.bamf_fee_amount_net)))
                    ats_rentals_rec['transgrosspayment'] = round(
                        (Decimal(re.sub(',', '', instalmentnet))) * Decimal(config.other_sales_tax) + Decimal(re.sub(',', '', str(config.bamf_fee_amount_vat))), 2)
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        # TODO: GO#110 - Start
                        ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                            re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2)
                        # TODO: GO#110 - End

            if go_id.bamf_flag == 0 and go_id.risk_flag == 0 and go_id.broker_id == 1:
                ats_rentals_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet))
                ats_rentals_rec['transnetpaymentinterest'] = (go_id.term - i) * Decimal(multiplier2)
                ats_rentals_rec['transgrosspayment'] = round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2)
                if agreement_detail.agreementdefname == 'Hire Purchase':
                    ats_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))

            go_account_transaction_summary(**ats_rentals_rec).save()

            atd_rentals_rec = {'go_id': go_id,
                               'agreementnumber': agreement_id,
                               # 'transtypeid': '1',
                               'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                               'transactionsourceid': 'GO1',
                               'transflag': 'Pay',
                               'transfallendue': '0',
                               'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                               'transpayproprincipal': Decimal(re.sub(',', '', instalmentnet)) - (go_id.term - i) * Decimal(multiplier2),
                               'transpayprointerest': (go_id.term - i) * Decimal(multiplier2),
                               'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                               'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                               }
            if agreement_detail.agreementdefname == 'Hire Purchase':
                atd_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                atd_rentals_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
            if go_id.broker_id == 1:
                go_account_transaction_detail(**atd_rentals_rec).save()

            atd_risk_rec = {'go_id': go_id,
                            'agreementnumber': agreement_id,
                            'transtypeid': '3',
                            'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                            'transactionsourceid': 'GO1',
                            'transtypedesc': 'Risk Fee',
                            'transflag': 'Fee',
                            'transfallendue': '0',
                            'transnetpayment': Decimal(re.sub(',', '', riskfee)),
                            'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                            'transpayprointerest': Decimal(re.sub(',', '', riskfee)),
                            'transgrosspayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2),
                            'transvatpayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.sales_tax), 2),
                            }
            # TODO: GO#110 - Start
            # if agreement_detail.agreementdefname == 'Hire Purchase':
            #     atd_risk_rec['transgrosspayment'] = Decimal(re.sub(',', '', riskfee))
            #     atd_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
            # TODO: GO#110 - End
            if go_id.risk_flag == 1:
                if go_id.broker_id == 1:
                    go_account_transaction_detail(**atd_risk_rec).save()

        for i in range(go_id.term):
            if go_id.bamf_flag == 1:
                if i > 0 and (i+1) % 6 == 0:
                    atd_BAMF_rec = {'go_id': go_id,
                                    'agreementnumber': agreement_id,
                                    'transtypeid': '5',
                                    'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                    'transactionsourceid': 'GO1',
                                    'transtypedesc': 'Bi-Annual Management Fee',
                                    'transflag': 'Fee',
                                    'transfallendue': '0',
                                    'transnetpayment' : str(config.bamf_fee_amount_net),
                                    'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                    'transpayprointerest': str(config.bamf_fee_amount_net),
                                    'transgrosspayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2),
                                    'transvatpayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.sales_tax), 2),
                                    }
                    # TODO: GO#110 - Start
                    # if agreement_detail.agreementdefname == 'Hire Purchase':
                    #     atd_BAMF_rec['transgrosspayment'] = Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                    #     atd_BAMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))
                    # TODO: GO#110 - End
                    if go_id.bamf_flag == 1:
                        go_account_transaction_detail(**atd_BAMF_rec).save()
            if go_id.amf_flag == 1:
                if i > 0 and (i+1) % 12 == 0:
                    atd_BAMF_rec = {'go_id': go_id,
                                    'agreementnumber': agreement_id,
                                    'transtypeid': '2',
                                    'transactiondate': agreement_detail.agreementfirstpaymentdate + relativedelta(months=+i),
                                    'transactionsourceid': 'GO1',
                                    'transtypedesc': 'Annual Management Fee',
                                    'transflag': 'Fee',
                                    'transfallendue': '0',
                                    'transnetpayment' : str(config.bamf_fee_amount_net),
                                    'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                    'transpayprointerest': str(config.bamf_fee_amount_net),
                                    'transgrosspayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.other_sales_tax), 2),
                                    'transvatpayment': round(Decimal(re.sub(',', '', str(config.bamf_fee_amount_net))) * Decimal(config.sales_tax), 2),
                                    }
                    if agreement_detail.agreementdefname == 'Hire Purchase':
                        atd_BAMF_rec['transgrosspayment'] = Decimal(re.sub(',', '', str(config.bamf_fee_amount_net)))
                        atd_BAMF_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                    go_account_transaction_detail(**atd_BAMF_rec).save()

        for i in range(3):
            ats_secondary_rec = {'go_id': go_id,
                                 'agreementnumber': agreement_id,
                                 'transtypeid': '0',
                                 'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                 'transactionsourceid': 'GO3',
                                 'transtypedesc': '',
                                 'transflag': '',
                                 'transfallendue': '0',
                                 'transnetpayment': Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)),
                                 'transgrosspayment': round((Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)))*Decimal(config.other_sales_tax), 2),
                                 'transactionsourcedesc': 'Secondary',
                                 'transagreementagreementdate': agreement_detail.agreementagreementdate,
                                 'transagreementauthority': agreement_detail.agreementauthority,
                                 'transagreementclosedflag_id': '901',
                                 'transactionstatus': '901',
                                 'transagreementcustomernumber': agreement_detail.agreementcustomernumber,
                                 'transagreementddstatus_id': agreement_detail.agreementddstatus_id,
                                 'transagreementdefname': 'Lease Agreement',
                                 'transcustomercompany': agreement_detail.customercompany,
                                 'transddpayment': '1',
                                 # 'transgrosspayment':,
                                 'transnetpaymentcapital' : Decimal(re.sub(',', '', '0.00')),
                                 'transnetpaymentinterest' : Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)),
                                 }
                # TODO: GO#110 - Start
            if agreement_detail.agreement_stage == 4:
                go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                              transactionstatus='905').update(
                    transactionstatus='901')

            if go_id.secondary_flag == 1:
                ats_secondary_rec['transnetpayment'] = Decimal(re.sub(',', '', instalmentnet)) + Decimal(
                    re.sub(',', '', riskfee))

                if agreement_detail.agreementdefname == 'Hire Purchase':
                    ats_secondary_rec['transagreementdefname'] = 'Hire Purchase'
                    ats_secondary_rec['transgrosspayment'] = round(
                        Decimal(re.sub(',', '', instalmentnet)) + Decimal(re.sub(',', '', riskfee)) * Decimal(
                            config.other_sales_tax), 2)
                # TODO: GO#110 - End

                go_account_transaction_summary(**ats_secondary_rec).save()
                atd_secondary_rentals_rec = {'go_id': go_id,
                                             'agreementnumber': agreement_id,
                                             # 'transtypeid': '0',
                                             'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                             'transactionsourceid': 'GO3',
                                             # 'transtypedesc': 'Documentation Fee',
                                             'transflag': 'Sec',
                                             'transfallendue': '0',
                                             'transnetpayment': Decimal(re.sub(',', '', instalmentnet)),
                                             'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                             'transpayprointerest': Decimal(re.sub(',', '', instalmentnet)),
                                             'transgrosspayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.other_sales_tax), 2),
                                             'transvatpayment': round(Decimal(re.sub(',', '', instalmentnet)) * Decimal(config.sales_tax), 2),
                                             }
                if agreement_detail.agreementdefname == 'Hire Purchase':
                    atd_secondary_rentals_rec['transgrosspayment'] = Decimal(re.sub(',', '', instalmentnet))
                    atd_secondary_rentals_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                go_account_transaction_detail(**atd_secondary_rentals_rec).save()

                atd_secondary_risk_rec = {'go_id': go_id,
                                          'agreementnumber': agreement_id,
                                          'transtypeid': '3',
                                          'transactiondate': agreement_detail.agreementresidualdate + relativedelta(months=+(i+1)),
                                          'transactionsourceid': 'GO3',
                                          'transtypedesc': 'Risk Fee',
                                          'transflag': 'SFn',
                                          'transfallendue': '0',
                                          'transnetpayment': Decimal(re.sub(',', '', riskfee)),
                                          'transpayproprincipal': Decimal(re.sub(',', '', '0.00')),
                                          'transpayprointerest': Decimal(re.sub(',', '', riskfee)),
                                          'transgrosspayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.other_sales_tax), 2),
                                          'transvatpayment': round(Decimal(re.sub(',', '', riskfee)) * Decimal(config.sales_tax), 2),
                                          }
                # TODO: GO#110 - Start
                # if agreement_detail.agreementdefname == 'Hire Purchase':
                #     atd_secondary_risk_rec['transgrosspayment'] = Decimal(re.sub(',', '', riskfee))
                #     atd_secondary_risk_rec['transvatpayment'] = Decimal(re.sub(',', '', '0.00'))

                if go_id.risk_flag == 1:
                    go_account_transaction_detail(**atd_secondary_risk_rec).save()
            # if go_id.broker_id == 2:
            #     go_account_transaction_detail(**atd_secondary_rentals_rec).save()
            # TODO: GO#110 - End

        #Charges
        chargecorrection = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
        chargecorrection.agreementcharges = Decimal(Interest)
        chargecorrection.save()


        #Risk Fee
        instalmentnet2=(agreement_detail.agreementinstalmentnet)

        if agreement_detail.agreementinstalmentnet < 500:
            risk_fee = '0'
        if instalmentnet2 > 500:
            risk_fee = '100'
        if instalmentnet2 > 2000:
            risk_fee = '200'
        if instalmentnet2 > 3000:
            risk_fee = '300'
        if go_id.risk_flag == 1:
            risk_fee = '0'
        if go_id.broker_id == 2:
            risk_fee = '0'
        # risk_fee = '100'

        if agreement_detail.agreementagreementtypeid.agreementdefid == 1:
            risk_fee = Decimal(risk_fee) / Decimal(config.other_sales_tax)

        riskfeecorrection = go_agreement_index.objects.get(agreement_id=agreement_id)
        riskfeecorrection.agreement_risk_fee=Decimal(risk_fee)
        riskfeecorrection.save()

        if go_id.bamf_flag == 0: Bamf = 0
        if go_id.bamf_flag == 1:  Bamf = config.bamf_fee_amount_net
        if go_id.broker_id == 1:
            a = (math.floor(go_id.term / 6))
        else:
            a = (math.floor(go_id.term / 12))
        b = Bamf * a
        c = go_id.term * round(go_id.agreement_risk_fee, 2)

        d = go_id.agreement_doc_fee
        totalFees = b + c + d


        totalfeescorrection = go_agreement_index.objects.get(agreement_id=agreement_id)
        totalfeescorrection.agreement_total_fees = Decimal(totalFees)
        totalfeescorrection.save()

        # PayableNet
        PayableNet = agreement_detail.agreementoriginalprincipal + Interest + totalFees
        # go_id.agreement_net

        payablenetcorrection = go_agreement_index.objects.get(agreement_id=agreement_id)
        payablenetcorrection.agreement_payable_net = Decimal(PayableNet)
        payablenetcorrection.save()

        #PayableGross
        # e=config.other_sales_tax
        PayableGross = PayableNet * Decimal(config.other_sales_tax)
        if agreement_detail.agreementdefname == 'Hire Purchase':
            PayableGross = PayableNet

        payablegrosscorrection = go_agreement_index.objects.get(agreement_id=agreement_id)

        payablegrosscorrection.agreement_payable_gross = Decimal(PayableGross)
        payablegrosscorrection.save()