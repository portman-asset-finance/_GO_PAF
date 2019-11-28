from django.db import models
from django.contrib.auth.models import User

from core.models import ncf_collection_agents


# Receipts
class receipt_allocations_by_agreement (models.Model):
    rag_agreement_id = models.CharField(max_length=50, blank=True, null=True)
    rag_customernumber = models.CharField(max_length=10, blank=True, null=True)
    rag_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    rag_received_count = models.IntegerField(blank=True, null=True)
    rag_received_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_received_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_received_last_date = models.DateField(blank=True, null=True)
    rag_allocated_count = models.IntegerField(blank=True, null=True)
    rag_allocated_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_allocated_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_allocated_last_date = models.DateField(blank=True, null=True)
    rag_unallocated_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_unallocated_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rag_unallocated_last_date = models.DateField(blank=True, null=True)
    rag_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    rag_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    rag_status_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('rag_agreement_id',)
        verbose_name = 'Receipts Summary at Agreement Level'
        verbose_name_plural = 'Receipts Summary at Agreement Level'

    def __str__(self):
        return '{}'.format(self.rag_agreement_id)


class receipt_allocations_by_arrears (models.Model):
    ras_agreement_id = models.CharField(max_length=50)
    ras_customernumber = models.CharField(max_length=10, blank=True, null=True)
    ras_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    ras_effective_date = models.DateTimeField(blank=True, null=True)
    ras_due_date = models.DateTimeField(blank=True, null=True)
    ras_transactionsourceid = models.CharField(max_length=10, blank=True, null=True)
    ras_reference = models.CharField(max_length=50, blank=True, null=True)
    ras_referencestrip = models.CharField(max_length=50, blank=True, null=True)
    ras_return_description = models.CharField(max_length=500, blank=True, null=True)
    ras_arrears_id = models.IntegerField(blank=True, null=True)
    ras_allocation_id = models.IntegerField(blank=True, null=True)
    ras_arrears_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_arrears_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_collected_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_collected_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_adjustment_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_adjustment_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_balance_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_balance_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ras_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ras_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    ras_status_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('ras_agreement_id',)
        verbose_name = 'Receipts Summary at Arrear Level'
        verbose_name_plural = 'Receipts Summaries at Arrear Level'

    def __str__(self):
        return '{}'.format(self.ras_agreement_id)


class receipt_allocations_by_detail (models.Model):
    rad_agreement_id = models.CharField(max_length=50)
    rad_customernumber = models.CharField(max_length=10, blank=True, null=True)
    rad_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    rad_effective_date = models.DateTimeField(blank=True, null=True)
    rad_due_date = models.DateTimeField(blank=True, null=True)
    rad_reference = models.CharField(max_length=50, blank=True, null=True)
    rad_referencestrip = models.CharField(max_length=50, blank=True, null=True)
    rad_arrears_id = models.IntegerField(blank=True, null=True)
    rad_allocation_id = models.IntegerField(blank=True, null=True)
    rad_allocation_charge_type = models.ForeignKey('arrears_allocation_type', null=True, blank=True,
                                                on_delete=models.SET_NULL)
    rad_arrears_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_arrears_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_collected_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_collected_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_adjustment_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_adjustment_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_balance_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_balance_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rad_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    rad_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    rad_status_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('rad_agreement_id',)
        verbose_name = 'Receipts Allocations at Detail Level'
        verbose_name_plural = 'Receipts Allocations at Detail Level'

    def __str__(self):
        return '{}'.format(self.rad_agreement_id)


# Arrears
class arrears_summary_agreement_level(models.Model):
    arr_agreement_id = models.CharField(max_length=50, blank=True, null=True)
    arr_customernumber = models.CharField(max_length=10, blank=True, null=True)
    arr_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    arr_arrears_count = models.IntegerField(blank=True, null=True)
    arr_arrears_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_arrears_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_arrears_last_date = models.DateField(blank=True, null=True)
    arr_collected_count = models.IntegerField(blank=True, null=True)
    arr_collected_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_collected_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_collected_last_date = models.DateField(blank=True, null=True)
    arr_writtenoff_count = models.IntegerField(blank=True, null=True)
    arr_writtenoff_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_writtenoff_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_writtenoff_last_date = models.DateField(blank=True, null=True)
    arr_balance_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_balance_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_balance_last_date = models.DateField(blank=True, null=True)
    arr_unallocated_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_unallocated_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_unallocated_last_date = models.DateField(blank=True, null=True)
    arr_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    arr_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    arr_status_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('arr_agreement_id',)
        verbose_name = 'Arrears Summary by Agreement'
        verbose_name_plural = 'Arrears Summaries by Agreement'

    def __str__(self):
        return '{}'.format(self.arr_agreement_id)


class arrears_summary_arrear_level(models.Model):
    ara_agreement_id = models.CharField(max_length=50)
    ara_customernumber = models.CharField(max_length=10, blank=True, null=True)
    ara_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    ara_effective_date = models.DateTimeField(blank=True, null=True)
    ara_due_date = models.DateTimeField(blank=True, null=True)
    ara_transactionsourceid = models.CharField(max_length=10, blank=True, null=True)
    ara_reference = models.CharField(max_length=50, blank=True, null=True)
    ara_referencestrip = models.CharField(max_length=50, blank=True, null=True)
    ara_return_description = models.CharField(max_length=500, blank=True, null=True)
    ara_arrears_id = models.IntegerField(blank=True, null=True)
    ara_arrears_count = models.IntegerField(blank=True, null=True)
    ara_arrears_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_arrears_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_arrears_last_date = models.DateField(blank=True, null=True)
    ara_collected_count = models.IntegerField(blank=True, null=True)
    ara_collected_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_collected_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_collected_last_date = models.DateField(blank=True, null=True)
    ara_writtenoff_count = models.IntegerField(blank=True, null=True)
    ara_writtenoff_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_writtenoff_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_writtenoff_last_date = models.DateField(blank=True, null=True)
    ara_balance_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_balance_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ara_balance_last_date = models.DateField(blank=True, null=True)
    ara_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ara_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    ara_status_date = models.DateField(blank=True, null=True)
    ara_file_name = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ('ara_agreement_id', '-ara_due_date')
        verbose_name = 'Arrears Summary at Arrear Level'
        verbose_name_plural = 'Arrears Summaries at Arrear Level'

    def __str__(self):
        return '{}'.format(self.ara_agreement_id)


class arrears_detail_arrear_level(models.Model):
    ard_agreement_id = models.CharField(max_length=50)
    ard_customernumber = models.CharField(max_length=10, blank=True, null=True)
    ard_customercompanyname = models.CharField(max_length=60, blank=True, null=True)
    ard_arrears_id = models.IntegerField(blank=True, null=True)
    ard_arrears_charge_type = models.ForeignKey('arrears_allocation_type', null=True, blank=True, on_delete=models.SET_NULL)
    ard_return_description = models.CharField(max_length=500, blank=True, null=True)
    ard_effective_date = models.DateTimeField(blank=True, null=True)
    ard_due_date = models.DateTimeField(blank=True, null=True)
    ard_reference = models.CharField(max_length=50, blank=True, null=True)
    ard_referencestrip = models.CharField(max_length=50, blank=True, null=True)
    ard_arrears_count = models.IntegerField(blank=True, null=True)
    ard_arrears_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_arrears_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_arrears_last_date = models.DateField(blank=True, null=True)
    ard_collected_count = models.IntegerField(blank=True, null=True)
    ard_collected_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_collected_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_collected_last_date = models.DateField(blank=True, null=True)
    ard_writtenoff_count = models.IntegerField(blank=True, null=True)
    ard_writtenoff_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_writtenoff_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_writtenoff_last_date = models.DateField(blank=True, null=True)
    ard_balance_value_netofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_balance_value_grossofvat = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ard_balance_last_date = models.DateField(blank=True, null=True)
    ard_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ard_status = models.ForeignKey('arrears_status', null=True, blank=True, on_delete=models.SET_NULL)
    ard_status_date = models.DateField(blank=True, null=True)
    ard_file_name = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ('ard_agreement_id',)
        verbose_name = 'Arrears Summary at Arrear Level'
        verbose_name_plural = 'Arrears Summaries at Arrear Level'

    def __str__(self):
        return '{}'.format(self.ard_agreement_id)


# Definitions & Codes
class arrears_status(models.Model):
    arr_status_code = models.CharField(max_length=1, unique=True)
    arr_status_description = models.CharField(max_length=100)

    class Meta:
        ordering = ('arr_status_code',)
        verbose_name = 'Arrears Status'
        verbose_name_plural = 'Arrears Statuses'

    def __str__(self):
        return '{}'.format(self.arr_status_description)


class arrears_allocation_type(models.Model):
    arr_allocation_id = models.IntegerField(blank=True, null=True)
    arr_allocation_code = models.CharField(max_length=20, blank=True, null=True)
    arr_allocation_description = models.CharField(max_length=100)
    arr_allocation_src_id = models.CharField(max_length=10, blank=True, null=True)
    arr_allocation_src_type_max = models.SmallIntegerField(null=True)
    arr_allocation_src_type_01 = models.SmallIntegerField(null=True)
    arr_allocation_src_type_02 = models.SmallIntegerField(null=True)
    arr_allocation_value_net = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_allocation_value_gross = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    arr_allocation_applied_auto = models.BooleanField(default=False)
    arr_allocation_status = models.CharField(max_length=1)

    class Meta:
        ordering = ('arr_allocation_code',)
        verbose_name = 'Arrears Allocation Type'
        verbose_name_plural = 'Arrears Allocation Types'

    def __str__(self):
        return '{}'.format(self.arr_allocation_description)


class agent_allocations_control (models.Model):
    aac_agent_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    aac_agent_phase = models.CharField(max_length=10, blank=True, null=True)
    aac_status = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        ordering = ('aac_agent_id',)
        verbose_name = 'Agent Allocation Control'
        verbose_name_plural = 'Agent Allocation Control'

    def __str__(self):
        return '{}'.format(self.aac_agent_id)