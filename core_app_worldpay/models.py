from django.db import models
from django.contrib.auth.models import User
import datetime

class Collection_WorldPay(models.Model):
    #collection_id = models.CharField(max_length=50,default="")
    collection_number = models.CharField(max_length=50, default="")
    agreement_number = models.CharField(max_length=50, default="")
    #collection_amount = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    collection_quantity = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    #django_user_id = models.CharField(max_length=50)
    user_name = models.CharField(max_length=50, default="")
    created_on = models.DateTimeField(null=True)
    allocated = models.BooleanField(null=False, default=False)
