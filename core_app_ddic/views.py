# Django Imports
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User

from core_notes.models import Note

from core.models import ncf_ddic_advices
from core_agreement_crud.models import go_agreement_querydetail


#JC Step 2.5
from xlsxwriter.workbook import Workbook
import decimal, datetime
import random
from datetime import timedelta

# Python Imports
import decimal, io, datetime, pytz

# Third Party Imports
from dateutil.relativedelta import *
from xlsxwriter.workbook import Workbook
import uuid
import getpass
# from pandas.tseries.holiday import (
#     AbstractHolidayCalendar, DateOffset, EasterMonday,
#     GoodFriday, Holiday, MO,
#     next_monday, next_monday_or_tuesday)
# from pandas.tseries.offsets import CDay


#JC Step 2
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, Frame, BaseDocTemplate, PageTemplate, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from reportlab.pdfgen import canvas

from anchorimport.models import AnchorimportAgreement_QueryDetail, \
                                AnchorimportCustomers, \
                                AnchorimportAccountTransactionSummary, \
                                AnchorimportAccountTransactionDetail

from core.models import ncf_applicationwide_text, \
                        go_extensions, \
                        ncf_dd_schedule, \
                        ncf_datacash_drawdowns, \
                        ncf_dd_audit_log, \
                        ncf_regulated_agreements

from .filters import AnchorimportAgreement_QueryDetail_Filter, \
                     AnchorimportAccountTransactionSummary_Filter, \
                     ncf_arrears_summary_Filter, ncf_ddic_advices_Filter, AnchorimportCustomers_Filter

@login_required(login_url="signin")
def ddic(request):


    ddic_extract = ncf_ddic_advices.objects.filter(ddic_TotalDocumentValue__isnull=False,
                                                   ).order_by('-ddic_DateOfDocumentDebit')

    ddic_list = ncf_ddic_advices_Filter(request.GET, queryset=ddic_extract)

    paginator = Paginator(ddic_list.qs, 10)
    page = request.GET.get('page')
    try:
        pub = paginator.page(page)
    except PageNotAnInteger:
        pub = paginator.page(1)
    except EmptyPage:
        pub = paginator.page(paginator.num_pages)

    has_filter = request.GET.get('agreement_id') or request.GET.get('customercompany') or request.GET.get('checked_notes')
                    # or request.GET.get('transagreementddstatus') or request.GET.get('transactiondate') \
                    # or request.GET.get('transagreementdefname') or request.GET.get('transactionsourcedesc')

    ddic_checked_list = {}
    for row in pub:
        try:
            querydetail_obj = go_agreement_querydetail.objects.get(agreementnumber=row.agreement_id)
            row.customer_id = querydetail_obj.agreementcustomernumber
            print(row.customer_id)
            ddic_checked_list[row.agreement_id] = Note.objects.filter(agreement_id=row.agreement_id,
                                                                      type='DDIC').count()
        except:
            pass

    return render(request, 'core_app_ddic/ddic.html',{'ddic_list':ddic_list,
                                                            'ddic_list_qs':pub,
                                                            'ddic_checked_list': ddic_checked_list,
                                                            'has_filter': has_filter})


@login_required(login_url='signin')
def update_ddic(request):
    context = {}

    print(request.POST['ddic_date'])
    seqno = request.POST['seqno']
    checked = request.POST['checked']
    ddic_type = request.POST['ddic_type']
    ddic_date = request.POST['ddic_date']

    if request.method == 'POST':
        ddic_obj = ncf_ddic_advices.objects.filter(ddic_DDIC_Type=ddic_type, ddic_seqno=seqno, ddic_DateOfOriginalDD=ddic_date )
        ddic_obj.update(checked_notes=checked)

    num1 = ncf_ddic_advices.objects.filter(checked_notes='Unchecked').count()
    num2 = ncf_ddic_advices.objects.filter(checked_notes__isnull=True).count()
    num = num1 + num2

    context = {'count': num}

    return JsonResponse(context)


@login_required(login_url='signin')
def active_ddic(request):

    num1 = ncf_ddic_advices.objects.filter(checked_notes='Unchecked').count()
    num2 = ncf_ddic_advices.objects.filter(checked_notes__isnull=True).count()
    num = num1+num2
    return JsonResponse({'count':num})


