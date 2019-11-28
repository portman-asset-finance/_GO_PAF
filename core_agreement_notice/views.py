from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .forms import NoticeForm
from .models import Notice
from .filters import AnchorimportAgreement_QueryDetail_Filter, Notice_Filter

from anchorimport.models import AnchorimportAgreement_QueryDetail, \
                                AnchorimportCustomers, \
                                AnchorimportAccountTransactionSummary, \
                                AnchorimportAccountTransactionDetail


def update_or_create(request, agreement_id):

    data = {}
    context = {'agreement_id': agreement_id}
    template_name = 'includes/partial_notice_update_or_create.html'

    try:
        notice = Notice.objects.get(agreement_number=agreement_id)
        context['update_or_create'] = 'Update'
    except:
        notice = False
        context['update_or_create'] = 'Add'

    if request.method == 'POST':

        if notice:
            form = NoticeForm(request.POST, instance=notice)
        else:
            form = NoticeForm(request.POST)

        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
        else:
            data['form_is_valid'] = False

    else:

        if notice:
            form = NoticeForm(instance=notice)
        else:
            form = NoticeForm()

        context['form'] = form

        form.fields['agreement_number'].initial = agreement_id
        form.fields['agreement_number'].widget.attrs['readonly'] = True

        data['html_form'] = render_to_string(template_name, context, request=request)

    return JsonResponse(data)


def notice_list(request):#, agreement_id):
    notices = Notice.objects.all().order_by('-agreement_number')

   # return render(request, 'core_agreement_notice/notice_list.html', {'notice_list': notices})
    #agreement_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=agreement_id)
    #notice_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=agreement_id) \
    #    .order_by('agreementnumber')
    notice_list = Notice_Filter(request.GET, queryset=notices)
    paginator = Paginator(notice_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreement_number') #or request.GET.get('customercompany') \
                 #or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')
    return render(request, 'core_agreement_notice/notice_list.html', {#'notice_within_agreement': notices,
                                                                       'notice_list': notice_list,
                                                                       'notice_list_qs': pub,
                                                                       'has_filter': has_filter
                                                                       })


def notice_within_agreement(request, agreement_id):
    notices = Notice.objects.all().order_by('-agreement_number')
    notice_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=agreement_id)

   # notice_extract = AnchorimportAgreement_QueryDetail.objects.all()



    notice_list = Notice_Filter(request.GET, queryset=notices)
    paginator = Paginator(notice_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)
    has_filter = request.GET.get('agreementnumber') #or request.GET.get('customercompany') \
                 #or request.GET.get('agreementclosedflag') or request.GET.get('agreementddstatus')
    return render(request, 'core_agreement_notice/notice_within_agreement.html', {'notice_within_agreement': notices,
                                                                       'notice_detail': notice_detail,
                                                                       #'notice_list': notice_list,
                                                                       'notice_list_qs': pub,
                                                                       'has_filter': has_filter
                                                                       })


def save_notice_form(request, form, template_name, agid=None):
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            notices = Notice.objects.all()
            data['html_notice_list'] = render_to_string('includes/partial_notice_list.html', {
                'notice_list': notices
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form, 'agreement_id': agid}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)


def notice_create(request, agreement_id):
    #from .. import path
    #core_agreement_notice/notice_within_agreement
   # notice_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber)
    # notice_detail = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=agreement_id)

    if request.method == 'POST':
        form = NoticeForm(request.POST)
    else:
        form = NoticeForm()

    form.fields['agreement_number'].initial = agreement_id
    # form.fields['agreement_number'].disabled = agreement_id

    return save_notice_form(request, form, 'includes/partial_notice_create.html')


def notice_create_list(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
    else:
        form = NoticeForm()
    return save_notice_form(request, form, 'includes/partial_notice_create.html')


def notice_update(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
    else:
        form = NoticeForm(instance=notice)
    return save_notice_form(request, form, 'includes/partial_notice_update.html')


def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    data = dict()
    if request.method == 'POST':
        notice.delete()
        data['form_is_valid'] = True  # This is just to play along with the existing code
        notices = notice.objects.all()
        data['html_notice_list'] = render_to_string('includes/partial_notice_list.html', {
            'notice_list': notices
        })
    else:
        context = {'notice': notice}
        data['html_form'] = render_to_string('includes/partial_notice_delete.html',
            context,
            request=request,
        )
    return JsonResponse(data)
