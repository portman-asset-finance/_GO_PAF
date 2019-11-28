from django.db import models
from django.contrib.auth.models import User

from core.models import ncf_dd_status_text
from core_direct_debits.models import DDHistory
from core_agreement_crud.models import go_funder


class StatusDefinition(models.Model):

    class Meta:
        db_table = 'core_dd_drawdowns_status_definitions'

    # text code
    choices = (
        ('OPEN', 'OPEN'),
        ('PROCESSING', 'PROCESSING'),
        ('SENT', 'SENT'),
        ('RECEIVED', 'RECEIVED'),
        ('REMOVED', 'REMOVED'),
        ('ARCHIVED', 'ARCHIVED')
    )
    text_code = models.CharField(db_column='text_code', max_length=20, unique=True, choices=choices)

    # text description
    text_description = models.CharField(db_column='text_description', max_length=100)

    # created
    created = models.DateTimeField(auto_now_add=True)

    # updated
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text_code


class BatchHeaders(models.Model):

    class Meta:
        db_table = 'core_dd_drawdowns_batch_headers'

    # batch reference
    reference = models.CharField(db_column='reference', max_length=50, null=True, blank=True, unique=True)

    # total count
    total_count = models.IntegerField(db_column='total_count', null=True, blank=True)

    # total amount
    total_amount = models.DecimalField(db_column='total_amount', max_digits=20, decimal_places=2, null=True, blank=True)

    # due due
    due_date = models.DateField(db_column='due_date', null=True, blank=True)

    # call date
    call_date = models.DateField(db_column='call_date', null=True, blank=True)

    # status
    status = models.ForeignKey(StatusDefinition, max_length=20, to_field='text_code', on_delete=models.DO_NOTHING, null=True)

    # user
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)

    # info
    info = models.CharField(db_column='info', max_length=100, null=True, blank=True)

    # sent datetime
    sent = models.DateTimeField(db_column='sent_date', null=True, blank=True)

    # response datetime
    response = models.DateTimeField(db_column='response_date', null=True, blank=True)

    # sagewisdom processed?
    sagewisdom_processed = models.NullBooleanField(default=False)

    funder = models.ForeignKey(go_funder, on_delete=models.DO_NOTHING, null=True, blank=True)

    # created
    created = models.DateField(auto_now_add=True)


class DrawDown(models.Model):

    class Meta:
        db_table = 'core_dd_drawdowns'

    # agreement id
    agreement_id = models.CharField(db_column='agreement_id', max_length=10)

    # reference
    reference = models.CharField(db_column='reference', max_length=20, null=True, blank=True)

    # dd reference
    dd_reference = models.CharField(db_column='dd_reference', max_length=50, null=True, blank=True)

    # customer name
    customer_name = models.CharField(db_column='customer_name', max_length=60, null=True, blank=True)

    # amount
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    # due date
    due_date = models.DateField(db_column='due_date', null=True, blank=True)

    # sort code
    sort_code = models.CharField(db_column='sort_code', max_length=6, null=True, blank=True)

    # account name
    account_name = models.CharField(db_column='account_name', max_length=60, null=True, blank=True)

    # account number
    account_number = models.CharField(db_column='account_number', max_length=8, null=True, blank=True)

    # agreement type
    agreement_type = models.CharField(db_column='agreement_type', max_length=50, null=True, blank=True)

    # agreement phase
    agreement_phase = models.CharField(db_column='agreement_phase', max_length=50, null=True, blank=True)

    # status
    status = models.ForeignKey(StatusDefinition, max_length=20, null=True, to_field='text_code', on_delete=models.DO_NOTHING)

    # ddi status
    ddi_status = models.ForeignKey(ncf_dd_status_text, on_delete=models.SET_NULL, null=True, to_field='dd_text_code')

    # batch header
    batch_header = models.ForeignKey(BatchHeaders, on_delete=models.CASCADE, null=True, to_field='reference')

    # dd history record (added 18/04/2019)
    # dd_history = models.ForeignKey(DDHistory, null=True, on_delete=models.DO_NOTHING)

    # user
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)

    # agreement source
    agreement_origin_flag = models.CharField(max_length=250, null=True)

    # created
    created = models.DateTimeField(auto_now_add=True)

    # updated
    updated = models.DateTimeField(auto_now=True)

    funder_id = models.CharField(max_length=250, null=True)

    # transaction_summary_unique = models.CharField(max_length=250, null=True)


class SyncDrawdowns(models.Model):

    extract_type = models.CharField(max_length=2, blank=True, null=True)

    extract_count = models.IntegerField(null=True, blank=True)

    batch_reference = models.CharField(max_length=50, null=True, blank=True)

    due_date = models.DateField(null=True, blank=True)

    status_id = models.CharField(max_length=20, null=True, blank=True)

    agreement_id = models.CharField(max_length=10, null=True, blank=True)

    drawdown_batch_ref = models.CharField(max_length=50, null=True, blank=True)

    drawdown_gross_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    drawdown_reference = models.CharField(max_length=50, null=True, blank=True, unique=True)

    drawdown_account_name = models.CharField(max_length=60, null=True, blank=True)

    drawdown_sort_code = models.CharField(max_length=6, null=True, blank=True)

    drawdown_account_number = models.CharField(max_length=8, null=True, blank=True)

    txn_batch_ref = models.CharField(max_length=50, null=True, blank=True)

    txn_gross_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    txn_reference = models.CharField(max_length=50, null=True, blank=True, unique=True)

    txn_account_name = models.CharField(max_length=60, null=True, blank=True)

    txn_sort_code = models.CharField(max_length=6, null=True, blank=True)

    txn_account_number = models.CharField(max_length=8, null=True, blank=True)

    dd_reference = models.CharField(max_length=50, null=True, blank=True)

    funder_id = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '_GO_Drawdown_Merge'


class BatchLock(models.Model):

    session_id = models.CharField(max_length=36, null=True)

    batch_header = models.ForeignKey(BatchHeaders, on_delete=models.DO_NOTHING)

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    created = models.DateTimeField(auto_now_add=True)

    released = models.DateTimeField(null=True)


class Log(models.Model):

    batch_header = models.ForeignKey(BatchHeaders, on_delete=models.DO_NOTHING)

    request = models.TextField(null=True)

    response = models.TextField(null=True)

    request_time = models.DateTimeField(null=True, blank=True)

    response_time = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)


