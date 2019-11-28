from django.db import models
from django.contrib.auth.models import User

NULL = {'null': True}
BLANK = {'blank': True}
NULLBLANK = dict(NULL, **BLANK)


class RequestType(models.Model):

    code = models.CharField(max_length=50)

    description = models.TextField(**NULL)

    HTTP_METHODS = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('HEAD', 'HEAD'),
        ('TRACE', 'TRACE'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
        ('CONNECT', 'CONNECT')
    )
    method = models.CharField(max_length=7, choices=HTTP_METHODS)

    url = models.CharField(max_length=250)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.code)


class RequestParameter(models.Model):

    PARAMETER_TYPES = (
        ('QUERY_STRING', 'QUERY_STRING'),
        ('JSON_KEY_IN_POST_DATA', 'JSON_KEY_IN_POST_DATA'),
    )
    parameter_type = models.CharField(max_length=50, choices=PARAMETER_TYPES, **NULLBLANK)

    parameter_name = models.CharField(max_length=100)

    parameter_key = models.CharField(max_length=100, **NULL)

    parameter_default_value = models.CharField(max_length=250, **NULLBLANK)

    PARAMETER_VALUE_TYPES = (
        ('STRING', 'STRING'),
        ('DECIMAL', 'DECIMAL'),
        ('INTEGER', 'INTEGER'),
        ('DATE', 'DATE'),
        ('TIME', 'TIME')
    )
    parameter_value_type = models.CharField(max_length=10, choices=PARAMETER_VALUE_TYPES, **NULLBLANK)

    parameter_description = models.TextField(**NULLBLANK)

    required = models.NullBooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{}: {} ({})'.format(self.parameter_type, self.parameter_key, self.parameter_name)


class RequestSet(models.Model):

    request_type = models.ForeignKey(RequestType, on_delete=models.DO_NOTHING)

    process_after = models.DateTimeField()

    processed = models.DateTimeField(**NULL)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        str_value = 'Processing after {}'.format(self.process_after)
        if self.processed:
            str_value = 'Processed on {}'.format(self.processed)
        return '{} Request. {}'.format(self.request_type.code, str_value)


class RequestLog(models.Model):

    request_type = models.ForeignKey(RequestType, on_delete=models.DO_NOTHING, **NULL)

    request_set = models.ForeignKey(RequestSet, on_delete=models.DO_NOTHING, **NULL)

    full_url = models.CharField(max_length=250, **NULL)

    status_code = models.CharField(max_length=10)

    response = models.TextField(**NULL)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} Request on {} (STATUS {})'.format(self.request_type, self.created, self.status_code)

class CompanyHouse_CompanyProfile(models.Model):

    registered_office_address_address_line_1 = models.CharField(max_length=50, null = True)
    registered_office_address_address_line_2 = models.CharField(max_length=50, null = True)
    registered_office_address_locality = models.CharField(max_length=50, null = True)
    registered_office_address_region = models.CharField(max_length=50, null = True)
    registered_office_address_postal_code = models.CharField(max_length=50, null = True)

    date_of_creation = models.DateTimeField(null=True)
    company_number = models.CharField(max_length=10)
    last_full_members_list_date = models.DateTimeField(null=True)
    company_name = models.CharField(max_length=50, null = True)
    status = models.CharField(max_length=50, null = True)
    has_been_liquidated = models.CharField(max_length=50, null = True)
    jurisdiction = models.CharField(max_length=50, null = True)
    accounts_next_due = models.DateTimeField(null=True)
    accounts_accounting_reference_date = models.DateTimeField(null=True)
    accounts_next_made_up_to = models.DateTimeField(null=True)
    accounts_next_accounts_period_end_on = models.DateTimeField(null=True)
    accounts_next_accounts_due_on = models.DateTimeField(null=True)
    accounts_next_accounts_period_start_on = models.DateTimeField(null=True)
    accounts_next_accounts_overdue = models.CharField(max_length=50, null = True)
    accounts_overdue = models.CharField(max_length=50, null = True)
    accounts_last_accounts_made_up_to = models.DateTimeField(null=True)
    accounts_last_accounts_type = models.CharField(max_length=50, null = True)
    accounts_last_accounts_period_end_on = models.DateTimeField(null=True)
    accounts_last_accounts_period_start_on = models.DateTimeField(null=True)

    undeliverable_registered_office_address = models.CharField(max_length=50, null = True)
    sic_codes = models.CharField(max_length=50, null = True)
    type = models.CharField(max_length=50, null = True)
    etag = models.CharField(max_length=50, null = True)
    has_insolvency_history = models.CharField(max_length=50, null = True)
    company_status  = models.CharField(max_length=50, null = True)
    has_charges  = models.CharField(max_length=50, null = True)

    confirmation_statement_next_due = models.DateTimeField(null=True)
    confirmation_statement_last_made_up_to = models.DateTimeField(null=True)
    confirmation_statement_next_made_up_to = models.DateTimeField(null=True)
    confirmation_statement_overdue = models.CharField(max_length=50, null = True)
    links_self = models.CharField(max_length=50, null = True)
    links_filing_history = models.CharField(max_length=50, null = True)
    links_officers = models.CharField(max_length=50, null = True)
    links_persons_with_significant_control = models.CharField(max_length=50, null = True)

    # previous_company_names_name = models.CharField(max_length=50, null = True)
    # previous_company_names_ceased_on = models.CharField(max_length=50, null = True)
    # previous_company_names_effective_from = models.CharField(max_length=50, null = True)

    registered_office_is_in_dispute = models.CharField(max_length=50, null = True)
    can_file = models.CharField(max_length=50, null = True)

    def __str__(self):
        return "{}".format(self.code)

class CompanyHouse_CompanyProfile_Previous_Company_Names(models.Model):

    company_number = models.CharField(max_length=10, null=True)
    previous_company_names_name = models.CharField(max_length=50, null=True)
    previous_company_names_ceased_on = models.DateTimeField(null=True)
    previous_company_names_effective_from = models.DateTimeField(null=True)

    def __str__(self):
        return "{}".format(self.code)

class CompanyHouse_Registered_Office_Address(models.Model):

    company_number = models.CharField(max_length=10, null=True)
    address_line_1 = models.CharField(max_length=50, null=True)
    address_line_2 = models.CharField(max_length=50, null=True)
    locality = models.CharField(max_length=50, null=True)
    region = models.CharField(max_length=50, null=True)
    postal_code = models.CharField(max_length=50, null=True)
    kind = models.CharField(max_length=50, null=True)
    etag = models.CharField(max_length=50, null=True)
    links_self = models.CharField(max_length=50, null=True)

    def __str__(self):
        return "{}".format(self.code)

class CompanyHouse_Company_Officers(models.Model):

    company_number = models.CharField(max_length=10, null=True)
    etag = models.CharField(max_length=50, null=True)
    country_of_residence = models.CharField(max_length=50, null=True)
    appointed_on = models.DateTimeField(null=True)
    date_of_birth_month = models.CharField(max_length=50, null=True)
    date_of_birth_year = models.CharField(max_length=50, null=True)
    nationality = models.CharField(max_length=50, null=True)
    officer_role = models.CharField(max_length=50, null=True)
    address_country = models.CharField(max_length=50, null=True)
    address_region = models.CharField(max_length=50, null=True)
    address_premises = models.CharField(max_length=50, null=True)
    address_address_line_1 = models.CharField(max_length=50, null=True)
    address_locality = models.CharField(max_length=50, null=True)
    address_postal_code = models.CharField(max_length=50, null=True)
    occupation = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return "{}".format(self.code)

class CompanyHouse_Charge_List(models.Model):

    company_number = models.CharField(max_length=10, null=True)
    description = models.CharField(max_length=3000, null=True)
    contains_negative_pledge = models.CharField(max_length=100, null=True)
    contains_floating_charge = models.CharField(max_length=100, null=True)
    floating_charge_covers_all = models.CharField(max_length=100, null=True)
    contains_fixed_charge = models.CharField(max_length=100, null=True)
    type = models.CharField(max_length=100, null=True)
    created_on = models.DateTimeField(null=True)
    persons_entitled = models.CharField(max_length=100, null=True)
    classification_description = models.CharField(max_length=100, null=True)
    classification_type = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=100, null=True)
    transactions_filing_type = models.CharField(max_length=1000, null=True)
    transactions_filing = models.CharField(max_length=100, null=True)
    transactions_delivered_on = models.DateTimeField(null=True)
    charge_number = models.CharField(max_length=100, null=True)
    charge_code = models.CharField(max_length=100, null=True)
    delivered_on = models.DateTimeField(null=True)
    etag = models.CharField(max_length=100, null=True)
    satisfied_count = models.CharField(max_length=100, null=True)
    total_count = models.CharField(max_length=100, null=True)
    unfiltered_count = models.CharField(max_length=100, null=True)
    part_satisfied_count = models.CharField(max_length=100, null=True)

    def __str__(self):
        return "{}".format(self.code)

class CompanyHouse_Changes(models.Model):

    company = models.CharField(max_length=3000, null=True)
    company_number = models.CharField(max_length=3000, null=True)
    # agreements_affected = models.CharField(max_length=3000, null=True)
    type_of_change = models.CharField(max_length=3000, null=True)
    contact_name = models.CharField(max_length=3000, null=True)
    contact_number = models.CharField(max_length=3000, null=True)
    account_manager = models.CharField(max_length=3000, null=True)
    etag = models.CharField(max_length=3000, null=True)
    ncf_customer_number = models.CharField(max_length=3000, null=True)
    link = models.CharField(max_length=3000, null=True)
    checked = models.CharField(max_length=3000, null=True)

    def __str__(self):
        return "{}".format(self.code)


class eTagAudit(models.Model):

    company_number = models.CharField(max_length=3000, null=True)
    second_id = models.CharField(max_length=3000, null=True)
    etag = models.CharField(max_length=3000, null=True)
    checked = models.CharField(max_length=3000, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    checked_date = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    type_of_change = models.ForeignKey(RequestType, on_delete=models.DO_NOTHING)
    link = models.CharField(max_length=3000, null=True)
    agreements_affected = models.CharField(max_length=3000, null=True)

    def __str__(self):
        return "{} - {}".format(self.company_number, self.etag)
