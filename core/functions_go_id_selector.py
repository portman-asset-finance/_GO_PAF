from core.models import go_extensions, client_configuration
from core_agreement_crud.models import go_agreement_index


def go_id_selector():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode= identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    # maxtabs = client_config.max_tab_create_agreement

    return client_config


def requiredtabs():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode = identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    maxtabs = client_config.max_tab_create_agreement

    return maxtabs


def daysbeforecalldd():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode = identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    days = client_config.dd_days_before_call

    return days


def daysbeforeddsetup():

   identifier = go_extensions.objects.get(ap_extension_sequence='1')

   extensioncode = identifier.ap_extension_code

   client_config = client_configuration.objects.get(client_id=extensioncode)

   days = client_config.dd_days_before_drawdown_setup

   return days


def riskfeenetamount():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode = identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    riskfeenet = client_config.risk_fee_amount

    return riskfeenet


def pmt_commission():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode = identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    pmt_min_commission = client_config.pmt_commission

    return pmt_min_commission


def pmt_yield():

    identifier = go_extensions.objects.get(ap_extension_sequence='1')

    extensioncode = identifier.ap_extension_code

    client_config = client_configuration.objects.get(client_id=extensioncode)

    pmt_min_yield = client_config.pmt_yield

    return pmt_min_yield


def is_go(agreement_no):

    try:
        go_id_obj = go_agreement_index.objects.get(agreement_id=agreement_no)
        if go_id_obj.agreement_origin_flag == 'GO':
            return True
        else:
            return False
    except:
        return False

