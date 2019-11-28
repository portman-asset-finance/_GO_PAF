from django import template
from django.contrib.auth.models import Group
import decimal
import re
import datetime


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
            if a.transgrosspayment:
                sum += float(decimal.Decimal('{0:.2f}'.format(a.transgrosspayment)))
        else:
            break

    return sum


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_icon_for_note_asset(original_file_name):
    """
    File Icons for the notes system.
    """

    base_url = '/static/static_core_notes/icons/'

    # PDF files
    if re.search(r'pdf$', original_file_name):
        return base_url + 'pdf.png'

    # Excel files
    if re.search(r'csv$', original_file_name):
        return base_url + 'excel.png'
    if re.search(r'xls$', original_file_name):
        return base_url + 'excel.png'
    if re.search(r'xlsx$', original_file_name):
        return base_url + 'excel.png'

    # Word files
    if re.search(r'doc$', original_file_name):
        return base_url + 'word.png'
    if re.search(r'docx$', original_file_name):
        return base_url + 'word.png'

    # Image files
    if re.search(r'png$', original_file_name):
        return base_url + 'image.png'
    if re.search(r'gif$', original_file_name):
        return base_url + 'image.png'
    if re.search(r'jpg$', original_file_name):
        return base_url + 'image.png'
    if re.search(r'jpeg$', original_file_name):
        return base_url + 'image.png'

    return base_url + 'file.png'


@register.filter(name='view_truncate')
def view_truncate(in_string, in_length):
    wip_string = str(in_string)
    if len(wip_string) > in_length:
        out_string = wip_string[:in_length] + '...'
    else:
        out_string = wip_string
    return out_string


@register.filter
def has_group(user, group_name):
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False


@register.filter
def is_in_past(date):
    if date < datetime.datetime.now():
        return True
    return False
