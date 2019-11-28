from core_direct_debits.models import DDHistory
from core_agreement_crud.models import go_agreement_querydetail, \
                                        go_account_transaction_detail, go_account_transaction_summary, \
                                        go_agreement_index

import re, datetime, decimal

def app_get_agreement_id(parm_search_reference):

    dd_history = DDHistory.objects.filter(reference=parm_search_reference).first()
    try:
        return_agreement_id = dd_history.agreement_no
    except:
        return_agreement_id = 'NOT_FOUND'

    return return_agreement_id


def write_account_history(in_agreement, in_schedule_date, in_source_id, in_transtype, in_transflag, in_value,
                                            in_gross_net_flag, in_payprointerest, in_payproprincipal,
                                                in_trans_date, in_description):

    # Validate incoming dates
    valid_date_format = '%Y-%m-%d'
    val_today = datetime.datetime.today()

    try:
        date_obj = datetime.datetime.strftime(in_schedule_date, valid_date_format)
    except:
        in_schedule_date = None

    try:
        date_obj = datetime.datetime.strftime(in_trans_date, valid_date_format)
    except:
        in_trans_date = None

    # Get Agreement Object and condition further processing
    agreement_extract = None
    if in_agreement:
        try:
            agreement_extract = go_agreement_querydetail.objects.get(agreementnumber=in_agreement)
        except:
            pass

    if agreement_extract:
        agreement_origin_extract = go_agreement_index.objects.filter(agreement_id=in_agreement).first()
        if agreement_origin_extract:
            agreement_origin = agreement_origin_extract.agreement_origin_flag
        else:
            agreement_origin = None
    else:
        agreement_origin = None

    # agreement_origin = True
    # Only do anything further if Agreement object has been retrieved.
    # if agreement_extract and agreement_origin:
    if agreement_extract:

        # Populate Transaction Detail Values
        wip_go_id = agreement_extract.go_id
        wip_agreementnumber = agreement_extract.agreementnumber

        if not isinstance(in_schedule_date, datetime.datetime):
            my_time = datetime.datetime.min.time()
            in_schedule_date = datetime.datetime.combine(in_schedule_date, my_time)

        if in_trans_date and not isinstance(in_trans_date, datetime.datetime):
            my_time = datetime.datetime.min.time()
            in_trans_date = datetime.datetime.combine(in_trans_date, my_time)

        if in_trans_date:
            wip_transactiondate = in_trans_date
        else:
            if in_schedule_date:
                wip_transactiondate = in_schedule_date
            else:
                wip_transactiondate = val_today

        wip_transactiondate = wip_transactiondate + datetime.timedelta(hours=23)
        # wip_transactionsourceid = in_source_id
        wip_transactionsourceid = 'GO5'
        wip_transtypeid = in_transtype
        wip_transtypedesc = in_description
        wip_transflag = in_transflag

        if in_schedule_date:
            if in_schedule_date <= val_today:
                wip_transfallendue = 1
            else:
                wip_transfallendue = 0
        else:
            wip_transfallendue = 0

        wip_value = round(decimal.Decimal(float(in_value)),2)
        if agreement_extract.agreementdefname == 'Hire Purchase':
            wip_transgrosspayment = wip_value
            wip_transvatpayment = 0
            wip_transnetpayment = 0
        else:
            if in_gross_net_flag == 'GROSS':
                wip_transgrosspayment = wip_value
                wip_transnetpayment = round((wip_transgrosspayment/decimal.Decimal(1.2)),2)
                wip_transvatpayment = round((wip_transgrosspayment-wip_transnetpayment ), 2)
            else:
                wip_transnetpayment = wip_value
                wip_transvatpayment = round((wip_transnetpayment * decimal.Decimal(0.2)),2)
                wip_transgrosspayment = wip_transvatpayment + wip_transnetpayment

        wip_transpayproid = None
        wip_transpayproprincipal = round(in_payproprincipal,2)
        wip_transpayprointerest = round(in_payprointerest,2)

        # Write Transaction Detail record
        new_transaction_detail = go_account_transaction_detail(
                                        go_id = wip_go_id,
                                        agreementnumber = wip_agreementnumber,
                                        transactiondate = wip_transactiondate,
                                        transactionsourceid = wip_transactionsourceid,
                                        transtypeid = wip_transtypeid,
                                        transtypedesc = wip_transtypedesc,
                                        transflag = wip_transflag,
                                        transfallendue = wip_transfallendue,
                                        transnetpayment = wip_transnetpayment,
                                        transvatpayment = wip_transvatpayment,
                                        transgrosspayment = wip_transgrosspayment,
                                        transpayproid = wip_transpayproid,
                                        transpayproprincipal = wip_transpayproprincipal,
                                        transpayprointerest = wip_transpayprointerest)
        new_transaction_detail.save()

        # Populate Transaction Summary Values
        wip_transrunningtotal = None
        wip_transagreementcustomernumber = agreement_extract.agreementcustomernumber
        wip_transcustomercompany = agreement_extract.customercompany
        wip_transagreementclosedflag = agreement_extract.agreementclosedflag
        wip_transagreementddstatus = agreement_extract.agreementddstatus
        wip_transagreementcloseddate = agreement_extract.closeddate
        wip_transagreementdefname = agreement_extract.agreementdefname
        wip_transagreementagreementdate = agreement_extract.agreementagreementdate
        wip_transddpayment = 1
        wip_transagreementauthority = agreement_extract.agreementauthority
        wip_transnetpaymentinterest = wip_transpayprointerest
        wip_transnetpaymentcapital = wip_transpayproprincipal
        wip_transactionbatch_id = None
        wip_transactionstatus = ' '

        # Write Transaction Summary record
        new_transaction_summary = go_account_transaction_summary(
                                        go_id = wip_go_id,
                                        agreementnumber = wip_agreementnumber,
                                        transactiondate = wip_transactiondate,
                                        transactionsourceid = wip_transactionsourceid,
                                        transactionsourcedesc = 'HISTORY',
                                        transtypeid = wip_transtypeid,
                                        transtypedesc = wip_transtypedesc,
                                        transflag = wip_transflag,
                                        transfallendue = wip_transfallendue,
                                        transnetpayment = wip_transnetpayment,
                                        transgrosspayment = wip_transgrosspayment,
                                        transrunningtotal = wip_transrunningtotal,
                                        transagreementcustomernumber = wip_transagreementcustomernumber,
                                        transcustomercompany = wip_transcustomercompany,
                                        transagreementclosedflag = wip_transagreementclosedflag,
                                        transagreementddstatus = wip_transagreementddstatus,
                                        transagreementcloseddate = wip_transagreementcloseddate,
                                        transagreementdefname = wip_transagreementdefname,
                                        transagreementagreementdate = wip_transagreementagreementdate,
                                        transddpayment = wip_transddpayment,
                                        transagreementauthority = wip_transagreementauthority,
                                        transnetpaymentinterest = wip_transnetpaymentinterest,
                                        transnetpaymentcapital = wip_transnetpaymentcapital,
                                        transactionbatch_id = wip_transactionbatch_id,
                                        transactionstatus = wip_transactionstatus)
        new_transaction_summary.save()

    return


# def write_account_history(in_agreement, in_schedule_date, in_source_id, in_transtype, in_transflag, in_value,
#                                             in_gross_net_flag, in_payprointerest, in_payproprincipal,
#                                                 in_trans_date, in_description):
#
#     # Validate incoming dates
#     valid_date_format = '%Y-%m-%d'
#     val_today = datetime.datetime.today()
#
#     try:
#         date_obj = datetime.datetime.strftime(in_schedule_date, valid_date_format)
#     except:
#         in_schedule_date = None
#
#     try:
#         date_obj = datetime.datetime.strftime(in_trans_date, valid_date_format)
#     except:
#         in_trans_date = None
#
#     # Get Agreement Object and condition further processing
#     agreement_extract = None
#     if in_agreement:
#         try:
#             agreement_extract = go_agreement_querydetail.objects.get(agreementnumber=in_agreement)
#         except:
#             pass
#
#     if agreement_extract:
#         agreement_origin_extract = go_agreement_index.objects.filter(agreement_id=in_agreement).first()
#         if agreement_origin_extract:
#             agreement_origin = agreement_origin_extract.agreement_origin_flag
#         else:
#             agreement_origin = None
#     else:
#         agreement_origin = None
#
#     # agreement_origin = True
#     # Only do anything further if Agreement object has been retrieved.
#     if agreement_extract and agreement_origin:
#
#         # Populate Transaction Detail Values
#         wip_go_id = agreement_extract.go_id
#         wip_agreementnumber = agreement_extract.agreementnumber
#
#         if not isinstance(in_schedule_date, datetime.datetime):
#             my_time = datetime.datetime.min.time()
#             in_schedule_date = datetime.datetime.combine(in_schedule_date, my_time)
#
#         if in_trans_date and not isinstance(in_trans_date, datetime.datetime):
#             my_time = datetime.datetime.min.time()
#             in_trans_date = datetime.datetime.combine(in_trans_date, my_time)
#
#         if in_trans_date:
#             wip_transactiondate = in_trans_date
#         else:
#             if in_schedule_date:
#                 wip_transactiondate = in_schedule_date
#             else:
#                 wip_transactiondate = val_today
#
#         wip_transactiondate = wip_transactiondate + datetime.timedelta(hours=23)
#         # wip_transactionsourceid = in_source_id
#         wip_transactionsourceid = 'GO5'
#         wip_transtypeid = in_transtype
#         wip_transtypedesc = in_description
#         wip_transflag = in_transflag
#
#         if in_schedule_date:
#             if in_schedule_date <= val_today:
#                 wip_transfallendue = 1
#             else:
#                 wip_transfallendue = 0
#         else:
#             wip_transfallendue = 0
#
#         wip_value = round(decimal.Decimal(float(in_value)),2)
#         if agreement_extract.agreementdefname == 'Hire Purchase':
#             wip_transgrosspayment = wip_value
#             wip_transvatpayment = 0
#             wip_transnetpayment = 0
#         else:
#             if in_gross_net_flag == 'GROSS':
#                 wip_transgrosspayment = wip_value
#                 wip_transnetpayment = round((wip_transgrosspayment/decimal.Decimal(1.2)),2)
#                 wip_transvatpayment = round((wip_transgrosspayment-wip_transnetpayment ), 2)
#             else:
#                 wip_transnetpayment = wip_value
#                 wip_transvatpayment = round((wip_transnetpayment * decimal.Decimal(0.2)),2)
#                 wip_transgrosspayment = wip_transvatpayment + wip_transnetpayment
#
#         wip_transpayproid = None
#         wip_transpayproprincipal = round(in_payproprincipal,2)
#         wip_transpayprointerest = round(in_payprointerest,2)
#
#         # Write Transaction Detail record
#         new_transaction_detail = go_account_transaction_detail(
#                                         go_id = wip_go_id,
#                                         agreementnumber = wip_agreementnumber,
#                                         transactiondate = wip_transactiondate,
#                                         transactionsourceid = wip_transactionsourceid,
#                                         transtypeid = wip_transtypeid,
#                                         transtypedesc = wip_transtypedesc,
#                                         transflag = wip_transflag,
#                                         transfallendue = wip_transfallendue,
#                                         transnetpayment = wip_transnetpayment,
#                                         transvatpayment = wip_transvatpayment,
#                                         transgrosspayment = wip_transgrosspayment,
#                                         transpayproid = wip_transpayproid,
#                                         transpayproprincipal = wip_transpayproprincipal,
#                                         transpayprointerest = wip_transpayprointerest)
#         new_transaction_detail.save()
#
#         # Populate Transaction Summary Values
#         wip_transrunningtotal = None
#         wip_transagreementcustomernumber = agreement_extract.agreementcustomernumber
#         wip_transcustomercompany = agreement_extract.customercompany
#         wip_transagreementclosedflag = agreement_extract.agreementclosedflag
#         wip_transagreementddstatus = agreement_extract.agreementddstatus
#         wip_transagreementcloseddate = agreement_extract.closeddate
#         wip_transagreementdefname = agreement_extract.agreementdefname
#         wip_transagreementagreementdate = agreement_extract.agreementagreementdate
#         wip_transddpayment = 1
#         wip_transagreementauthority = agreement_extract.agreementauthority
#         wip_transnetpaymentinterest = wip_transpayprointerest
#         wip_transnetpaymentcapital = wip_transpayproprincipal
#         wip_transactionbatch_id = None
#         wip_transactionstatus = ' '
#
#         # Write Transaction Summary record
#         new_transaction_summary = go_account_transaction_summary(
#                                         go_id = wip_go_id,
#                                         agreementnumber = wip_agreementnumber,
#                                         transactiondate = wip_transactiondate,
#                                         transactionsourceid = wip_transactionsourceid,
#                                         transactionsourcedesc = 'HISTORY',
#                                         transtypeid = wip_transtypeid,
#                                         transtypedesc = wip_transtypedesc,
#                                         transflag = wip_transflag,
#                                         transfallendue = wip_transfallendue,
#                                         transnetpayment = wip_transnetpayment,
#                                         transgrosspayment = wip_transgrosspayment,
#                                         transrunningtotal = wip_transrunningtotal,
#                                         transagreementcustomernumber = wip_transagreementcustomernumber,
#                                         transcustomercompany = wip_transcustomercompany,
#                                         transagreementclosedflag = wip_transagreementclosedflag,
#                                         transagreementddstatus = wip_transagreementddstatus,
#                                         transagreementcloseddate = wip_transagreementcloseddate,
#                                         transagreementdefname = wip_transagreementdefname,
#                                         transagreementagreementdate = wip_transagreementagreementdate,
#                                         transddpayment = wip_transddpayment,
#                                         transagreementauthority = wip_transagreementauthority,
#                                         transnetpaymentinterest = wip_transnetpaymentinterest,
#                                         transnetpaymentcapital = wip_transnetpaymentcapital,
#                                         transactionbatch_id = wip_transactionbatch_id,
#                                         transactionstatus = wip_transactionstatus)
#         new_transaction_summary.save()
#
#     return
