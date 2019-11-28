from django import template
from django.contrib.auth.models import Group

import decimal
import re

register = template.Library()

@register.filter(name='running_total_net')
def running_total_net(account_summary, counter ):
    count = 0
    sum = 0
    for a in account_summary:
        count += 1
        if count <= counter:
            sum += a.transnetpayment
        else:
            break

    return sum

@register.filter(name='running_total_gross')
def running_total_gross(account_summary, counter ):
    count = 0
    sum = 0
    for a in account_summary:
        count += 1
        if count <= counter:
            sum += float(decimal.Decimal('{0:.2f}'.format(a.transgrosspayment)))
        else:
            break

    return sum


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False