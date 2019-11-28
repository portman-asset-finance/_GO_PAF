
import numpy
import traceback

from datetime import datetime, timedelta, date

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import DDHistory

from .forms import DirectDebitForm
from .functions import generate_dd_reference, create_ddi_with_datacash, update_ddi_status, cancel_ddi_with_datacash, \
                       cancel_ddi_with_datacash_based_on_dd_history_id

from core.functions_go_id_selector import daysbeforecalldd, daysbeforeddsetup
from core_agreement_crud.functions import get_next_due_date, get_holidays

from core_dd_drawdowns.models import DrawDown
from core_agreement_crud.models import go_agreement_index


@login_required(login_url='signin')
def cancel_dd_instruction(request, dd_history_id):

    context = {}

    try:
        context = cancel_ddi_with_datacash_based_on_dd_history_id(dd_history_id, request.user)
    except Exception as e:
        context['error'] = str(e)

    return JsonResponse(context)


@login_required(login_url='signin')
def get_dd_history(request, agreement_no):
    """
    Gets records from the dd_history model.
    :param request:
    :param agreement_no:

    """
    data = dict()
    if request.method == 'GET':
        context = {
            'agreement_no': agreement_no,
            'records': DDHistory.objects.filter(agreement_no=agreement_no).order_by('-sequence'),
            'future': get_next_due_date(agreement_no)
        }
        data['is_manual'] = go_agreement_index.objects.filter(agreement_id=agreement_no, manual_payments=1).exists()
        data['html'] = render_to_string('includes/partial_dd_list.html',
                                        context,
                                        request=request)
    return JsonResponse(data)


@login_required(login_url='signin')
def create_new_dd_instruction(request, agreement_no):
    """
    Create's a new dd instruction and a dd_history record
    :param request:
    :param agreement_no:

    """

    data = dict()
    template = 'includes/partial_dd_create_form.html'

    go_id = go_agreement_index.objects.get(agreement_id=agreement_no)

    manual_payment_update = False
    manual_payment_failed = False
    manual_payments_display = go_id.manual_payments

    if request.method == 'POST':

        manual_payments = request.POST.get('manual_payments', 0) or 0
        if manual_payments == "0":
            manual_payments = 0
            manual_payments_display = 0

        form = DirectDebitForm(request.POST)

        if manual_payments:

            if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_no).exists():
                data['form_is_valid'] = False
                data['error'] = 'This agreement has a transaction in an open batch.'
                manual_payment_failed = True

            if not manual_payment_failed:

                go_id.manual_payments = 1
                go_id.save()

                cancel_ddi_with_datacash(agreement_no, user=request.user)
                manual_payment_update = True
                data['form_is_valid'] = True
                manual_payments_display = 1

        else:
            if form.is_valid():
                try:

                    rec = form.save(commit=False)

                    if DDHistory.objects.filter(reference=rec.reference).exists():
                        raise Exception("Duplicate reference")

                    args = (
                        agreement_no,
                        rec.reference,
                        rec.account_name,
                        rec.account_number,
                        rec.sort_code,
                        request.user
                    )
                    create_ddi_with_datacash(*args)

                    # rec.effective_date = datetime.now() + timedelta(days=7)
                    #
                    # rec.user = request.user
                    #
                    # rec.sequence = "9999"
                    #
                    # rec.agreement_no = agreement_no
                    #
                    # # form.save()

                    # if rec.dd_reference:
                    #     update_ddi_status(agreement_no, 'Active DD')
                    # else:
                    #     update_ddi_status(agreement_no, 'Inactive DD')

                    data['form_is_valid'] = True
                    go_id.manual_payments = 0
                    go_id.save()

                except Exception as e:
                    print('Failed.')
                    if str(e) == 'Failed validation check':
                        go_id.manual_payments = 0
                        go_id.save()
                        data['error'] = 'Bank Details Invalid'
                    else:
                        data['error'] = '{}'.format(e)
                        print(traceback.format_exc())
                    data['form_is_valid'] = False


            else:
                data['form_is_valid'] = False

        if data['form_is_valid']:
            template = 'includes/partial_create_form_success_message.html'
        else:
            form.fields['reference'].initial = generate_dd_reference(agreement_no)
    else:
        form = DirectDebitForm()
        rec = None
        if not go_id.manual_payments:
            try:
                rec = DDHistory.objects.get(sequence=9999, agreement_no=agreement_no)
            except Exception as e:
                print(e)
                pass
        if rec:
            form.fields['reference'].initial = rec.reference
            form.fields['account_number'].initial = rec.account_number
            form.fields['account_name'].initial = rec.account_name
            form.fields['sort_code'].initial = rec.sort_code
            form.fields['reference'].initial = generate_dd_reference(agreement_no)
        else:
            form.fields['reference'].initial = generate_dd_reference(agreement_no)

    context = {
        'form': form,
        'error': data.get('error'),
        'agreement_no': agreement_no,
        'go_id': go_id,
        'manual_payments_display': manual_payments_display,
        'manual_payment_update': manual_payment_update
    }

    holidays = get_holidays()

    days_before_dd_call = daysbeforecalldd()
    context['days_before_dd_call'] = days_before_dd_call

    days_before_setup_active = daysbeforeddsetup()

    context['next_due_date'] = get_next_due_date(agreement_no)

    context['setup_active_date'] = numpy.busday_offset(date.today(), days_before_setup_active,
                                                       roll='forward', holidays=holidays).astype(datetime)

    context['call_active_date'] = numpy.busday_offset(date.today(),
                                                      days_before_dd_call + days_before_setup_active,
                                                      roll='forward', holidays=holidays).astype(datetime)

    if context['next_due_date'].date() < context['call_active_date']:
        context['state'] = 'red'
        context['earliest_call_date'] = numpy.busday_offset(context['call_active_date'],
                                                            -days_before_dd_call, roll='backward',
                                                            holidays=holidays).astype(datetime)

    else:
        context['state'] = 'blue'
        context['earliest_call_date'] = numpy.busday_offset(context['next_due_date'],
                                                            -days_before_dd_call, roll='backward',
                                                            holidays=holidays).astype(datetime)

    context['days_before_setup_active'] = days_before_setup_active

    batches = [row for row in DrawDown.objects.filter(status='OPEN', agreement_id=agreement_no)]
    context['batches'] = batches

    data['html_form'] = render_to_string(template,
                                         context,
                                         request=request)

    return JsonResponse(data)


# @login_required(login_url='signin')
# def create_new_dd_instruction(request, agreement_no):
#
#     data = {}
#     context = {}
#     template = 'includes/partial_dd_create_form.html'
#
#     if request.method == 'POST':
#         pass
#
#     data['html_form'] = render_to_string(template, context, request=request)
#
#     return JsonResponse(data)




