from django import template
from django.contrib.auth.models import Group
import re
register = template.Library()

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
