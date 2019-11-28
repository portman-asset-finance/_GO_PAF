from django.core.management.base import BaseCommand

from core_companies_house.functions import api_call, Compare_Company_House_Data

from pprint import pprint


class Command(BaseCommand):
    """
    Django management command to test the companies house API call.

    """

    # def add_arguments(self, parser):
    #     parser.add_argument('request_type')

    def handle(self, *args, **options):

        print(Compare_Company_House_Data())

        # if not options.get('request_type'):
        #     raise Exception('No charge type argument provided')
        #
        # pprint(api_call(options['request_type'], **self.__get_args(options['request_type'])))

    # def __get_args(self, request_type):
    #
    #     kwargs = {
    #         'company_number': '01582278'
    #     }
    #
    #     if request_type == 'CHARGE':
    #         kwargs.update({
    #             'charge_id': '117s-7_ys419LBU-UrQ0JPDW9d0'
    #         })
    #     if request_type == 'CHARGES_LIST':
    #         kwargs.update({
    #             'company_number': '01582278'
    #         })
    #
    #     return kwargs

