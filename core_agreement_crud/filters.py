import datetime
from .models import go_agreement_querydetail, go_account_transaction_summary, go_customers
from core.models import ncf_arrears_summary, ncf_dd_schedule, ncf_ddic_advices
from core_agreement_editor.models import go_editor_history
import django_filters

FILTER_AGREEMENT_STAGE_CHOICES = (
    ('', '- - - - -'),
    ('4','Agreement Live'),
    ('1','Stage 1'),
    ('2','Stage 2'),
    ('3','Stage 3'),


    # ('4','4'),
    # ('5','Live'),
)

FILTER_AGREEMENT_STATUS_CHOICES = (
    ('', '- - - - -'),
    ('901','LIVE'),
    ('902','CLOSED'),

)
FILTER_AGREEMENT_DD_STATUS_CHOICES = (
    ('', '- - - - -'),
    ('A', 'Active DD'),
    ('I', 'Inactive DD'),
)

class agreement_querydetail_Filter(django_filters.FilterSet):
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    customercompany = django_filters.CharFilter(lookup_expr='icontains')
    agreement_stage = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_STAGE_CHOICES)
    agreementclosedflag_id = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_STATUS_CHOICES)
    agreementddstatus_id = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_DD_STATUS_CHOICES)

    class Meta:
        model = go_agreement_querydetail
        exclude = ['agreementproducttierid']

class go_editor_history_Filter(django_filters.FilterSet):
    agreement_id = django_filters.CharFilter(lookup_expr='icontains')
    customercompany = django_filters.CharFilter(lookup_expr='icontains')
    user_id = django_filters.CharFilter(lookup_expr='icontains')
    action = django_filters.CharFilter(lookup_expr='icontains')
    updated = django_filters.DateFilter()

    class Meta:
        model = go_editor_history
        exclude = ['agreementproducttierid']

class customers_Filter(django_filters.FilterSet):
    customernumber = django_filters.CharFilter(lookup_expr='icontains')
    customercompany = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = go_customers
        exclude = ['agreementproducttierid']


FILTER_RENTAL_TYPE_CHOICES = (
    ('Primary', 'Primary'),
    ('Secondary', 'Secondary'),
)

FILTER_AGREEMENT_TYPE_CHOICES = (
    ('Lease Agreement', 'Lease Agreement'),
    ('Hire Purchase', 'Hire Purchase'),
)

class accounttransactionsummary_Filter(django_filters.FilterSet):

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

        super(accounttransactionsummary_Filter, self).__init__(data, *args, **kwargs)

    # Get due date two weeks from now
    today = datetime.date.today()
    targetdate = today + datetime.timedelta(days=21)
    initial_default_date_queryset = ncf_dd_schedule.objects.filter(dd_calendar_due_date__gte=targetdate)[:1].get()
    agreementnumber = django_filters.CharFilter(lookup_expr='icontains')
    transcustomercompany = django_filters.CharFilter(lookup_expr='icontains')
    transactionsourcedesc = django_filters.ChoiceFilter(choices=FILTER_RENTAL_TYPE_CHOICES)
    transagreementdefname = django_filters.ChoiceFilter(choices=FILTER_AGREEMENT_TYPE_CHOICES)
    transactiondate = django_filters.DateFilter(initial=initial_default_date_queryset.dd_calendar_due_date)

    class Meta:
        model = go_account_transaction_summary
        exclude = ['agreementproducttierid']

class ncf_arrears_summary_Filter(django_filters.FilterSet):

    agreementnumber = django_filters.CharFilter(field_name='col_agreement_id__agreementnumber', lookup_expr='icontains')
    customercompany = django_filters.CharFilter(field_name='col_agreement_id__CustomerCompany', lookup_expr='icontains')

    class Meta:
        model = ncf_arrears_summary
        exclude = ['agreementproducttierid']

class ncf_ddic_advices_Filter(django_filters.FilterSet):

    agreementnumber = django_filters.CharFilter(field_name='agreement_id', lookup_expr='icontains')
    customercompany = django_filters.CharFilter(field_name='customercompany', lookup_expr='icontains')

