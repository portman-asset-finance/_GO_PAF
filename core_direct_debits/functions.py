import requests
import datetime
import dicttoxml
import xmltodict

from .models import DDHistory, DDLog
from .apps import CoreDirectDebitsConfig

from core.models import ncf_dd_audit_log, ncf_dd_status_text
from core_dd_datacash.models import datacash_credentials

from core_agreement_crud.models import go_account_transaction_summary, go_agreement_querydetail, go_agreements,\
                                       go_agreement_index

from core_eazycollect.functions import create_dd_mandate


def update_agreement_tables(agreement_id, **kwargs):

    update_object = {
        'agreementbanksortcode': kwargs.get('sort_code'),
        'agreementbankreference': kwargs.get('reference'),
        'agreementbankaccountname': kwargs.get('account_name'),
        'agreementbankaccountnumber': kwargs.get('account_number'),
        'agreementdatacashmerchantref': kwargs.get('dd_reference')
    }

    # Agreements
    go_agreements.objects.filter(agreementnumber=agreement_id).update(**update_object)

    # Agreement_QueryDetail
    go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(**update_object)

    return True


def update_ddi_status(agreement_no, status):
    """
    Update all tables with the ddi status

    """

    ddi_status = ncf_dd_status_text.objects.get(dd_text_description=status)

    # Account Transaction Summary
    go_account_transaction_summary.objects.filter(agreementnumber=agreement_no).update(transagreementddstatus=ddi_status)

    # Agreement Query Detail
    go_agreement_querydetail.objects.filter(agreementnumber=agreement_no).update(agreementddstatus=ddi_status)

    return True


def generate_dd_reference(agreement_no):
    """
    Generates a unique dd reference.
    :param agreement_no:
    :return:
    """
    count = DDHistory.objects.filter(agreement_no=agreement_no).count()
    while True:
        reference = '{}{}'.format(CoreDirectDebitsConfig.ref_prefix, agreement_no)
        if count > 0:
            reference += '-{}'.format(count)
        if not DDHistory.objects.filter(reference=reference).count():
            return reference
        count = count + 1


def cancel_ddi_with_datacash_based_on_dd_history_id(dd_history_id, user):

    rec = DDHistory.objects.get(id=dd_history_id)

    agreement_id = rec.agreement_no

    log = DDLog(
        agreement_no=agreement_id,
        reference=rec.reference,
        dd_reference=rec.dd_reference,
        account_name=rec.account_name,
        account_number=rec.account_number,
        sort_code=rec.sort_code,
        method='revoke',
        user=user
    )

    datacash_request(
        method='revoke',
        agreement_id=agreement_id,
        reference=rec.reference,
        dd_reference=rec.dd_reference,
        log=log
    )

    log.save()

    ncf_dd_audit_log(
        da_agreement_id=agreement_id,
        da_reference=rec.reference,
        da_source='GOSETUP',
        da_account_name=rec.account_name,
        da_reason='revoked',
        da_payer_sort_code=rec.sort_code,
        da_payer_account_number=rec.account_number,
        da_datacash_method='revoke',
        da_datacash_stage='revoked',
        da_referencestrip=agreement_id,
        da_sourcetype='GO',
        da_effective_date=datetime.datetime.now(),
        da_created_at=datetime.datetime.now(),
        da_reporting_date=datetime.datetime.now(),
        da_reporting_date_set='Y'
    ).save()

    rec.cancelled_date = datetime.datetime.now()
    rec.save()

    return {'success': rec.cancelled_date, 'agreement_id': agreement_id}


def cancel_ddi_with_datacash(agreement_id, user=None, recs=None):
    """
    Sends a request to DataCash to cancel a DDI, also updates
    ddsequence value
    :return:
    """

    recs = DDHistory.objects.filter(agreement_no=agreement_id, sequence=9999)

    for rec in recs:

        if rec.dd_reference:

            log = DDLog(
                agreement_no=agreement_id,
                reference=rec.reference,
                dd_reference=rec.dd_reference,
                account_name=rec.account_name,
                account_number=rec.account_number,
                sort_code=rec.sort_code,
                method='revoke',
                user=user
            )

            datacash_request(
                method='revoke',
                agreement_id=agreement_id,
                reference=rec.reference,
                dd_reference=rec.dd_reference,
                log=log
            )

            log.save()

            ncf_dd_audit_log(
                da_agreement_id=agreement_id,
                da_reference=rec.reference,
                da_source='GOSETUP',
                da_account_name=rec.account_name,
                da_reason='revoked',
                da_payer_sort_code=rec.sort_code,
                da_payer_account_number=rec.account_number,
                da_datacash_method='revoke',
                da_datacash_stage='revoked',
                da_referencestrip=agreement_id,
                da_sourcetype='GO',
                da_effective_date=datetime.datetime.now(),
                da_created_at=datetime.datetime.now(),
                da_reporting_date=datetime.datetime.now(),
                da_reporting_date_set='Y',
            ).save()

        rec.cancelled_date = datetime.datetime.now()
        rec.save()

        update_ddi_status(agreement_id, 'Inactive DD')

    return recs


def create_ddi_with_datacash(agreement_id, reference, account_name, account_number, sort_code, user=None):
    """
    Cancels any existing, active DDIs, updates the sequence number, then
    creates a new DDI
    :return: datacash reference
    """

    # Cancel existing DDIs
    recs = cancel_ddi_with_datacash(agreement_id, user)

    log = DDLog(
        agreement_no=agreement_id,
        reference=reference,
        sort_code=sort_code,
        account_name=account_name,
        account_number=account_number,
        method='setup',
        user=user
    )

    kwargs_for_audit_log = {
        'da_agreement_id': agreement_id,
        'da_reference': reference,
        'da_source': 'GOSETUP',
        'da_account_name': account_name,
        'da_payer_sort_code': sort_code,
        'da_payer_account_number': account_number,
        'da_datacash_method': '',
        'da_datacash_stage': '',
        'da_referencestrip': agreement_id,
        'da_sourcetype': 'GO',
        'da_effective_date': datetime.datetime.now(),
        'da_created_at': datetime.datetime.now()
    }

    ncf_dd_audit_log(
        da_reason='New Instruction',
        da_reporting_date = datetime.datetime.now(),
        da_reporting_date_set = 'Y',
        **kwargs_for_audit_log
    ).save()

    dd_history_obj = DDHistory(
        user=user,
        sequence=9999,
        reference=reference,
        agreement_no=agreement_id,
        account_name=account_name,
        sort_code=sort_code,
        account_number=account_number,
        effective_date=datetime.datetime.now() + datetime.timedelta(days=7),
        valid=False
    )

    error = None

    # Create new DDI
    try:

        ref = datacash_request(
            method='setup',
            agreement_id=agreement_id,
            reference=reference,
            account_number=account_number,
            account_name=account_name,
            sort_code=sort_code,
            log=log,
            dd_history=dd_history_obj
        )
        ncf_dd_audit_log(
            da_reason='setup - valid DDI',
            da_reporting_date=datetime.datetime.now(),
            da_reporting_date_set='Y',
            **kwargs_for_audit_log
        ).save()

        log.dd_reference = ref

        update_ddi_status(agreement_id, 'Active DD')
        update_agreement_tables(agreement_id, reference=reference, dd_reference=ref,
                                account_number=account_number, account_name=account_name, sort_code=sort_code,)

    except Exception as e:

        log.success = False

        ncf_dd_audit_log(
            da_reason='setup - invalid DDI',
            da_reporting_date=datetime.datetime.now(),
            da_reporting_date_set='Y',
            **kwargs_for_audit_log
        )

        update_ddi_status(agreement_id, 'Inactive DD')

        error = e

    count = DDHistory.objects.filter(agreement_no=agreement_id).count()
    for rec in recs:
        DDHistory.objects.filter(id=rec.id).update(sequence=count)

    go_agreement_querydetail.objects.filter(agreementnumber=agreement_id).update(agreementbankaccountname=account_name,
                                                                                 agreementbanksortcode=sort_code,
                                                                                 agreementbankaccountnumber=account_number,
                                                                                 agreementbankreference=reference)

    log.save()

    if error:
        raise error

    return ref


def datacash_request(**kwargs):
    """
    Submits a request to DataCash
    :return:
    """

    if not kwargs.get('method'):
        raise Exception('datacash_request: method must be provided.')

    if kwargs.get('method') not in ('setup', 'revoke'):
        raise Exception('datacash_request: invalid method {}'.format(kwargs.get('method')))

    if not kwargs.get('agreement_id'):
        raise Exception('datacash_request: agreement_id must be provided.')

    if not kwargs.get('reference'):
        raise Exception('datacash_request: reference must be provided.')

    if kwargs.get('method') == 'setup':
        for k in ('account_name', 'account_number', 'sort_code'):
            if not kwargs.get(k):
                raise Exception('datacash_request: {} must be provided.'.format(k))

    dd_history = kwargs.get('dd_history')

    if kwargs.get('method') == 'revoke':
        if not kwargs.get('dd_reference'):
            raise Exception('datacash_request: dd_reference must be provided.')

    log = kwargs.get('log')

    go_id = go_agreement_index.objects.get(agreement_id=kwargs['agreement_id'])
    creds = datacash_credentials.objects.get(funder=go_id.funder)

    xml = {
        'Authentication': {
            'client': creds.test_auth_client,
            'password': creds.test_auth_password
        }
    }

    txn_req = {}

    if kwargs.get('method') == 'revoke':
        txn_req = {
            'HistoricTxn': {
                'method': 'revoke',
                'reference': kwargs.get('dd_reference'),
            }
        }

    if kwargs.get('method') == 'setup':
        txn_req = {
            'DirectDebitTxn': {
                'sortcode': kwargs.get('sort_code'),
                'accountnumber': kwargs.get('account_number'),
                'accountname': kwargs.get('account_name'),
                'method': 'setup'
            }
        }

    txn_req['TxnDetails'] = {
        'merchantreference': kwargs.get('reference')
    }
    xml['Transaction'] = txn_req

    print(xml)

    xml_req = dicttoxml.dicttoxml(xml, custom_root='Request', attr_type=False)

    if log:
        log.request = xml_req.decode('utf-8')

    try:
        res = requests.post(CoreDirectDebitsConfig.bacs_url, data=xml_req)
    except requests.exceptions.ConnectionError as e:
        if dd_history:
            dd_history.save()
        raise Exception('Datacash Service Unavailable')
    except requests.exceptions.HTTPError as e:
        if dd_history:
            dd_history.save()
        raise Exception('Datacash Service Unavailable')

    if res.status_code != 200:
        if dd_history:
            dd_history.save()
        raise Exception('datacash_request failed (status {})'.format(res.status_code))

    if log:
        log.response = res.text

    xml_res = xmltodict.parse(res.text)
    print(xml_res)

    if dd_history:
        dd_history.dd_reference = xml_res['Response'].get('datacash_reference')
        dd_history.save()

    if xml_res['Response']['status'] not in (1, '1', 75, '75'):
        print("Response.reason:", xml_res['Response']['reason'])
        if log:
            log.success = False
            if xml_res['Response'].get('information'):
                log.info = xml_res['Response']['information']
            else:
                log.info = xml_res['Response']['reason']
            print('log.info:', len(log.info))
            log.save()
        raise Exception(kwargs.get('error', '{}'.format(xml_res['Response']['reason'])))

    if log:
        log.success = True
        log.info = 'SUCCESS'

    if dd_history:
        dd_history.valid = True
        dd_history.save()

    return xml_res['Response'].get('datacash_reference', True)


def create_ddi_with_eazycollect(*args, **kwargs):

    create_dd_mandate(*args, **kwargs)