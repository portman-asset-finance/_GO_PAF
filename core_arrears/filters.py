import datetime
from django.contrib.auth.models import User
from .models import arrears_summary_agreement_level, arrears_summary_arrear_level
from core.models import ncf_dd_schedule

import django_filters


class arrears_summary_agreement_level_Filter(django_filters.FilterSet):
    arr_agreement_id = django_filters.CharFilter(lookup_expr='icontains')
    arr_customercompanyname = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = arrears_summary_agreement_level
        exclude = ['agreementproducttierid']


class arrears_summary_arrear_level_Filter(django_filters.FilterSet):

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

        super(arrears_summary_arrear_level_Filter, self).__init__(data, *args, **kwargs)

    # Get current due date
    initial_default_date_queryset = ncf_dd_schedule.objects.filter(dd_status_id='999')[:1].get()

    ara_agreement_id = django_filters.CharFilter(lookup_expr='icontains')
    ara_customercompanyname = django_filters.CharFilter(lookup_expr='icontains')
    ara_due_date = django_filters.DateFilter()
    ara_agent_id = django_filters.ModelChoiceFilter(queryset=User.objects.filter(groups__name='NCF_Collections_PrimaryAgents'),label=('Assigned'))
    class Meta:
        model = arrears_summary_arrear_level
        exclude = ['agreementproducttierid']