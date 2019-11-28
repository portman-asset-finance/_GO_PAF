from django.http import JsonResponse
from django.shortcuts import render, reverse

from core.models import go_extensions
from core.functions_bacs_file_process import app_process_bacs_files
from core.functions_datacash import app_process_datacash_drawdowns, app_process_datacash_setups, app_process_datacash_invalid_agreements
from core_arrears.functions_shared import app_process_bacs_udd_arrears, app_process_datacash_arrears, process_agent_allocations

from .functions import upload_bacs_file, upload_datacash_file

from datetime import datetime, timedelta


def process_bacs_files(request):
    """
    Process BACs files.
    :param request:
    :return:
    """

    context = {}
    keys = ('udd_success', 'auddis_success', 'bacs_error')
    for param in keys:
        key = 'core_bounce_{}'.format(param)
        if key in request.session:
            context[param] = request.session[key]
            del(request.session[key])

    if request.method == 'POST':

        file = request.FILES.get('file')

        if file:

            file_format = file.name[-3:]

            if file_format in ('xml', 'zip'):

                # try:

                upload_bacs_file(file)

                app_process_bacs_files()

                app_process_bacs_udd_arrears()

                process_agent_allocations()

                apellio_extension = go_extensions.objects.get(ap_extension_code='audrun')
                apellio_extension.ap_extension_last_interface_run = datetime.now()
                apellio_extension.ap_extension_next_interface_run = \
                    apellio_extension.ap_extension_last_interface_run + \
                    timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
                apellio_extension.save()

                request.session['core_bounce_udd_success'] = True

                # except Exception as e:
                #     request.session['core_bounce_bacs_error'] = 'File Processing Error - Please contact support'

            else:
                request.session['core_bounce_bacs_error'] = 'Invalid format. Only XML and ZIP files are accepted.'

        else:
            request.session['core_bounce_bacs_error'] = 'Please upload a file.'

        return JsonResponse(context)

    return render(request, 'bounces.html', context)


def process_datacash_files(request):

    context = {}
    keys = ('datacash_drawdowns', 'datacash_setups', 'datacash_error')
    for param in keys:
        key = 'core_bounce_{}'.format(param)
        if key in request.session:
            context[param] = request.session[key]
            del(request.session[key])

    if request.method == 'POST':

        file = request.FILES.get('file')

        if file:

            if file.name in ('datacash_drawdowns.xlsx', 'datacash_setups.xlsx'):

                # try:

                upload_datacash_file(file)

                if file.name == 'datacash_drawdowns.xlsx':

                    app_process_datacash_drawdowns()

                    app_process_datacash_arrears()

                    process_agent_allocations()

                    apellio_extension = go_extensions.objects.get(ap_extension_code='dc_drawdn')
                    apellio_extension.ap_extension_last_interface_run = datetime.now()
                    apellio_extension.ap_extension_next_interface_run = \
                        apellio_extension.ap_extension_last_interface_run + \
                        timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
                    apellio_extension.save()

                    app_process_datacash_invalid_agreements()

                    request.session['core_bounce_datacash_drawdowns'] = True

                elif file.name == 'datacash_setups.xlsx':

                    app_process_datacash_setups()

                    apellio_extension = go_extensions.objects.get(ap_extension_code='dc_setup')
                    apellio_extension.ap_extension_last_interface_run = datetime.now()
                    apellio_extension.ap_extension_next_interface_run = \
                        apellio_extension.ap_extension_last_interface_run + \
                        timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
                    apellio_extension.save()

                    app_process_datacash_invalid_agreements()

                    request.session['core_bounce_datacash_setups'] = True

                # except Exception as e:
                #     request.session['core_bounce_datacash_error'] = 'Invalid File Format - Please confirm file contents'

            else:
                request.session['core_bounce_datacash_error'] = 'Invalid file name. Must be either ' \
                                                                'datacash_drawdowns.xlsx or datacash_setups.xlsx'

        else:
            request.session['core_bounce_datacash_error'] = 'Please upload a file.'

        return JsonResponse(context)

    return render(request, 'bounces.html', context)

