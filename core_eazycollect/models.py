from django.db import models

from core_agreement_crud.models import go_funder, go_customers


NB = {
    'null': True,
    'blank': True
}


class Credentials(models.Model):

    funder = models.ForeignKey(go_funder, on_delete=models.DO_NOTHING)

    url = models.CharField(max_length=250, **NB)

    client_code = models.CharField(max_length=100)

    api_key = models.CharField(max_length=250)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)


class Contracts(models.Model):

    agreement_id = models.CharField(max_length=50, **NB)  # customerRef

    ez_customer_id = models.CharField(max_length=100, **NB)

    ez_contract_id = models.CharField(max_length=100, **NB)

    first_name = models.CharField(max_length=100, **NB)

    last_name = models.CharField(max_length=100, **NB)

    company_name = models.CharField(max_length=100, **NB)

    email = models.CharField(max_length=100, **NB)

    address_line1 = models.CharField(max_length=100, **NB)

    address_line2 = models.CharField(max_length=100, **NB)

    post_code = models.CharField(max_length=15, **NB)

    account_name = models.CharField(max_length=100, **NB)

    account_number = models.CharField(max_length=8, **NB)

    sort_code = models.CharField(max_length=6, **NB)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)


class Payments(models.Model):

    agreement_id = models.CharField(max_length=50, **NB)

    ez_payment_id = models.CharField(max_length=100, **NB)

    ez_contract_id = models.CharField(max_length=100, **NB)

    due_date = models.DateTimeField(**NB)

    amount = models.DecimalField(max_digits=20, decimal_places=2, **NB)

    error = models.TextField(**NB)

    message = models.TextField(**NB)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)


class RequestLog(models.Model):

    HTTP_METHOD_CHOICES = (
        ('GET', 'GET'),
        ('PUT', 'PUT'),
        ('POST', 'POST'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE')
    )

    REQUEST_TYPE_CHOICES = (
        ('payment', 'payment'),
        ('customer', 'customer'),
        ('contract', 'contract'),
    )

    source_id = models.CharField(max_length=100, **NB)

    source_type = models.CharField(max_length=100, **NB)

    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES, **NB)

    http_method = models.CharField(max_length=10, choices=HTTP_METHOD_CHOICES, **NB)

    status_code = models.CharField(max_length=10, **NB)

    url = models.CharField(max_length=250, **NB)

    headers = models.TextField(**NB)

    request = models.TextField(**NB)

    response = models.TextField(**NB)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(**NB)


class BacsIssues(models.Model):

    agreement_id = models.CharField(max_length=50, **NB)

    new_status = models.CharField(max_length=100, **NB)

    object_id = models.CharField(max_length=100, **NB)

    change_date = models.DateTimeField(**NB)

    entity = models.CharField(max_length=100, **NB)

    source = models.CharField(max_length=100, **NB)

    message = models.TextField(**NB)

    comment = models.TextField(**NB)


class CallbackLog(models.Model):

    http_method = models.CharField(max_length=10, **NB)

    body_data = models.TextField(**NB)

    get_data = models.TextField(**NB)

    post_data = models.TextField(**NB)

    meta_data = models.TextField(**NB)

    error = models.TextField(**NB)

    processed = models.NullBooleanField(**NB)

    created = models.DateTimeField(auto_now_add=True, **NB)
