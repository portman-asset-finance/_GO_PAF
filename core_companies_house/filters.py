import datetime
from anchorimport.models import AnchorimportAgreement_QueryDetail, AnchorimportAccountTransactionSummary, AnchorimportCustomers
from core.models import ncf_arrears_summary, ncf_dd_schedule, ncf_ddic_advices
import django_filters

FILTER_CHECKED = (
    ('Checked', 'Checked'),
    ('Unchecked', 'Unchecked'),
    #(, 'New')
)

class Company_House_Filter(django_filters.FilterSet):

    company = django_filters.CharFilter(lookup_expr='icontains')
    ncf_customer_number = django_filters.CharFilter(lookup_expr='icontains')
    checked = django_filters.ChoiceFilter(choices=FILTER_CHECKED)