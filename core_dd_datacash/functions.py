"""
Functions specific for DataCash processing.

"""

import zlib
import base64
import requests
import datetime
import xmltodict

from collections import OrderedDict

from decimal import Decimal

import xml.etree.ElementTree as ET

from .apps import CoreDdDatacashConfig
from .models import datacash_credentials

from core_agreement_crud.models import go_agreement_index
from core.models import ncf_dd_audit_log
from core_dd_drawdowns.models import Log, BatchHeaders


def batch_drawdowns(**kwargs):
    """
    Create batch request for direct debit drawdowns and send to DataCash.
    :return:
    """

    if not kwargs.get('batch_ref'):
        raise Exception('batch_drawdowns: missing required key "batch_ref"')

    if not kwargs.get('total_count'):
        raise Exception('batch_drawdowns: missing required key "total_count"')

    if not kwargs.get('total_amount'):
        raise Exception('batch_drawdowns: missing required key "total_amount"')

    if not kwargs.get('recs'):
        raise Exception('batch_drawdowns: missing required key "recs"')

    recs = kwargs['recs']
    batch_ref = kwargs['batch_ref']

    xml = ET.Element('BatchInputRequest')

    headers = {
        'format': 'xml_directdebit',
        'reference': batch_ref
    }

    h_xml = dict_to_xml('Header', headers)
    xml.append(h_xml)

    bh_rec = BatchHeaders.objects.get(reference=batch_ref)
    creds = datacash_credentials.objects.get(funder=bh_rec.funder)
    print('boom..........................',creds.test_auth_client,)
    print('boom..........................',creds.test_auth_password,)
    t_xml = ET.Element('Transactions')

    for rec in recs:
        req = OrderedDict({
            'Authentication': {
                'client': creds.test_auth_client,
                'password': creds.test_auth_password
            },
            'Transaction': {
                'TxnDetails': {
                    'merchantreference': rec['reference'],
                    'amount': '{}'.format(Decimal('{0:.2f}'.format(rec['amount']))),
                },
                'HistoricTxn': {
                    'method': 'drawdown',
                    'reference': rec['dd_reference'],
                    'duedate': rec['due_date']
                }
            }
        })

        t_xml.append(dict_to_xml('Request', req))

    xml.append(t_xml)
    print(ET.tostring(xml))

    batch_input_str = base64.b64encode(zlib.compress(ET.tostring(xml))).decode('UTF-8')

    try:
        xml_request(
            total_count=kwargs['total_count'],
            method='drawdown',
            total_amount=kwargs['total_amount'],
            batch_data=batch_input_str,
            batch_ref=batch_ref
        )
        for rec in recs:
            _add_to_audit_log(rec, 'drawdown - requested')
    except Exception as e:
        for rec in recs:
            _add_to_audit_log(rec, 'drawdown - invalid'.format(e))
        raise e

    return True


def _add_to_audit_log(rec, reason):

    print(rec)

    ncf_dd_audit_log(
        da_agreement_id=rec['agreement_id'],
        da_reference=rec['reference'],
        da_source='GOBATCH',
        da_effective_date=rec.get('effective_date'),
        da_account_name=rec['account_name'],
        da_payer_account_number=rec['account_number'],
        da_referencestrip=rec['reference'],
        da_payer_sort_code=rec['sort_code'],
        da_sourcetype='GO',
        da_created_at=datetime.datetime.now(),
        da_reason=reason,
        da_reporting_date=datetime.datetime.now(),
        da_reporting_date_set='Y'
    ).save()


def xml_request(**kwargs):
    """
    Function that handles XML request to DataCash
    :param kwargs:
    :return:
    """

    xml = ET.Element('Request')

    bh_rec = BatchHeaders.objects.get(reference=kwargs['batch_ref'])
    creds = datacash_credentials.objects.get(funder=bh_rec.funder)

    auth = {
        'client': creds.test_auth_client,
        'password': creds.test_auth_password
    }
    xml.append(dict_to_xml('Authentication', auth))

    t_xml = {
        'BatchInputTxn': {
            'batchfile': ('format', 'xml_directdebit', kwargs['batch_data']),
            'txn_count': str(kwargs['total_count']),
            'total_amount': str(kwargs['total_amount']),
        }
    }
    xml.append(dict_to_xml('Transaction', t_xml))

    batch_header = BatchHeaders.objects.get(reference=kwargs.get('batch_ref'))

    print(ET.tostring(xml))
    _log = Log(batch_header=batch_header, request=ET.tostring(xml).decode('UTF-8'), request_time=datetime.datetime.now())
    _log.save()

    try:
        res = requests.post(CoreDdDatacashConfig.bacs_url, data=ET.tostring(xml).decode('UTF-8'))
    except requests.exceptions.ConnectionError as e:
        raise Exception('Datacash Service Unavailable')
    except requests.exceptions.HTTPError as e:
        raise Exception('Datacash Service Unavailable')

    # TODO: /Transaction_bad url remedy
    if res.status_code not in (200, '200'):
        raise Exception('Datacash Service Unavailable. Status code {}'.format(res.status_code))

    print(res.text)
    _log.response = res.text
    _log.response_time = datetime.datetime.now()
    _log.save()

    res_xml = xmltodict.parse(res.text)
    if res_xml['Response']['status'] not in ('1', 1):
        raise Exception("{}".format(res_xml['Response'].get('information', res_xml['Response']['reason'])))

    return True


def dict_to_xml(tag, d):
    """
    Converts a dictionary into XML.
    :param tag:
    :param d:
    :return:
    """

    e = ET.Element(tag)
    if '__attr__' in d:
        e.set(d['__attr__'][0], d['__attr__'][1])
        del d['__attr__']

    for k, v in d.items():
        if type(v) is dict:
            c = dict_to_xml(k, v)
        else:
            c = ET.Element(k)
            if type(v) is tuple:
                c.set(v[0], v[1])
                c.text = v[2]
            else:
                c.text = v
        e.append(c)

    return e

