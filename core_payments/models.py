from django.db import models
from django.contrib.auth.models import User

class receipt_record(models.Model):
    rr_receipt_id = models.CharField(max_length=50,default="")
    rr_agreement_number = models.CharField(max_length=50, default="")
    rr_receipt_source = models.CharField(max_length=50, default="")
    rr_receipt_source_id = models.CharField(max_length=50, default="")
    rr_receipt_type = models.ForeignKey('receipt_type', to_field='rt_type_code', null=True, blank=True, on_delete=models.SET_NULL)
    rr_receipt_salestax_rate = models.DecimalField(max_digits=2, decimal_places=2, blank=True, null=True)
    rr_receipt_value_net = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    rr_receipt_value_gross = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    rr_receipt_user_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    rr_receipt_created_on = models.DateTimeField(null=True)

    class Meta:
        ordering = ('rr_receipt_id',)
        verbose_name = 'Payment Receipt Record'
        verbose_name_plural = 'Payment Receipt Record'

    def __str__(self):
        return '{}'.format(self.rr_receipt_id)

class receipt_type(models.Model):
    rt_type_code = models.CharField(max_length=10, unique=True)
    rt_type_description = models.CharField(max_length=250, default="", blank=True, null=True)
    rt_type_crdr_flag = models.CharField(max_length=250, default="", blank=True, null=True)
    rt_type_crdr_multiplier = models.IntegerField(blank=True, null=True)


    class Meta:
        ordering = ('rt_type_description',)
        verbose_name = 'Payment Receipt Type'
        verbose_name_plural = 'Payment Receipt Types'

    def __str__(self):
        return '{}'.format(self.rt_type_description)
