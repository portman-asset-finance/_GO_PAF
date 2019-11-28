from django.db import models
from django.contrib.auth.models import User


# BACS File Processing
class ncf_bacs_files_to_process(models.Model):
    network_path_source = models.CharField(max_length=500, blank=True, null=True)
    network_path_archive = models.CharField(max_length=500, blank=True, null=True)
    target_data_format = models.CharField(max_length=10, blank=True, null=True)
    file_type = models.CharField(max_length=10, blank=True, null=True)
    file_identifier = models.CharField(max_length=500, blank=True, null=True)


    class Meta:
        ordering = ('file_identifier',)
        verbose_name = 'BACS File to Process'
        verbose_name_plural = '< 0.01 BACS File Processing Control'

    def __str__(self):
        return '{}'.format(self.file_identifier)


class ncf_bacs_reasons(models.Model):
    reason_code = models.CharField(max_length=1)
    reason_description = models.CharField(max_length=100)

    class Meta:
        ordering = ('reason_code',)
        verbose_name = 'BACS Reason Code'
        verbose_name_plural = '< 1.01 BACS Reason Codes'

    def __str__(self):
        return '{}'.format(self.reason_description)


class ncf_bacs_ddic_reasons(models.Model):
    ddic_reason_code = models.CharField(max_length=1, unique=True)
    ddic_reason_description = models.CharField(max_length=100)

    class Meta:
        ordering = ('ddic_reason_code',)
        verbose_name = 'DDIC Reason Code'
        verbose_name_plural = '< 1.02 BACS DDIC Reason Codes'

    def __str__(self):
        return '{}'.format(self.ddic_reason_description)


class ncf_bacs_files_processed(models.Model):
    file_name = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('file_name',)
        verbose_name = 'BACS File Processed'
        verbose_name_plural = '< 1.03 BACS Files Processed'

    def __str__(self):
        return '{}'.format(self.file_name)


class ncf_auddis_addacs_advices(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    dd_reference = models.CharField(max_length=50, blank=True, null=True)
    dd_payer_name = models.CharField(max_length=500, blank=True, null=True)
    dd_reason_code = models.CharField(max_length=1, blank=True, null=True)
    dd_reason = models.CharField(max_length=500, blank=True, null=True)
    dd_payer_sort_code = models.CharField(max_length=6, blank=True, null=True)
    dd_payer_account_number = models.CharField(max_length=8, blank=True, null=True)
    dd_payer_new_sort_code = models.CharField(max_length=6, blank=True, null=True)
    dd_payer_new_account_number = models.CharField(max_length=8, blank=True, null=True)
    dd_effective_date = models.DateTimeField(blank=True, null=True)
    dd_due_date = models.DateTimeField(blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('dd_reference',)
        verbose_name = 'Auddis/Addacs Advice'
        verbose_name_plural = '< 1.04 BACS AUDDIS/ADDACS Advices'

    def __str__(self):
        return '{}'.format(self.dd_reference)


class ncf_udd_advices(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    dd_reference = models.CharField(max_length=50, blank=True, null=True)
    dd_original_process_date = models.DateTimeField(blank=True, null=True)
    dd_transcode = models.CharField(max_length=2, blank=True, null=True)
    dd_currency = models.CharField(max_length=5, blank=True, null=True)
    dd_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dd_payer_sort_code = models.CharField(max_length=8, blank=True, null=True)
    dd_payer_account_number = models.CharField(max_length=8, blank=True, null=True)
    dd_return_description = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dd_in_arrears_app = models.BooleanField(default=False)

    class Meta:
        ordering = ('dd_reference',)
        verbose_name = 'UDD Advice'
        verbose_name_plural = '< 1.05 BACS UDD Advices'

    def __str__(self):
        return '{}'.format(self.dd_reference)


class ncf_ddic_advices(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    ddic_SUReference = models.CharField(max_length=50, blank=True, null=True)
    ddic_DDIC_Type = models.CharField(max_length=50, blank=True, null=True)
    ddic_seqno = models.CharField(max_length=50, blank=True, null=True)
    ddic_TotalDocumentValue = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ddic_DateOfDocumentDebit = models.DateTimeField(blank=True, null=True)
    ddic_PayingBankReference = models.CharField(max_length=250, blank=True, null=True)
    ddic_Reason = models.ForeignKey('ncf_bacs_ddic_reasons', null=True, blank=True, on_delete=models.SET_NULL)
    ddic_PayerSortCode = models.CharField(max_length=50, blank=True, null=True)
    ddic_PayerName = models.CharField(max_length=250, blank=True, null=True)
    ddic_PayerAccount = models.CharField(max_length=50, blank=True, null=True)
    ddic_TotalAmount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ddic_DateOfOriginalDD = models.DateTimeField(blank=True, null=True)
    ddic_OriginalDDAmount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    customercompany = models.CharField(db_column='CustomerCompany', max_length=60, blank=True, null=True)
    checked_notes = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'BACS DDIC Advice'
        verbose_name_plural = '< 1.06 BACS DDIC Advices'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_dd_audit_log(models.Model):
    da_agreement_id = models.CharField(max_length=50)
    da_effective_date = models.DateTimeField(blank=True, null=True)
    da_due_date = models.DateTimeField(blank=True, null=True)
    da_reference = models.CharField(max_length=50, blank=True, null=True)
    da_referencestrip = models.CharField(max_length=50, blank=True, null=True)
    da_source = models.CharField(max_length=50, blank=True, null=True)
    da_sourcetype = models.CharField(max_length=50, blank=True, null=True)
    da_type = models.CharField(max_length=50, blank=True, null=True)
    da_seqno = models.IntegerField(blank=True, null=True)
    da_reason_type = models.CharField(max_length=1, blank=True, null=True)
    da_reason_code = models.CharField(max_length=20, blank=True, null=True)
    da_reason = models.CharField(max_length=500, blank=True, null=True)
    da_payingbank_reference = models.CharField(max_length=250, blank=True, null=True)
    da_account_name = models.CharField(max_length=500, blank=True, null=True)
    da_payer_sort_code = models.CharField(max_length=15, blank=True, null=True)
    da_payer_account_number = models.CharField(max_length=15, blank=True, null=True)
    da_new_account_name = models.CharField(max_length=500, blank=True, null=True)
    da_payer_new_sort_code = models.CharField(max_length=15, blank=True, null=True)
    da_payer_new_account_number = models.CharField(max_length=15, blank=True, null=True)
    da_original_process_date = models.DateTimeField(blank=True, null=True)
    da_transcode = models.CharField(max_length=2, blank=True, null=True)
    da_currency = models.CharField(max_length=5, blank=True, null=True)
    da_original_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    da_document_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    da_ddic_seqno = models.CharField(max_length=50, blank=True, null=True)
    da_ddic_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    da_ddic_debit_date = models.DateTimeField(blank=True, null=True)
    da_return_description = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    da_created_at = models.DateTimeField()
    da_datacash_stage = models.CharField(max_length=50, blank=True, null=True)
    da_datacash_method = models.CharField(max_length=50, blank=True, null=True)
    da_datacash_batch_status = models.CharField(max_length=50, blank=True, null=True)
    da_datacash_setup_no = models.CharField(max_length=20, blank=True, null=True)
    da_datacash_response = models.CharField(max_length=50, blank=True, null=True)
    da_datacash_bacs_reason = models.CharField(max_length=20, blank=True, null=True)
    da_reporting_date = models.DateTimeField(blank=True, null=True)
    da_reporting_date_set = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        ordering = ('da_agreement_id',)
        verbose_name = 'DD Audit Log Item'
        verbose_name_plural = '< 1.07 BACS DD Audit Log Items'

    def __str__(self):
        return '{}'.format(self.da_agreement_id)


# NCF Excel Imports and Processing
# ================================
class ncf_props_and_payouts(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    regulated_flag = models.CharField(max_length=10, blank=True, null=True)
    payout_date = models.DateField(blank=True, null=True)
    customer_name = models.CharField(max_length=500, blank=True, null=True)
    sales_person = models.CharField(max_length=10, blank=True, null=True)
    rep_person = models.CharField(max_length=10, blank=True, null=True)
    term_text = models.CharField(max_length=10, blank=True, null=True)
    term_mm = models.IntegerField(blank=True, null=True)
    gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    net_invoice_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    net_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    agreement_type = models.CharField(max_length=10, blank=True, null=True)
    first_rental_date = models.DateField(blank=True, null=True)
    final_rental_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'Props & Payouts record'
        verbose_name_plural = '< 0.02 NCF Interface Control'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_settled_agreements(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    agreement_name = models.CharField(max_length=500, blank=True, null=True)
    settlement_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    method = models.CharField(max_length=50, blank=True, null=True)
    settlement_date = models.DateField(blank=True, null=True)
    notes = models.TextField()
    received_from = models.CharField(max_length=500, blank=True, null=True)
    agreement_type = models.CharField(max_length=10, blank=True, null=True)
    vat_status = models.CharField(max_length=10, blank=True, null=True)
    removed_from_sentinel = models.BooleanField(default=False, blank=True)


    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'Settled Agreement'
        verbose_name_plural = '< 2.03 NCF Settled Agreements'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_advanced_payments(models.Model):
    agreement_id = models.CharField(max_length=50, blank=True, null=True)
    agreement_name = models.CharField(max_length=500, blank=True, null=True)
    advance_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    method = models.CharField(max_length=50, blank=True, null=True)
    advance_date = models.DateField(blank=True, null=True)
    notes = models.TextField()

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'Advance Payment'
        verbose_name_plural = '< 2.01 NCF Advance Payments'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_arrears_collected(models.Model):
    ac_collected_date = models.DateField(blank=True, null=True)
    ac_agreement_id = models.CharField(max_length=50)
    ac_agreement_name = models.CharField(max_length=250, blank=True, null=True)
    ac_arrears_collected = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ac_method = models.CharField(max_length=10, blank=True, null=True)
    ac_fees_collected = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ac_agent_name = models.CharField(max_length=50, blank=True, null=True)
    ac_notes = models.TextField(blank=True, null=True)


    class Meta:
        ordering = ('ac_agreement_id',)
        verbose_name = 'Arrears Collected'
        verbose_name_plural = '< 2.02 NCF Arrears Collected'

    def __str__(self):
        return '{}'.format(self.ac_agreement_id)


class ncf_agreement_titles(models.Model):
    agreement_id = models.CharField(max_length=50)
    title_date = models.DateField(null=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=250, blank=True)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    paying_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    proforma = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    method = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'Agreement Title'
        verbose_name_plural = '< 2.04 NCF Agreement Titles'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_global_terminations(models.Model):
    agreement_id = models.CharField(max_length=50)
    agreement_name = models.CharField(max_length=500, blank=True, null=True)
    agreement_rep = models.CharField(max_length=50, blank=True, null=True)
    written_off = models.BooleanField(default=True)
    date_terminated = models.DateField(blank=True, null=True)
    reason = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'Global Termination'
        verbose_name_plural = '< 2.05 NCF Global Terminations'

    def __str__(self):
        return '{}'.format(self.agreement_id)


# DataCash Interface
# ===================
class ncf_datacash_drawdowns(models.Model):
    agreement_id = models.CharField(max_length=50)
    dd_reference = models.CharField(max_length=50)
    dd_setup_no = models.CharField(max_length=20, blank=True, null=True)
    dd_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dd_method = models.CharField(max_length=20, blank=True, null=True)
    dd_request_date = models.DateField(blank=True, null=True)
    dd_batch_status = models.CharField(max_length=20, blank=True, null=True)
    dd_due_date = models.DateField(blank=True, null=True)
    dd_response = models.CharField(max_length=50, blank=True, null=True)
    dd_stage = models.CharField(max_length=20, blank=True, null=True)
    dd_bacs_reason = models.CharField(max_length=20, blank=True, null=True)
    dd_agreement_valid = models.CharField(max_length=1, blank=True, null=True)
    dd_in_arrears_app = models.BooleanField(default=False)
    dd_arrears_flag = models.BooleanField(default=False)

    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'DataCash Drawdown'
        verbose_name_plural = '< 0.03 DataCash Drawdowns'

    def __str__(self):
        return '{}'.format(self.agreement_id)


class ncf_datacash_setups(models.Model):
    agreement_id = models.CharField(max_length=50)
    dd_reference = models.CharField(max_length=50)
    dd_account_name = models.CharField(max_length=250, blank=True, null=True)
    dd_stage = models.CharField(max_length=20, blank=True, null=True)
    dd_method = models.CharField(max_length=10, blank=True, null=True)
    dd_request_date = models.DateTimeField(blank=True, null=True)
    dd_batch_status = models.CharField(max_length=20, blank=True, null=True)
    dd_agreement_valid = models.CharField(max_length=1, blank=True, null=True)


    class Meta:
        ordering = ('agreement_id',)
        verbose_name = 'DataCash Setup'
        verbose_name_plural = '< 3.01 DataCash Setups '

    def __str__(self):
        return '{}'.format(self.agreement_id)


# Bounce Day Processing
# =====================
class ncf_dd_call_control(models.Model):

    dd_call_date = models.DateField(blank=True, null=True)
    dd_due_date = models.DateField(blank=True, null=True)
    dd_bounce_process_date = models.DateField(blank=True, null=True)
    dd_arrears_process_date = models.DateField(blank=True, null=True)
    dd_first_bounce_day = models.BooleanField(default=True)
    dd_bacs_bounce_date01 = models.DateField(blank=True, null=True)
    dd_bacs_bounce_date02 = models.DateField(blank=True, null=True)
    dd_bacs_bounce_date03 = models.DateField(blank=True, null=True)
    dd_bacs_bounce_date04 = models.DateField(blank=True, null=True)
    dd_bacs_bounce_date05 = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('dd_due_date',)
        verbose_name = 'Bounce Day Control'
        verbose_name_plural = '< 0.04 Bounce Day Controls'

    def __str__(self):
        return '{}'.format(self.dd_due_date)


class ncf_dd_call_arrears(models.Model):
    ar_agreement_id = models.CharField(max_length=50)
    ar_account_name = models.CharField(max_length=250, blank=True, null=True)
    ar_salesperson = models.CharField(max_length=50, blank=True, null=True)
    ar_arrears_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_arrears_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_arrears_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_term = models.CharField(max_length=20, blank=True, null=True)
    ar_date = models.DateField(blank=True, null=True)
    ar_days = models.IntegerField(blank=True, null=True)
    ar_notes = models.TextField(blank=True, null=True)
    ar_agent_id = models.ForeignKey('ncf_collection_agents', null=True, blank=True, on_delete=models.SET_NULL)
    ar_agent_name = models.CharField(max_length=50, blank=True, null=True)
    ar_agreement_phase = models.CharField(max_length=50, blank=True, null=True)
    ar_exclude_reason = models.CharField(max_length=50, blank=True, null=True)
    ar_dd_original_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_schedule_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_file_name = models.CharField(max_length=500, blank=True, null=True)
    ar_calendar_due_date = models.DateField(blank=True, null=True)
    ar_uuid = models.UUIDField(blank=True, null=True)
    ar_created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ('ar_agreement_id',)
        verbose_name = 'Bounce Day Arrears'
        verbose_name_plural = '< 4.01 Bounce Day Arrears'

    def __str__(self):
        return '{}'.format(self.ar_agreement_id)


class ncf_dd_call_rejections(models.Model):
    ar_agreement_id = models.CharField(max_length=50)
    ar_account_name = models.CharField(max_length=250, blank=True, null=True)
    ar_salesperson = models.CharField(max_length=50, blank=True, null=True)
    ar_date_cancelled = models.DateField(blank=True, null=True)
    ar_term = models.CharField(max_length=20, blank=True, null=True)
    ar_reason_cancelled = models.CharField(max_length=250, blank=True, null=True)
    ar_days_cancelled = models.IntegerField(blank=True, null=True)
    ar_next_dd_due = models.DateField(blank=True, null=True)
    ar_days_until_dd = models.IntegerField(blank=True, null=True)
    ar_notes = models.TextField(blank=True, null=True)
    ar_agent_id = models.ForeignKey('ncf_collection_agents', null=True, blank=True, on_delete=models.SET_NULL)
    ar_agent_name = models.CharField(max_length=50, blank=True, null=True)
    ar_agreement_phase = models.CharField(max_length=50, blank=True, null=True)
    ar_exclude_reason = models.CharField(max_length=50, blank=True, null=True)
    ar_dd_original_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_schedule_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ar_file_name = models.CharField(max_length=500, blank=True, null=True)
    ar_calendar_due_date = models.DateField(blank=True, null=True)
    ar_created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    ar_uuid = models.UUIDField(blank=True, null=True)

    class Meta:
        ordering = ('ar_agreement_id',)
        verbose_name = 'Bounce Day BACS UDDs'
        verbose_name_plural = '< 4.02 Bounce Day BACS UDDs'

    def __str__(self):
        return '{}'.format(self.ar_agreement_id)


# Arrears and Collections
# =======================
class ncf_arrears_summary(models.Model):
    col_agreement_id = models.CharField(max_length=50, blank=True, null=True)
    col_agent_id = models.ForeignKey('ncf_collection_agents', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_startdate = models.DateField(blank=True, null=True)
    col_arrears_latestdate = models.DateField(blank=True, null=True)
    col_arrears_sum_status = models.ForeignKey('ncf_arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_sum_phase = models.ForeignKey('ncf_arrears_phase', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_sum_changedate = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('col_agreement_id',)
        verbose_name = 'Arrears Summary'
        verbose_name_plural = '< 5.01 Arrears Summaries'

    def __str__(self):
        return '{}'.format(self.col_agreement_id)


class ncf_arrears_summary_uuid_xref(models.Model):
    col_agreement_id = models.ForeignKey('anchorimport.AnchorimportAgreement_QueryDetail',
                                            to_field="agreementnumber", null=True, blank=True,
                                            on_delete=models.SET_NULL)
    col_uuid = models.UUIDField(blank=True, null=True)
    col_uuid_status = models.ForeignKey('ncf_arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    col_uuid_changedate = models.DateField(blank=True, null=True)


class ncf_arrears_detail(models.Model):
    col_agreement_id = models.CharField(max_length=50, blank=True, null=True)
    col_arrears_duedate = models.DateField(blank=True, null=True)
    col_agent_id = models.ForeignKey('ncf_collection_agents', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_startdate = models.DateField(blank=True, null=True)
    col_arrears_latestdate = models.DateField(blank=True, null=True)
    col_arrears_detl_status = models.ForeignKey('ncf_arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_detl_phase = models.ForeignKey('ncf_arrears_phase', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_detl_changedate = models.DateField(blank=True, null=True)
    col_uuid = models.UUIDField(blank=True, null=True)

    class Meta:
        ordering = ('col_agreement_id',)
        verbose_name = 'Arrears Detail'
        verbose_name_plural = 'Arrears Detail'

    def __str__(self):
        return '{}'.format(self.col_agreement_id)


class ncf_arrears_detail_txn(models.Model):
    col_agreement_id = models.CharField(max_length=50, blank=True, null=True)
    col_arrears_duedate = models.DateField(blank=True, null=True)
    col_agent_id = models.ForeignKey('ncf_collection_agents', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_type_id = models.SmallIntegerField(blank=True, null=True)
    col_arrears_type_desc = models.CharField(max_length=30, blank=True, null=True)
    col_arrears_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_collected_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_rental = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_fee = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_outstanding_gross_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    col_arrears_startdate = models.DateField(blank=True, null=True)
    col_arrears_latestdate = models.DateField(blank=True, null=True)
    col_arrears_txn_status = models.ForeignKey('ncf_arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_txn_phase = models.ForeignKey('ncf_arrears_phase', null=True, blank=True, on_delete=models.SET_NULL)
    col_arrears_txn_changedate = models.DateField(blank=True, null=True)
    col_uuid = models.UUIDField(blank=True, null=True)

    class Meta:
        ordering = ('col_agreement_id',)
        verbose_name = 'Arrears Detail Transaction'
        verbose_name_plural = 'Arrears Detail Transactions'

    def __str__(self):
        return '{}'.format(self.col_agreement_id)


class ncf_collection_agents(models.Model):
    bd_collection_agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    bd_agent_primary_manager = models.BooleanField(default=False)
    bd_agent_primary_active = models.BooleanField(default=False)
    bd_agent_secondary_manager = models.BooleanField(default=False)
    bd_agent_secondary_active = models.BooleanField(default=False)

    class Meta:
        ordering = ('bd_collection_agent',)
        verbose_name = 'Bounce Day Collection Agent'
        verbose_name_plural = '< 4.03 Bounce Day Collection Agents'

    def __str__(self):
        return '{}'.format(self.bd_collection_agent)


class ncf_arrears_status(models.Model):
    col_status_code=models.CharField(max_length=5, null=True, blank=True)
    col_status_description=models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ('col_status_description',)
        verbose_name = 'Collection Status'
        verbose_name_plural = '< 5.03 Collection Statuses'

    def __str__(self):
        return '{}'.format(self.col_status_description)


class ncf_arrears_phase(models.Model):
    col_phase_code = models.CharField(max_length=5, null=True, blank=True)
    col_phase_description = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ('col_phase_description',)
        verbose_name = 'Collection Phase'
        verbose_name_plural = 'Collection Phases'

    def __str__(self):
        return '{}'.format(self.col_phase_description)


class ncf_applicationwide_text(models.Model):
    app_text_code = models.IntegerField(unique=True)
    app_text_set = models.IntegerField(null=True, blank=True)
    app_text_description = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ('app_text_description',)
        verbose_name = 'Applicationwide Text Item'
        verbose_name_plural = 'Applicationwide Text Item'

    def __str__(self):
        return '{}'.format(self.app_text_description)


class ncf_dd_status_text(models.Model):
    dd_text_code = models.CharField(max_length=1, null=True, blank=True, unique=True)
    dd_text_set = models.IntegerField(null=True, blank=True)
    dd_text_description = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ('dd_text_description',)
        verbose_name = 'DD Status Text Item'
        verbose_name_plural = 'DD Status Text Items'

    def __str__(self):
        return '{}'.format(self.dd_text_description)


class ncf_dd_schedule(models.Model):
    dd_calendar_due_date = models.DateField()
    dd_working_due_date = models.DateField()
    dd_process_date01 = models.DateField()
    dd_process_date02 = models.DateField()
    dd_bounce_date01 = models.DateField()
    dd_bounce_date02 = models.DateField()
    dd_change_cutoff_date = models.DateField()
    dd_call_date = models.DateField()
    dd_firstbounce_processed = models.BooleanField(default=True)
    dd_status = models.ForeignKey('ncf_dd_schedule_status', on_delete=models.CASCADE,
                                                 blank=True, null=True, default=921,
                                                 to_field="dd_status_text_code")

    class Meta:
        ordering = ('dd_calendar_due_date',)
        verbose_name = 'Bounce Day Control'
        verbose_name_plural = '< 0.05 Bounce Day Controls'

    def __str__(self):
        return '{}'.format(self.dd_calendar_due_date)


class ncf_dd_schedule_status(models.Model):
    dd_status_text_code = models.IntegerField(unique=True)
    dd_status_text_description = models.CharField(max_length=200)

    class Meta:
        ordering = ('dd_status_text_code',)
        verbose_name = 'DD Schedule Status'
        verbose_name_plural = 'DD Schedule Statuses'

    def __str__(self):
        return '{}'.format(self.dd_status_text_description)


# GO Application Management
class go_extensions(models.Model):
    ap_extension_sequence = models.IntegerField(null=True, blank=True)
    ap_extension_code = models.CharField(max_length=10)
    ap_extension_description = models.CharField(max_length=50)
    ap_extension_required_interface_frequency_days = models.IntegerField()
    ap_extension_last_interface_run = models.DateTimeField(null=True, blank=True)
    ap_extension_next_interface_run = models.DateTimeField(null=True, blank=True)
    ap_extension_active = models.BooleanField()

    class Meta:
        ordering = ('ap_extension_sequence',)
        verbose_name = 'GO App Extension'
        verbose_name_plural = '< 0.00 GO App Extensions'

    def __str__(self):
        return '{}'.format(self.ap_extension_description)


class ncf_regulated_agreements(models.Model):
    ra_agreement_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ('ra_agreement_id',)
        verbose_name = 'Regulated Agreements'
        verbose_name_plural = '< 0.06 Regulated Agreements'

    def __str__(self):
        return '{}'.format(self.ra_agreement_id)


class client_configuration(models.Model):

    client_id = models.CharField(max_length=50, null=True, blank=True)
    sales_tax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    other_sales_tax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    prefix = models.CharField(max_length=5, null=True, blank=True)
    customer_number_iteration=models.IntegerField(blank=True, null=True)
    max_tab_create_agreement=models.IntegerField(blank=True, null=True)
    bamf_fee_amount_net = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    bamf_fee_amount_vat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dd_days_before_call=models.IntegerField(blank=True, null=True)
    dd_days_before_drawdown_setup = models.IntegerField(blank=True, null=True)
    pmt_yield = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    pmt_commission = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.client_id)


class holiday_dates(models.Model):
    holiday_date = models.DateField()

    def __str__(self):
        return '{}'.format(self.holiday_date)


class reason_codes(models.Model):
    reason_code = models.CharField(max_length=50, null=True, blank=True)
    reason_text = models.CharField(max_length=50, null=True, blank=True)
    selectable = models.NullBooleanField(default=True)

    def __str__(self):
        return '{}'.format(self.reason_text)


class database_joblog(models.Model):
    job_name = models.CharField(max_length=250, blank=True, null=True)
    job_start_datetime = models.DateTimeField(blank=True, null=True)
    job_end_datetime = models.DateTimeField(blank=True, null=True)
    job_ended = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        ordering = ('job_name',)
        verbose_name = 'Database Joblog'
        verbose_name_plural = 'Database Joblogs'

    def __str__(self):
        return '{}'.format(self.job_name)