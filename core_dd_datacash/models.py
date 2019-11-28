from django.db import models
# Create your models here.
from core_agreement_crud.models import go_funder


class datacash_credentials(models.Model):

    funder = models.ForeignKey(go_funder, blank=True, null=True, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    auth_client = models.CharField( max_length=50, blank=True, null=True)  # Field name made lowercase.
    auth_password = models.CharField( max_length=50, blank=True, null=True)  # Field name made lowercase
    bacs_url = models.CharField( max_length=150, blank=True, null=True)  # Field name made lowercase
    test_auth_client = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    test_auth_password = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase
    test_bacs_url = models.CharField(max_length=150, blank=True, null=True)  # Field name made lowercase

    def __str__(self):
        return '{}'.format(self.funder)