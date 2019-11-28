# Django Imports
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User

from core_companies_house.filters import Company_House_Filter
from core_companies_house.models import CompanyHouse_Changes
from core_notes.models import Note
from core_agreement_crud.models import go_customers, go_agreement_index, go_agreement_querydetail

from core.models import ncf_ddic_advices
from core_agreement_crud.models import go_agreement_querydetail

@login_required(login_url="signin")
def companies_house(request):

    companies_house_extract = CompanyHouse_Changes.objects.filter()

    companies_house_list = Company_House_Filter(request.GET, queryset=companies_house_extract)

    # go_customers_extract = go_customers.objects.filter()

    paginator = Paginator(companies_house_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    has_filter = request.GET.get('company') or request.GET.get('checked') or request.GET.get('ncf_customer_number') \


    # or request.GET.get('transagreementddstatus') or request.GET.get('transactiondate') \
    # or request.GET.get('transagreementdefname') or request.GET.get('transactionsourcedesc')



    companies_house_checked_list = {}
    for row in pub:
        querydetail_obj = CompanyHouse_Changes.objects.get(id=int(row.id))
        row.customer_id = querydetail_obj.company
        # print(row.checked)
        companies_house_checked_list[row.company] = Note.objects.filter(
            # company=row.company,
                                                                  type='companies_house').count()

    return render(request, 'core_companies_house/companies_house.html', {'companies_house_list': companies_house_list,
                                                       'companies_house_list_qs': pub,
                                                       # 'go_customers_extract' : go_customers_extract,
                                                       'companies_house_checked_list': companies_house_checked_list,
                                                       'has_filter': has_filter})
    #
    # return render(request, 'core_companies_house/companies_house.html')

@login_required(login_url='signin')
def update_companies_house(request):
    context = {}

    # print(request.POST['ddic_date'])
    etag = request.POST['etag']
    checked = request.POST['checked']
    # ddic_type = request.POST['ddic_type']
    # ddic_date = request.POST['ddic_date']

    if request.method == 'POST':
        CompanyHouse_Changes_obj = CompanyHouse_Changes.objects.filter(
            etag=etag
            # ddic_DDIC_Type=ddic_type, ddic_seqno=seqno, ddic_DateOfOriginalDD=ddic_date
        )
        CompanyHouse_Changes_obj.update(checked=checked)

    num1 = CompanyHouse_Changes.objects.filter(checked='Unchecked').count()
    num2 = CompanyHouse_Changes.objects.filter(checked__isnull=True).count()
    num = num1 + num2

    context = {'count': num}

    return JsonResponse(context)

@login_required(login_url='signin')
def active_companies_house(request):

    num1 = CompanyHouse_Changes.objects.filter(checked='Unchecked').count()
    num2 = CompanyHouse_Changes.objects.filter(checked__isnull=True).count()
    num = num1+num2
    return JsonResponse({'count':num})

# @login_required(login_url='signin')
# def companies_house(request):
#
#     data = {}
#
#     company_no = request.GET.get('company_no')
#
#     if request.method == 'POST' and company_no:
#
#         # Compare_Company_House_Data(company_no)
#         # company_no
#
#         # data = api_call("COMPANY_PROFILE",company_number=company_no)
#         # data = api_call("REGISTERED_OFFICE_ADDRESS",company_number=company_no)
#         # data = api_call("COMPANY_OFFICERS",company_number=company_no)
#         # data = api_call("CHARGES_LIST",company_number=company_no)
#
#         print(data)
#     return JsonResponse(data)
#
# # from django.shortcuts import render

# Create your views here.
