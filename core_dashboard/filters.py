import datetime
from anchorimport.models import AnchorimportAgreement_QueryDetail, AnchorimportAccountTransactionSummary
from core_agreement_crud.models import go_agreement_querydetail, go_account_transaction_summary

from core.models import ncf_dd_schedule
import django_filters

FILTER_RENTAL_TYPE_CHOICES = (
    ('', '- - - - -'),
    ('Primary', 'Primary'),
    ('Secondary', 'Secondary'),
)

FILTER_AGREEMENT_TYPE_CHOICES = (
    ('', '- - - - -'),
    ('Lease Agreement', 'Lease Agreement'),
    ('Hire Purchase', 'Hire Purchase'),
)

# GO specific Filters
# ===================
class go_agreement_querydetail_Filter(django_filters.FilterSet):
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    customercompany = django_filters.CharFilter(lookup_expr='icontains')
    agreementauthority = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = go_agreement_querydetail
        exclude = ['agreementproducttierid']


class go_account_transaction_summary_Filter(django_filters.FilterSet):

    def __init__(self, data=None, *args, **kwargs):

        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()
            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super(go_account_transaction_summary_Filter, self).__init__(data, *args, **kwargs)

    # Get due date two weeks from now
    today = datetime.date.today()
    targetdate = today + datetime.timedelta(days=21)
    initial_default_date_queryset = ncf_dd_schedule.objects.filter(dd_calendar_due_date__gte=targetdate)[:1].get()
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    transcustomercompany = django_filters.CharFilter(lookup_expr='icontains')
    agreementauthority = django_filters.CharFilter(lookup_expr='icontains')
    transactionsourcedesc = django_filters.ChoiceFilter(choices=FILTER_RENTAL_TYPE_CHOICES)
    transagreementdefname = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_TYPE_CHOICES)
    transactiondate = django_filters.DateFilter(initial=initial_default_date_queryset.dd_calendar_due_date)

    class Meta:
        model = go_account_transaction_summary
        exclude = ['agreementproducttierid']


# Anchor specific Filters
# =======================
class AnchorimportAgreement_QueryDetail_Filter(django_filters.FilterSet):
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    customercompany = django_filters.CharFilter(lookup_expr='icontains')
    agreementauthority = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = AnchorimportAgreement_QueryDetail
        exclude = ['agreementproducttierid']


class AnchorimportAccountTransactionSummary_Filter(django_filters.FilterSet):

    def __init__(self, data=None, *args, **kwargs):

        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()
            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super(AnchorimportAccountTransactionSummary_Filter, self).__init__(data, *args, **kwargs)

    # Get due date two weeks from now
    today = datetime.date.today()
    targetdate = today + datetime.timedelta(days=21)
    initial_default_date_queryset = ncf_dd_schedule.objects.filter(dd_calendar_due_date__gte=targetdate)[:1].get()
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    transcustomercompany = django_filters.CharFilter(lookup_expr='icontains')
    agreementauthority = django_filters.CharFilter(lookup_expr='icontains')
    transactionsourcedesc = django_filters.ChoiceFilter(choices=FILTER_RENTAL_TYPE_CHOICES)
    transagreementdefname = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_TYPE_CHOICES)
    transactiondate = django_filters.DateFilter(initial=initial_default_date_queryset.dd_calendar_due_date)

    class Meta:
        model = AnchorimportAccountTransactionSummary
        exclude = ['agreementproducttierid']
