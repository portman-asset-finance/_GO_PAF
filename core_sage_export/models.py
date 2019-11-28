from django.db import models
from django.contrib.auth.models import User

from core_dd_drawdowns.models import BatchHeaders


class SageBatchHeaders(models.Model):

    STATUS = (
        ('NOT RECORDED', 'NOT RECORDED'),
        ('NOT RECORDED', 'NOT RECORDED'),
        ('RECORDED', 'RECORDED'),
    )

    batch_header = models.ForeignKey(BatchHeaders, on_delete=models.DO_NOTHING, null=True, to_field='reference')
    sage_batch_ref = models.CharField(max_length=50, null=True, blank=True, unique=True)
    sage_batch_type = models.CharField(max_length=50, null=True, blank=True)
    total_debit_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    total_credit_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=20, null=True)
    processed = models.DateTimeField(null=True)
    processing = models.NullBooleanField(default=False)
    created = models.DateField(auto_now_add=True, null=True)
    updated = models.DateField(auto_now=True, null=True)
    sage_batch_date = models.DateTimeField(null=True)
    save_the_click = models.NullBooleanField(default=True)

    class Meta:
        db_table = 'core_sage_batch_headers'


class SageBatchDetails(models.Model):

    transactionsourceid = models.CharField(max_length=50, null=True, blank=True, unique=True)
    transactionsourcedesc = models.CharField(max_length=50, null=True, blank=True, unique=True)
    sage_batch_agreementdefname = models.CharField(max_length=50, null=True, blank=True, unique=True)
    sage_batch_typedesc = models.CharField(max_length=50, null=True, blank=True, unique=True)
    type = models.CharField(max_length=10, null=True, blank=True, unique=True)
    account_reference = models.CharField(max_length=10, null=True, blank=True, unique=True)
    nominal_account_ref = models.CharField(max_length=10, null=True, blank=True, unique=True)
    sage_batch_details = models.CharField(max_length=50, null=True, blank=True, unique=True)
    tax_code = models.CharField(max_length=10, null=True, blank=True, unique=True)
    sage_batch_type = models.CharField(max_length=10, null=True, blank=True, unique=True)
    batch_detail_total = models.CharField(max_length=10, null=True, blank=True, unique=True)
    sage_batch_ref_id  = models.CharField(max_length=10, null=True, blank=True, unique=True)

    class Meta:
        db_table = '_GO_Sage_detail_Extract'

    # sage_batch_detail_id = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # department_code = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # date = models.DateTimeField(null=True, blank=True)
    # reference = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # extra_reference = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # user_name = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # project_ref = models.CharField(max_length=10, null=True, blank=True, unique=True)
    # cost_code_ref = models.CharField(max_length=10, null=True, blank=True, unique=True)





class SageBatchTransactions(models.Model):
    sage_batch_transaction_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    # go_id = models.ForeignKey('go_agreement_index', max_length=50, null=True, on_delete=models.DO_NOTHING)
    agreementnumber = models.CharField(max_length=10, null=True, default='')
    transactiondate = models.DateTimeField(blank=True, null=True)
    transactionsourceid = models.CharField(max_length=10)
    transactionsourcedesc = models.CharField(max_length=20, blank=True, null=True)
    # sage_batch_typeid = models.SmallIntegerField(blank=True, null=True)
    sage_batch_typedesc = models.CharField(max_length=30, blank=True, null=True)
    # transflag = models.CharField(max_length=3, blank=True, null=True)
    # transfallendue = models.NullBooleanField(blank=True, null=True)
    sage_batch_netpayment = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    # transgrosspayment = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    # transrunningtotal = models.DecimalField(max_digits=19, decimal_places=4, blank=True,  null=True)
    # transagreementcustomernumber = models.ForeignKey('go_customers', max_length=10, blank=True, null=True, to_field="customernumber", on_delete=models.CASCADE)  # Field name made lowercase.
    sage_batch_customercompany = models.CharField(max_length=60, blank=True, null=True)  # Field name made lowercase.
    # transagreementclosedflag = models.ForeignKey('core.ncf_applicationwide_text', on_delete=models.CASCADE, blank=True, null=True, to_field="app_text_code")
    # transagreementddstatus = models.ForeignKey('core.ncf_dd_status_text', on_delete=models.CASCADE, blank=True, null=True, to_field="dd_text_code")
    # transagreementcloseddate = models.DateTimeField(blank=True, null=True)
    sage_batch_agreementdefname = models.CharField(max_length=200, blank=True, null=True)  # Field name made lowercase.
    # transagreementagreementdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    # transddpayment = models.NullBooleanField(default=True, blank=True, null=True)
    # transagreementauthority = models.CharField(max_length=30, blank=True, null=True)  # Field name made lowercase.
    # transnetpaymentinterest = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    # transnetpaymentcapital = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    # transactionbatch_id = models.CharField(max_length=15, null=True, default='')
    sage_batch_ref = models.ForeignKey(SageBatchHeaders, on_delete=models.DO_NOTHING, to_field='sage_batch_ref',blank=True,null=True)
    include = models.NullBooleanField(default=True)
    remove = models.NullBooleanField(default=False)

    class Meta:
        db_table = 'core_sage_batch_transactions'


class SageDependencyTable(models.Model):
    agreement_type = models.CharField(max_length=50, null=True, blank=True)
    sage_transaction_type = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    account_reference = models.CharField(max_length=50, null=True, blank=True)
    nominal_account_ref = models.CharField(max_length=50, null=True, blank=True)
    sage_batch_details = models.CharField(max_length=50, null=True, blank=True)
    tax_code = models.CharField(max_length=50, null=True, blank=True)
    sage_batch_type = models.CharField(max_length=50, null=True, blank=True)
    agreement_phase = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'core_sage_dependency_table'


class SageBatchLock(models.Model):
    session_id = models.CharField(max_length=36, null=True)
    sage_batch_header = models.ForeignKey(SageBatchHeaders, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    released = models.DateTimeField(null=True)
