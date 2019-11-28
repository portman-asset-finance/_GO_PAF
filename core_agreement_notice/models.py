from django.db import models

class Notice(models.Model):
    YES = 1
    NO = 2
    YES_NO = (
        (YES, 'Yes'),
        (NO, 'No'),
    )
    agreement_number = models.CharField(max_length=10)
    notice_given = models.PositiveSmallIntegerField(choices=YES_NO)
    notice_date = models.DateField(null=True)
    secondary_date = models.DateField(null=True)


