
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User


class DDHistory(models.Model):

    class Meta:
        db_table = 'core_direct_debits_history'

    # Agreement Number
    agreement_no = models.CharField(db_column='agreement_id', max_length=10)

    # Order/Sequence
    sequence = models.IntegerField(db_column='sequence')

    # our reference
    reference = models.CharField(db_column='reference', max_length=20, null=True, blank=True)

    # provider (ie datacash) reference
    dd_reference = models.CharField(db_column='dd_reference', max_length=50, null=True, blank=True)

    # account name
    account_name = models.CharField(db_column='account_name', max_length=60)

    # sort code
    sort_code = models.CharField(db_column='sort_code', max_length=6)

    # account number
    account_number = models.CharField(db_column='account_number', max_length=8)

    # effective date
    effective_date = models.DateTimeField(db_column='effective_date', null=True)

    # cancelled date
    cancelled_date = models.DateTimeField(db_column='cancelled_date', null=True)

    # valid
    valid = models.NullBooleanField(db_column='dd_valid', default=False, null=True)

    # user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # dd service provider
    PROVIDER_CHOICES = (
        ('datacash', 'datacash'),
        ('eazycollect', 'eazycollect')
    )
    provider = models.CharField(max_length=100, choices=PROVIDER_CHOICES, null=True, blank=True)

    # created
    created = models.DateTimeField(auto_now_add=True)

    # updated
    updated = models.DateTimeField(auto_now=True)


class DDLog(models.Model):

    class Meta:
        db_table = 'core_direct_debits_log'

    # agreement no
    agreement_no = models.CharField(db_column='agreement_id', max_length=10)

    # our reference
    reference = models.CharField(db_column='reference', max_length=20, null=True, blank=True)

    # provider (ie datacash) reference
    dd_reference = models.CharField(db_column='dd_reference', max_length=50, null=True, blank=True)

    # account name
    account_name = models.CharField(db_column='account_name', max_length=60)

    # sort code
    sort_code = models.CharField(db_column='sort_code', max_length=6)

    # account number
    account_number = models.CharField(db_column='account_number', max_length=8)

    # method
    method = models.CharField(db_column='method', max_length=10, choices=(('setup', 'setup'), ('revoke', 'revoke')))

    # success
    success = models.BooleanField(db_column='success')

    # info/reason
    info = models.TextField(db_column='info')

    # request
    request = models.TextField(db_column='request', null=True, blank=True)

    # response
    response = models.TextField(db_column='response', null=True, blank=True)

    # user
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # created
    created = models.DateTimeField(auto_now_add=True)


