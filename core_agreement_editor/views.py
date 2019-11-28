from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.http import HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .forms import EditorForm
from .models import Editor

# Card 68 Settlement Work Package #
from django.db.models import Sum, Q
# Card 68 Settlement Work Package #

from .filters import AnchorimportAgreement_QueryDetail_Filter, Editor_Filter
from . functions import change_single_date_function, change_future_dates_function, remove_single_risk_fee_function, remove_future_risk_fee_function,\
    remove_single_bamf_fee_function, remove_future_bamf_fee_function, reschedule_function, change_single_value_function, change_future_values_function
from core_agreement_crud.functions import settlement_function, global_termination_function, move_consol_amount_function, settlement_documentation_function
from core_agreement_crud.models import go_customers, go_agreement_querydetail, go_agreements, go_broker, go_account_transaction_detail, go_account_transaction_summary, \
                    go_agreement_definitions, go_profile_types, go_agreement_id_definitions, go_agreement_index, go_sales_authority
from core.models import reason_codes
from core_direct_debits.functions import cancel_ddi_with_datacash
from anchorimport.models import AnchorimportAgreement_QueryDetail, \
                                AnchorimportCustomers, \
                                AnchorimportAccountTransactionSummary, \
                                AnchorimportAccountTransactionDetail
import decimal

#JC Additions
import re
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, Frame, BaseDocTemplate, PageTemplate, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from reportlab.pdfgen import canvas
from xlsxwriter.workbook import Workbook
import decimal, datetime
import random
from datetime import timedelta

from core_dd_drawdowns.models import DrawDown


@login_required(login_url='signin')
def update_or_create(request, agreement_id):
    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),'trans_detail_id': request.GET.get('trans_detail_id')}

    template_name = 'includes/partial_editor_update_or_create.html'

    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    context['transactiondate'] = transaction_summary_extract.transactiondate

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def editor_list(request):#, agreement_id):
    editors = Editor.objects.all().order_by('-agreement_number')

    editor_list = Editor_Filter(request.GET, queryset=editors)
    paginator = Paginator(editor_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') #or request.GET.get('customercompany') \
                 #or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')
    return render(request, 'core_agreement_editor/editor_list.html', {#'editor_within_agreement': editors,
                                                                       'editor_list': editor_list,
                                                                       'editor_list_qs': pub,
                                                                       'has_filter': has_filter
                                                                       })


@login_required(login_url='signin')
def editor_within_agreement(request, agreement_id):
    editors = Editor.objects.all().order_by('-agreement_number')
    editor_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=agreement_id)

    editor_list = Editor_Filter(request.GET, queryset=editors)
    paginator = Paginator(editor_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') #or request.GET.get('customercompany') \
                 #or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')
    return render(request, 'core_agreement_editor/editor_within_agreement.html', {'editor_within_agreement': editors,
                                                                       'editor_detail': editor_detail,
                                                                       #'editor_list': editor_list,
                                                                       'editor_list_qs': pub,
                                                                       'has_filter': has_filter
                                                                       })


@login_required(login_url='signin')
def save_editor_form(request, form, template_name, agid=None):
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            editors = Editor.objects.all()
            data['html_editor_list'] = render_to_string('includes/partial_editor_list.html', {
                'editor_list': editors
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form, 'agreement_id': agid}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)


@login_required(login_url='signin')
def editor_create(request, agreement_id):
    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}

    template_name = 'includes/partial_editor_create.html'

    transaction_summary_extract_reschedule = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id).exclude(transtypeid__in =['1','4'])

    settlement_figure_net_queryset = transaction_summary_extract_reschedule.aggregate(Sum('transnetpayment'))
    context['settlement_figure_net'] = settlement_figure_net_queryset['transnetpayment__sum']

    # settlement_figure_gross_queryset = transaction_summary_extract_reschedule.aggregate(Sum('transgrosspayment'))
    # context['settlement_figure_gross'] = settlement_figure_gross_queryset['transgrosspayment__sum']

    # docfees = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transtypeid__in=['1','4'])
    # docfees_net_queryset = docfees.aggregate(Sum('transnetpayment'))
    # context['docfee_net'] = docfees_net_queryset['transnetpayment__sum']
    #
    # other = settlement_figure_net_queryset['transnetpayment__sum']

    if request.method == 'POST':
        reschedule_function(request, agreement_id)

        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        return redirect(url + '?change_profile=1')

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def editor_create_list(request):
    if request.method == 'POST':
        form = EditorForm(request.POST)
    else:
        form = EditorForm()
    return save_editor_form(request, form, 'includes/partial_editor_create.html')


@login_required(login_url='signin')
def editor_update(request, pk):
    editor = get_object_or_404(Editor, pk=pk)
    if request.method == 'POST':
        form = EditorForm(request.POST, instance=editor)
    else:
        form = EditorForm(instance=editor)
    return save_editor_form(request, form, 'includes/partial_editor_update.html')


@login_required(login_url='signin')
def editor_delete(request, pk):
    editor = get_object_or_404(Editor, pk=pk)
    data = dict()
    if request.method == 'POST':
        editor.delete()
        data['form_is_valid'] = True  # This is just to play along with the existing code
        editors = editor.objects.all()
        data['html_editor_list'] = render_to_string('includes/partial_editor_list.html', {
            'editor_list': editors
        })
    else:
        context = {'editor': editor}
        data['html_form'] = render_to_string('includes/partial_editor_delete.html',
            context,
            request=request,
        )
    return JsonResponse(data)


@login_required(login_url='signin')
def modalchangedate(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    template_name = 'includes/modalchangedate.html'

    transaction_summary_extract = go_account_transaction_summary.objects.get(id = context['transaction_id'])
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)

    context['comparisondate'] = agreement_detail.agreementfirstpaymentdate
    context['transactiondate'] = transaction_summary_extract.transactiondate
    # context['transnetpayment'] = transaction_summary_extract.transactiondate

    batch_error = False

    if request.method == 'POST':

        if request.POST.get('submit_type') == "singledates":

            batch_error = change_single_date_function(request,agreement_id)

        if request.POST.get('submit_type') == "futuredates":
            batch_error = change_future_dates_function(request,agreement_id)

        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        if batch_error:
            url += '?batch_error=' + batch_error
        else:
            url += '?change_profile=1'
        return redirect(url)

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def modalchangefees(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'), 'trans_detail_id': request.GET.get('trans_detail_id')}
    template_name = 'includes/modalchangefees.html'

    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    context['transactiondate'] = transaction_summary_extract.transactiondate

    try:
        transaction_detail_extract_rf = go_account_transaction_detail.objects.get(agreementnumber = agreement_id,
                                                                                 transtypedesc ='Risk Fee',
                                                                                 transactiondate= context['transactiondate']
                                                                                  )
        context['rf'] = round(transaction_detail_extract_rf.transnetpayment,2)

    except:
        # transaction_detail_extract_rf = False
        context['rf'] = '0.00'

    try:
        transaction_detail_extract_bamf = go_account_transaction_detail.objects.get(agreementnumber=agreement_id,
                                                                                    transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                    transactiondate=context['transactiondate']
                                                                                    )
        context['bamf'] = round(transaction_detail_extract_bamf.transnetpayment,2)

    except:
        # transaction_detail_extract_bamf = False
        context['bamf'] = '0.00'

    if request.method == 'POST':

        submit_type = request.POST.get('submit_type')
        remove_bamf = False
        remove_risk = False
        batch_error = False

        if request.POST.get('remove_bamf', '') == 'on':
            remove_bamf = True

        if request.POST.get('remove_risk_fee', '') == 'on':
            remove_risk = True

        if submit_type == 'single':

            if remove_bamf:
                batch_error = remove_single_bamf_fee_function(request, agreement_id)

            if remove_risk:
                batch_error = remove_single_risk_fee_function(request, agreement_id)

        if submit_type == 'future':

            if remove_bamf:
                batch_error = remove_future_bamf_fee_function(request, agreement_id)

            if remove_risk:
                batch_error = remove_future_risk_fee_function(request, agreement_id)

        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        if batch_error:
            url += '?batch_error=' + batch_error
        else:
            url += '?change_profile=1'
        return redirect(url)

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def modalchangevalues(request, agreement_id):
    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),'trans_detail_id': request.GET.get('trans_detail_id')}
    template_name = 'includes/modalchangevalues.html'


    transaction_summary_extract = go_account_transaction_summary.objects.get(id=context['transaction_id'])
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)

    context['comparisondate'] = agreement_detail.agreementfirstpaymentdate
    context['transactiondate'] = transaction_summary_extract.transactiondate

    try:
        transaction_detail_extract_rental = go_account_transaction_detail.objects.get(agreementnumber=agreement_id,
                                                                                  transtypedesc__isnull = True,
                                                                                  transactiondate=context[
                                                                                      'transactiondate']
                                                                                  )
        context['rental'] = round(transaction_detail_extract_rental.transnetpayment, 2)

    except:
        # transaction_detail_extract_rf = False
        context['rental'] = '0.00'


    try:
        transaction_detail_extract_rf = go_account_transaction_detail.objects.get(agreementnumber = agreement_id,
                                                                                 transtypedesc ='Risk Fee',
                                                                                 transactiondate= context['transactiondate']
                                                                                  )
        context['rf'] = round(transaction_detail_extract_rf.transnetpayment,2)

    except:
        # transaction_detail_extract_rf = False
        context['rf'] = '0.00'

    try:
        transaction_detail_extract_bamf = go_account_transaction_detail.objects.get(agreementnumber=agreement_id,
                                                                                    transtypedesc__in=['Bi-Annual Management Fee','Bi-Annual Anniversary Fee', 'Annual Management Fee'],
                                                                                    transactiondate=context['transactiondate']
                                                                                    )
        context['bamf'] = round(transaction_detail_extract_bamf.transnetpayment,2)

    except:
        # transaction_detail_extract_bamf = False
        context['bamf'] = '0.00'

    try:
        transaction_detail_extract_docfee = go_account_transaction_detail.objects.get(agreementnumber=agreement_id,
                                                                                    transtypedesc='Documentation Fee',
                                                                                    transactiondate=context[
                                                                                        'transactiondate']
                                                                                    )
        context['docfee'] = round(transaction_detail_extract_docfee.transnetpayment, 2)

    except:
        context['docfee'] = '0.00'

    try:
        transaction_detail_extract_docfee2 = go_account_transaction_detail.objects.get(agreementnumber=agreement_id,
                                                                                    transtypedesc='Documentation Fee 2',
                                                                                    transactiondate=context[
                                                                                        'transactiondate']
                                                                                    )
        context['docfee2'] = round(transaction_detail_extract_docfee2.transnetpayment, 2)

    except:
        context['docfee2'] = '0.00'

    if request.method == 'POST':
        submit_type = request.POST.get('submit_type')
        if submit_type == 'single':
            change_single_value_function(request, agreement_id)
        if submit_type == 'future':
            change_future_values_function(request, agreement_id)

        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        return redirect(url + '?change_profile=1')
    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def modalsettlement(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    template_name = 'includes/modalsettlement.html'

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)

    if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
        if request.method == 'POST':
            return redirect('core_agreement_crud:agreement_management_tab4', agreement_id)
        else:
            return JsonResponse({'redirect': True})

    # Card 68 Settlement Work Package #

    residual_date = agreement_detail.agreementresidualdate
    dt = residual_date
    day_agreement_calls = dt.day
    max_date = day_agreement_calls + 2
    min_date = day_agreement_calls - 6
    if datetime.date.today().day < max_date and datetime.date.today().day > min_date:
        context['in_payment_cycle'] = True

    transaction_summary_dates = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                              transactionsourceid__in=['GO1', 'SP1'],
                                                                              transactiondate__gte=agreement_detail.agreementfirstpaymentdate)
    infodataset = []
    for row3 in transaction_summary_dates:
        infodataset.append(row3.transactiondate)

    not_required_dates = []
    dd_call_dates = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                  transactiondate__in=infodataset,
                                                                  transtypeid__in=['12'])
    for row2 in dd_call_dates:
        not_required_dates.append(row2.transactiondate)

    transaction_summary_extract_reschedule = go_account_transaction_summary.objects.filter(Q(transactionbatch_id__isnull=True) | Q(transactionbatch_id=''), agreementnumber=agreement_id,transtypeid__in=['0'], transactiondate__gte=agreement_detail.agreementfirstpaymentdate).exclude(
        transactiondate__in=not_required_dates)

    datedataset = []
    for row in transaction_summary_extract_reschedule:
        datedataset.append(row.transactiondate)

    charge_detail = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transactionsourceid='GO1', transtypedesc__isnull=True, transflag='Pay', transactiondate__gt=datetime.datetime.today())
    transaction_summary_extract_reschedule_sec = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transactionsourceid='GO3', transflag='Sec', transactiondate__in=datedataset)
    transaction_detail_extract_reschedule_bamf = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transtypedesc__in=['Bi-Annual Management Fee', 'Bi-Annual Anniversary Fee', 'Annual Management Fee'], transactiondate__gt=datetime.datetime.today())
    transaction_detail_extract_reschedule_risk = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transtypedesc='Risk Fee', transactiondate__gt=datetime.datetime.today())
    transaction_detail_extract_reschedule_doc = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transactiondate__lt=agreement_detail.agreementfirstpaymentdate)
    # TODO: GO#110 - Start
    transaction_detail_extract_reschedule_doc2 = go_account_transaction_detail.objects.filter(agreementnumber=agreement_id, transactiondate__lt=agreement_detail.agreementfirstpaymentdate, transtypedesc='Documentation Fee 2')

    sumriskfee = 0

    if transaction_detail_extract_reschedule_doc:
        doc_figure_queryset = transaction_detail_extract_reschedule_doc.aggregate(Sum('transnetpayment'))
        if transaction_detail_extract_reschedule_doc2:
            doc_figure2_queryset = transaction_detail_extract_reschedule_doc2.aggregate(Sum('transnetpayment'))

            # if agreement_detail.agreementdefname == 'Hire Purchase':
            #     context['doc_figure'] = doc_figure_queryset['transnetpayment__sum']

            if agreement_detail.agreementdefname == 'Hire Purchase':
                context['doc_figure'] = ((doc_figure_queryset['transnetpayment__sum']) * decimal.Decimal(1.2)) + (
                doc_figure2_queryset['transnetpayment__sum'])
            else:
                context['doc_figure'] = ((doc_figure_queryset['transnetpayment__sum']) + (doc_figure2_queryset['transnetpayment__sum'])) * decimal.Decimal(1.2)
        else:
            if agreement_detail.agreementdefname == 'Hire Purchase':
                context['doc_figure'] = ((doc_figure_queryset['transnetpayment__sum']) * decimal.Decimal(1.2))
            else:
                context['doc_figure'] = (doc_figure_queryset['transnetpayment__sum']) * decimal.Decimal(1.2)
        # TODO: GO#110 - End
    else: context['doc_figure'] = 0.00


    for transaction in transaction_detail_extract_reschedule_risk:
        sumriskfee = sumriskfee + round((transaction.transnetpayment) * decimal.Decimal(1.2),2)

    if transaction_summary_extract_reschedule:
        settlement_figure_queryset = transaction_summary_extract_reschedule.aggregate(Sum('transgrosspayment'))
        context['settlement_figure'] = settlement_figure_queryset['transgrosspayment__sum'] + context['doc_figure']

    if transaction_summary_extract_reschedule_sec:
        secondary_figure_queryset = transaction_summary_extract_reschedule_sec.aggregate(Sum('transnetpayment'))
        if agreement_detail.agreementdefname == 'Hire Purchase':
            context['secondary_figure'] = secondary_figure_queryset['transnetpayment__sum']
        else:
            context['secondary_figure'] = (secondary_figure_queryset['transnetpayment__sum']) * decimal.Decimal(1.2)
    else:  context['secondary_figure'] = 0.00

    if transaction_detail_extract_reschedule_bamf:
        bamf_figure_queryset = transaction_detail_extract_reschedule_bamf.aggregate(Sum('transnetpayment'))
        # TODO: GO#110 - Start
        # if agreement_detail.agreementdefname == 'Hire Purchase':
        #     context['bamf_figure'] = bamf_figure_queryset['transnetpayment__sum']
        # else:
        context['bamf_figure'] = (bamf_figure_queryset['transnetpayment__sum']) * decimal.Decimal(1.2)
        # TODO: GO#110 - End
    else:  context['bamf_figure'] = 0.00

    if transaction_detail_extract_reschedule_risk:
        risk_figure_queryset = transaction_detail_extract_reschedule_risk.aggregate(Sum('transnetpayment'))
        # TODO: GO#110 - Start
        # if agreement_detail.agreementdefname == 'Hire Purchase':
        #     context['risk_figure'] = risk_figure_queryset['transnetpayment__sum']
        # else:
        # TODO: GO#110 - End
        context['risk_figure'] = sumriskfee
    else:
        context['risk_figure'] = 0.00

    if transaction_summary_extract_reschedule:
        principal_queryset = transaction_summary_extract_reschedule.aggregate(Sum('transnetpaymentcapital'))
        if agreement_detail.agreementdefname == 'Hire Purchase':
            context['principal_figure'] = (principal_queryset['transnetpaymentcapital__sum'])
        else:
            context['principal_figure'] = (principal_queryset['transnetpaymentcapital__sum']) * decimal.Decimal(1.2)
    else: context['principal_figure'] = 0.00

    if transaction_summary_extract_reschedule:
        charges_queryset = charge_detail.aggregate(Sum('transpayprointerest'))
        if agreement_detail.agreementdefname == 'Hire Purchase':
            context['charges_figure'] = (charges_queryset['transpayprointerest__sum'])
        else:
            if charges_queryset['transpayprointerest__sum']:
                context['charges_figure'] = (charges_queryset['transpayprointerest__sum'])*decimal.Decimal(1.2)
            else:
                context['charges_figure'] = 0.00
    else:   context['charges_figure'] = 0.00

    # Card 68 Settlement Work Package #

    if request.method == 'POST':

        settlement_function(request, agreement_id)
        settlement_documentation_function(request, agreement_id)
        # cancel_ddi_with_datacash(agreement_id, user=None)

        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        return redirect(url + '?change_profile=1')

    context['reason_codes'] = reason_codes.objects.filter(selectable=True)

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def modalglobal_termination(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
               'trans_detail_id': request.GET.get('trans_detail_id')}
    template_name = 'includes/modalglobaltermination.html'

    if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
        if request.method == 'POST':
            return redirect('core_agreement_crud:agreement_management_tab4', agreement_id)
        else:
            return JsonResponse({'redirect': True})

    transaction_summary_extract_reschedule = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)

    settlement_figure_queryset = transaction_summary_extract_reschedule.aggregate(Sum('transgrosspayment'))
    context['settlement_figure'] = settlement_figure_queryset['transgrosspayment__sum']

    if request.method == 'POST':
        global_termination_function(request, agreement_id)
        url = reverse('core_agreement_crud:agreement_management_tab4', args=[agreement_id])
        return redirect(url + '?change_profile=1')

    context['reason_codes'] = reason_codes.objects.filter(selectable=True)

    data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


@login_required(login_url='signin')
def modalconsolidate(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
                'trans_detail_id': request.GET.get('trans_detail_id'), 'number_of_consolidated_agreements': 0}
    template_name = 'includes/modalconsolidate.html'

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)

    if request.method == 'GET':

        if go_id.consolidation_info:

            context['consolidated_agreements'] = []

            for aid in go_id.consolidation_info.split("::"):

                go_id = go_agreement_index.objects.get(agreement_id=aid)
                agreement_detail = go_agreement_querydetail.objects.get(go_id=go_id)

                if agreement_detail.agreementclosedflag_id == 902:
                    status = "CLOSED"

                elif agreement_detail.agreementclosedflag_id == 905:
                    status = "OPEN"

                else:
                    status = "LIVE"

                context['consolidated_agreements'].append({
                    'agreement_id': aid,
                    'customercompany': agreement_detail.customercompany,
                    'paymentsum': go_account_transaction_summary.objects.filter(go_id=go_id).aggregate(
                        Sum('transnetpaymentcapital'))["transnetpaymentcapital__sum"],
                    'status': status
                })

            context['number_of_consolidated_agreements'] = len(context['consolidated_agreements']) + 1

        data['html_form'] = render_to_string(template_name, context, request=request)

    elif request.method == 'POST':

        if DrawDown.objects.filter(status='OPEN', agreement_id=agreement_id).exists():
            raise Exception("This agreement is in an open batch.")

        data = move_consol_amount_function(request, agreement_id)

    elif request.method == 'DELETE':
        pass

    return JsonResponse(data)

@login_required(login_url='signin')
def modalaccountinfo(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id, 'transaction_id': request.GET.get('transaction_id'),
                'trans_detail_id': request.GET.get('trans_detail_id'), 'number_of_consolidated_agreements': 0}
    template_name = 'includes/modalaccountinfo.html'

    go_id = go_agreement_index.objects.get(agreement_id=agreement_id)

    if request.method == 'GET':

        if go_id.consolidation_info:

            context['consolidated_agreements'] = []

            for aid in go_id.consolidation_info.split("::"):

                go_id = go_agreement_index.objects.get(agreement_id=aid)
                agreement_detail = go_agreement_querydetail.objects.get(go_id=go_id)

                if agreement_detail.agreementclosedflag_id == 902:
                    status = "CLOSED"

                elif agreement_detail.agreementclosedflag_id == 905:
                    status = "OPEN"

                else:
                    status = "LIVE"

                context['consolidated_agreements'].append({
                    'agreement_id': aid,
                    'customercompany': agreement_detail.customercompany,
                    'paymentsum': go_account_transaction_summary.objects.filter(go_id=go_id).aggregate(
                        Sum('transnetpaymentcapital'))["transnetpaymentcapital__sum"],
                    'status': status
                })

            context['number_of_consolidated_agreements'] = len(context['consolidated_agreements']) + 1

        data['html_form'] = render_to_string(template_name, context, request=request)


    return JsonResponse(data)


@login_required(login_url='signin')
def agreement_detail(request, agreement_id):

    agreement_id_to_consolidate = request.GET.get('agreement_id')

    context = {}

    try:

        if agreement_id_to_consolidate == agreement_id:
            context['error'] = 'Cannot conslidate agreement into itself'

        if not context.get('error'):
            go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
            if go_id.consolidation_info:
                if agreement_id_to_consolidate in go_id.consolidation_info:
                    context['error'] = 'Agreement already conslidated into this agreement.'
        #
        # if not context.get('error'):
        #     agreement_query = go_agreement_querydetail.objects.get(agreementnumber=agreement_id_to_consolidate)
        #     if str(agreement_query.agreementclosedflag_id) == '905':
        #         context['error'] = 'Agreement Not Complete'
        #     if str(agreement_query.agreementclosedflag_id) == '902':
        #         context['error'] = 'Agreement Not Complete'

        if not context.get('error'):

            go_id = go_agreement_index.objects.get(agreement_id=agreement_id_to_consolidate)
            agreement_detail = go_agreement_querydetail.objects.get(go_id=go_id)

            if agreement_detail.agreementclosedflag_id == 902:
                status = "CLOSED"
                context['error'] = 'Agreement Closed'

            elif agreement_detail.agreementclosedflag_id == 901:
                status = "LIVE"

            else:
                status = "OPEN"
                context['error'] = 'Agreement Not Complete'

        if not context.get('error'):
            context = {
                'customercompany': agreement_detail.customercompany,
                'paymentsum': go_account_transaction_summary.objects.filter(go_id=go_id).aggregate(Sum('transnetpaymentcapital'))["transnetpaymentcapital__sum"],
                'status': status,
                'batches': '',
                'success': True
            }

        # Check if in a batch
        # dd_filter = DrawDown.objects.filter(status='OPEN', agreement_no=agreement_id)
        # if dd_filter.exists():
        #     context['batches'] = []
        #     for row in dd_filter:
        #         context['batches'].append({
        #             'agreement_no': agreement_id,
        #         })

    except Exception as e:
        raise e

    return JsonResponse(context)

#  Card 43 CRU-131 – Settlement Document – remove underlines, format the date as a number (commas) and remove italicas, VAT should be in capitals, “Your Account” should read “Your account”, “Shown below subject” should read “shown below, subject”, could you make the URL in Fair Processing Notice look like a URL (underlines and closer together), account number show as a straight 8 characer number, remove spaces from sort code, settlement value at bottom formatted, agreement should not be capital
@login_required(login_url='signin')
def print_pdf_EARLY_SETTLEMENT(request, agreement_id):

    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer,
                               rightMargin=50,
                               leftMargin=50,
                               topMargin=20,
                               bottomMargin=50
                               )
    flowables = []

    sample_style_sheet = getSampleStyleSheet()
    sample_style_sheet.list()

    agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=agreement_id)
    agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
    account_summary = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id)
    if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
        agreement_type = 'Lease'
        sales_tax_rate = 1.2
    else:
        agreement_type = 'HP'
        sales_tax_rate = 1.0

    settlement_figure_queryset = account_summary.aggregate(Sum('transnetpayment'))
    settlement_figure = settlement_figure_queryset['transnetpayment__sum']
    settlement_figure_queryset_gross = account_summary.aggregate(Sum('transgrosspayment'))
    settlement_figure_gross = settlement_figure_queryset_gross['transgrosspayment__sum']
    if agreement_type == 'Lease':
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)
    else:
        settlement_figure_vat = settlement_figure * decimal.Decimal(sales_tax_rate)

    next_rental_date = go_account_transaction_summary.objects.filter(agreementnumber=agreement_id,
                                                                            transactionsourceid__in=['SP1', 'SP2',
                                                                                                     'SP3', 'GO1', 'GO3'],
                                                                            transtypeid__isnull=False,
                                                                            transactiondate__gt=datetime.date.today()).first()
    next = next_rental_date.transactiondate.strftime("%d.%m.%Y")

    paragraph_33 = Paragraph(

        "<u> Early Termination Figure </u>",

        sample_style_sheet['Heading1']
    )
    arrears_total_collected = request.GET.get('arrears_total_collected')

    arrears_total_collected = decimal.Decimal(arrears_total_collected)

    a = Paragraph('''Hire Agreement Number:''', sample_style_sheet['BodyText'])
    b = Paragraph('''Hire Agreement Name:''', sample_style_sheet['BodyText'])
    c = Paragraph('''Goods:''', sample_style_sheet['BodyText'])
    d = Paragraph('''<b>Terminal Settlement Figure:</b>''', sample_style_sheet['BodyText'])
    e = Paragraph("£"+str(format(round(arrears_total_collected, 2), ',')), sample_style_sheet['Heading4'])
    # e = Paragraph("£" + str(format(arrears_total_collected)), sample_style_sheet['Heading4'])
    table3 = [a, agreement_id], \
             [b, agreement_customer.customercompany], \
             [c, "As per schedule NCF01"], \
             [d, e]

    paragraph_4 = Paragraph(
        "In response to your request for a termination figure for agreement " + agreement_id + " we have pleasure in providing the following information. For security purposes the termination details are provided by email and post.If you have not requested this, please contact us immediately."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_5 = Paragraph(

        "Your account details are protected by the Data Protection Act (DPA), so we can only discuss your account with you. We will not discuss details of your account with any other person unless you first give us your express permission to do so. This is to ensure the details about your business remain secure at all times. "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_6 = Paragraph(
        "These types of agreements have huge tax benefits to your business and are not interest only contracts, we are not allowed or permitted to discount over a certain level, however there are no penalties for early termination. This figure has been calculated after taking into account the transactions up to and including todays date and is valid until the date shown below. We are assuming that your bank will not recall any direct debit, standing order and any cheques already received by us will be honoured. The Termination Sum which you will have to pay upon early termination of this agreement will be based upon the remaining total gross rentals shown on the agreement in the Rental payments section as also shown in clause 9 (b). This termination sum represents damages and not a supply of services therefore you will not receive a separate VAT invoice as per clause 9 (d). The total payable below is only valid until the date shown below, subject to the agreement being upto date. "
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_7 = Paragraph(
        "<b>Important - Your Personal Information</b> - We may use your personal information for a variety of purposes and further details of the use of information by us can be found about this and your other rights if you see our Fair Processing Notice at: <u> www.bluerockfinance.co.uk/fair-processing-notice/</u>. We consider that such processing is necessary for our legitimate interests in considering applications and in operating agreements and our business, and it is a requirement of entering into an agreement. You have a right to object to our processing your information on grounds relating to your particular situation."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_8 = Paragraph(
        "If you decide to terminate the agreement early and applying the maximum discount possible, including the notice period, please see below:       "
        ,
        sample_style_sheet['BodyText']
    )

    f = Paragraph("<b>Total Payable for Settlement:</b>", sample_style_sheet['BodyText'])
    h = Paragraph("<b>Valid Until:</b>", sample_style_sheet['BodyText'])
    i = Paragraph(next, sample_style_sheet['Heading4'])

    table5 = [f, e, h, i],

    j = Paragraph("Bank Name:", sample_style_sheet['BodyText'])
    k = Paragraph("Coutts & Co", sample_style_sheet['BodyText'])
    l = Paragraph("Account No & Sort Code:", sample_style_sheet['BodyText'])
    m = Paragraph("05769981   18-00-02", sample_style_sheet['BodyText'])

    n = Paragraph("Account Name:", sample_style_sheet['BodyText'])
    o = Paragraph("Bluerock Secured Finance", sample_style_sheet['BodyText'])
    p = Paragraph("Reference:", sample_style_sheet['BodyText'])
    q = Paragraph(agreement_id, sample_style_sheet['BodyText'])

    table4 = [j, k, l, m], \
             [n, o, p, q]

    paragraph_11 = Paragraph(
        "We offer a new business discount for further finance taken out prior to the valid until date shown above. If you would like to discuss the end of hire options & requirements, then please contact your broker."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_12 = Paragraph(
        "We would like to take this opportunity to thank you for using Bluerock Secured Finance Ltd and wish you "
        "and your business every success in the future."
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_125 = Paragraph(
        "",
        sample_style_sheet['BodyText']
    )

    paragraph_13 = Paragraph(
        " Yours faithfully,"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_14 = Paragraph(
        "Alan Richards"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_15 = Paragraph(
        " Customer Services"
        ,
        sample_style_sheet['BodyText']
    )
    paragraph_16 = Paragraph(

        " VAT Reg No. 974 594073 | Authorised & Regulated by the Financial Conduct Authority Firm Ref No: 729205 | Company Reg No. 06944649."
        ,

        sample_style_sheet['Heading6']
    )

    im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
    im.hAlign = 'RIGHT'

    if agreement_customer.customeraddress1:
        address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
    else:
        address1 = ''
    if agreement_customer.customeraddress2:
        address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
    else:
        address2 = ''
    if agreement_customer.customeraddress3:
        address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
    else:
        address3 = ''
    if agreement_customer.customeraddress4:
        address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
    else:
        address4 = ''
    if agreement_customer.customeraddress5:
        address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
    else:
        address5 = ''
    if agreement_customer.customerpostcode:
        postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
    array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
    while ('' in array): array.remove('')
    array.append('')
    array.append('')
    array.append('')
    array.append('')

    data2 = [['', ''],
             [array[0], ''],
             [array[1], ''],
             [array[2], ''],
             [array[3], ''],
             [array[4], ''],
             [array[5], im],
             ]

    t2 = Table(data2, colWidths=247, rowHeights=15)
    t3 = Table(table3, colWidths=247, rowHeights=15, style=[])
    t5 = Table(table5, colWidths=99, rowHeights=18, style=[])
    t4 = Table(table4, colWidths=120, rowHeights=15, style=[])

    t4._argW[0] = 1.2 * inch
    t4._argW[1] = 2 * inch
    t4._argW[2] = 1.9 * inch
    t4._argW[3] = 1.8 * inch

    t5._argW[0] = 2.4 * inch
    t5._argW[1] = 1.5 * inch
    t5._argW[2] = 1.5 * inch
    t5._argW[3] = 1.5 * inch

    flowables.append(t2)
    flowables.append(paragraph_33)
    flowables.append(t3)
    flowables.append(paragraph_4)
    flowables.append(paragraph_5)
    flowables.append(paragraph_6)
    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(t5)
    flowables.append(t4)
    flowables.append(paragraph_11)
    flowables.append(paragraph_12)
    flowables.append(paragraph_13)
    flowables.append(paragraph_125)
    flowables.append(paragraph_125)
    flowables.append(paragraph_125)
    flowables.append(paragraph_14)
    flowables.append(paragraph_15)
    flowables.append(paragraph_16)

    my_doc.build(flowables)

    pdf_EARLY_SETTLEMENT_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = HttpResponse(content_type='application.pdf')

    filename = 'Apellio ' + agreement_id + " Early Settlement Figure"

    response['Content-Disposition'] = "attachment; filename=%s.pdf" % filename

    response.write(pdf_EARLY_SETTLEMENT_value)
    return response



@login_required(login_url='signin')
def remove_consolidation_agreement(request, agreement_id):

    agreement_id_to_remove = request.GET.get('agreement_id_to_remove')
    number_of_consolidations = 0

    if request.method == 'POST':

        try:
            go_id = go_agreement_index.objects.get(agreement_id=agreement_id)
            if go_id.consolidation_info:
                consolidated_agreements = go_id.consolidation_info.split("::")
                new_consolidated_agreements = []
                for aid in consolidated_agreements:
                    if not agreement_id_to_remove == aid:
                        new_consolidated_agreements.append(aid)
                go_id.consolidation_info = "::".join(new_consolidated_agreements)
                number_of_consolidations = len(new_consolidated_agreements)
                go_id.save()
        except Exception as e:
            pass

    return JsonResponse({'success': True, 'number_of_consolidations': number_of_consolidations})

