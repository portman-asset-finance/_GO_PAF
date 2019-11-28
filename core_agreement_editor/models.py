from django.db import models
from django.contrib.auth.models import User

class Editor(models.Model):
    YES = 1
    NO = 2
    YES_NO = (
        (YES, 'Yes'),
        (NO, 'No'),
    )
    agreement_number = models.CharField(max_length=10)
    editor_given = models.PositiveSmallIntegerField(choices=YES_NO)
    editor_date = models.DateField(null=True)
    secondary_date = models.DateField(null=True)

class go_settlement(models.Model):

    go_id = models.CharField(max_length=50, null=True)
    agreement_id = models.CharField(max_length=10,null=True)

    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    calculated = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    actuals = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    adjustment = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    description = models.CharField(max_length=50, null=True)
    reason = models.CharField(max_length=50, null=True)
    sent_to_customer = models.CharField(max_length=10, null=True)

    def __str__(self):
        return '{}'.format(self.agreement_id)

class go_editor_history(models.Model):
    go_id = models.CharField(max_length=50, null=True)
    agreement_id = models.CharField(max_length=10, null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    updated = models.DateTimeField(auto_now=True, null=True)
    action = models.CharField(max_length=50, null=True)
    transaction = models.CharField(max_length=50, null=True)
    customercompany = models.CharField(db_column='CustomerCompany', max_length=60, blank=True, null=True)

    class Meta:
        ordering = ('-updated', 'agreement_id')
        verbose_name = 'Go Editor History'
        verbose_name_plural = 'Go Editor Historys'

    def __str__(self):
        return '{}'.format(self.agreement_id)
