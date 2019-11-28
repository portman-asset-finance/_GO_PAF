from django.apps import AppConfig


class CoreDdDatacashConfig(AppConfig):
    name = 'core_dd_datacash'

    # ### TEST1 NCF FUNDER BLUEROCK
    # auth_client = '99011006'
    # auth_password = 'txRkY92Sb3F'
    # bacs_url = 'https://testserver.datacash.com/Transaction'

    ### TEST1 NCF FUNDER BLUEROCK
    auth_client = '99011187'
    auth_password = 'xYAMQNQu4aE'
    bacs_url = 'https://testserver.datacash.com/Transaction'

    ### TEST2 BLU
    test_auth_client = '99011187'
    test_auth_password = 'xYAMQNQu4aE'
    test_bacs_url = 'https://testserver.datacash.com/Transaction'

    # ## LIVE
    # auth_client = '21900831'
    # auth_password = 'jrgEQZubHbs'
    # bacs_url = 'https://mars.transaction.datacash.com/Transaction'
