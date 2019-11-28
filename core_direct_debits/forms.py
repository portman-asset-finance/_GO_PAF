import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import DDHistory


class DirectDebitForm(forms.ModelForm):

    class Meta:
        model = DDHistory
        fields = ('reference', 'account_name', 'sort_code', 'account_number')

    def clean_reference(self):
        """
        Validates the reference field.
        :return:
        """

        ref = self.cleaned_data['reference']

        tmp_ref = re.sub(r'\W+', '', ref)  # strip out all characters that aren't alphanumeric and _
        tmp_ref = re.sub(r'_', '', tmp_ref)  # strip out any underscores

        if len(tmp_ref) < 6:
            raise ValidationError(_('Reference must have at least 6 alphanumeric characters.'))

        if re.search(r'\\s', ref):
            raise ValidationError(_('Reference must not contain spaces.'))

        return ref

    def clean_sort_code(self):
        """
        Validates the sort code
        :return:
        """

        sort_code = self.cleaned_data['sort_code']

        if not re.search(r'^\d+$', sort_code):
            raise ValidationError(_('Sort code must be digits only.'))

        if len(sort_code) != 6:
            raise ValidationError(_('Sort code must be 6 digits long.'))

        return sort_code

    def clean_account_number(self):
        """
        Validates the account number
        :return:
        """

        account_number = self.cleaned_data['account_number']

        if not re.search(r'^\d+$', account_number):
            raise ValidationError(_('Account number must be digits only.'))

        if len(account_number) != 8:
            raise ValidationError(_('Account number must be 8 digits long.'))

        return account_number


