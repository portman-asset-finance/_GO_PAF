# Generated by Django 2.1.12 on 2019-09-26 09:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyHouse_Changes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=3000, null=True)),
                ('company_number', models.CharField(max_length=3000, null=True)),
                ('type_of_change', models.CharField(max_length=3000, null=True)),
                ('contact_name', models.CharField(max_length=3000, null=True)),
                ('contact_number', models.CharField(max_length=3000, null=True)),
                ('account_manager', models.CharField(max_length=3000, null=True)),
                ('etag', models.CharField(max_length=3000, null=True)),
                ('ncf_customer_number', models.CharField(max_length=3000, null=True)),
                ('link', models.CharField(max_length=3000, null=True)),
                ('checked', models.CharField(max_length=3000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyHouse_Charge_List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_number', models.CharField(max_length=10, null=True)),
                ('description', models.CharField(max_length=3000, null=True)),
                ('contains_negative_pledge', models.CharField(max_length=100, null=True)),
                ('contains_floating_charge', models.CharField(max_length=100, null=True)),
                ('floating_charge_covers_all', models.CharField(max_length=100, null=True)),
                ('contains_fixed_charge', models.CharField(max_length=100, null=True)),
                ('type', models.CharField(max_length=100, null=True)),
                ('created_on', models.DateTimeField(null=True)),
                ('persons_entitled', models.CharField(max_length=100, null=True)),
                ('classification_description', models.CharField(max_length=100, null=True)),
                ('classification_type', models.CharField(max_length=100, null=True)),
                ('status', models.CharField(max_length=100, null=True)),
                ('transactions_filing_type', models.CharField(max_length=1000, null=True)),
                ('transactions_filing', models.CharField(max_length=100, null=True)),
                ('transactions_delivered_on', models.DateTimeField(null=True)),
                ('charge_number', models.CharField(max_length=100, null=True)),
                ('charge_code', models.CharField(max_length=100, null=True)),
                ('delivered_on', models.DateTimeField(null=True)),
                ('etag', models.CharField(max_length=100, null=True)),
                ('satisfied_count', models.CharField(max_length=100, null=True)),
                ('total_count', models.CharField(max_length=100, null=True)),
                ('unfiltered_count', models.CharField(max_length=100, null=True)),
                ('part_satisfied_count', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyHouse_Company_Officers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_number', models.CharField(max_length=10, null=True)),
                ('etag', models.CharField(max_length=50, null=True)),
                ('country_of_residence', models.CharField(max_length=50, null=True)),
                ('appointed_on', models.DateTimeField(null=True)),
                ('date_of_birth_month', models.CharField(max_length=50, null=True)),
                ('date_of_birth_year', models.CharField(max_length=50, null=True)),
                ('nationality', models.CharField(max_length=50, null=True)),
                ('officer_role', models.CharField(max_length=50, null=True)),
                ('address_country', models.CharField(max_length=50, null=True)),
                ('address_region', models.CharField(max_length=50, null=True)),
                ('address_premises', models.CharField(max_length=50, null=True)),
                ('address_address_line_1', models.CharField(max_length=50, null=True)),
                ('address_locality', models.CharField(max_length=50, null=True)),
                ('address_postal_code', models.CharField(max_length=50, null=True)),
                ('occupation', models.CharField(max_length=50, null=True)),
                ('name', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyHouse_CompanyProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_office_address_address_line_1', models.CharField(max_length=50, null=True)),
                ('registered_office_address_address_line_2', models.CharField(max_length=50, null=True)),
                ('registered_office_address_locality', models.CharField(max_length=50, null=True)),
                ('registered_office_address_region', models.CharField(max_length=50, null=True)),
                ('registered_office_address_postal_code', models.CharField(max_length=50, null=True)),
                ('date_of_creation', models.DateTimeField(null=True)),
                ('company_number', models.CharField(max_length=10)),
                ('last_full_members_list_date', models.DateTimeField(null=True)),
                ('company_name', models.CharField(max_length=50, null=True)),
                ('status', models.CharField(max_length=50, null=True)),
                ('has_been_liquidated', models.CharField(max_length=50, null=True)),
                ('jurisdiction', models.CharField(max_length=50, null=True)),
                ('accounts_next_due', models.DateTimeField(null=True)),
                ('accounts_accounting_reference_date', models.DateTimeField(null=True)),
                ('accounts_next_made_up_to', models.DateTimeField(null=True)),
                ('accounts_next_accounts_period_end_on', models.DateTimeField(null=True)),
                ('accounts_next_accounts_due_on', models.DateTimeField(null=True)),
                ('accounts_next_accounts_period_start_on', models.DateTimeField(null=True)),
                ('accounts_next_accounts_overdue', models.CharField(max_length=50, null=True)),
                ('accounts_overdue', models.CharField(max_length=50, null=True)),
                ('accounts_last_accounts_made_up_to', models.DateTimeField(null=True)),
                ('accounts_last_accounts_type', models.CharField(max_length=50, null=True)),
                ('accounts_last_accounts_period_end_on', models.DateTimeField(null=True)),
                ('accounts_last_accounts_period_start_on', models.DateTimeField(null=True)),
                ('undeliverable_registered_office_address', models.CharField(max_length=50, null=True)),
                ('sic_codes', models.CharField(max_length=50, null=True)),
                ('type', models.CharField(max_length=50, null=True)),
                ('etag', models.CharField(max_length=50, null=True)),
                ('has_insolvency_history', models.CharField(max_length=50, null=True)),
                ('company_status', models.CharField(max_length=50, null=True)),
                ('has_charges', models.CharField(max_length=50, null=True)),
                ('confirmation_statement_next_due', models.DateTimeField(null=True)),
                ('confirmation_statement_last_made_up_to', models.DateTimeField(null=True)),
                ('confirmation_statement_next_made_up_to', models.DateTimeField(null=True)),
                ('confirmation_statement_overdue', models.CharField(max_length=50, null=True)),
                ('links_self', models.CharField(max_length=50, null=True)),
                ('links_filing_history', models.CharField(max_length=50, null=True)),
                ('links_officers', models.CharField(max_length=50, null=True)),
                ('links_persons_with_significant_control', models.CharField(max_length=50, null=True)),
                ('registered_office_is_in_dispute', models.CharField(max_length=50, null=True)),
                ('can_file', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyHouse_CompanyProfile_Previous_Company_Names',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_number', models.CharField(max_length=10, null=True)),
                ('previous_company_names_name', models.CharField(max_length=50, null=True)),
                ('previous_company_names_ceased_on', models.DateTimeField(null=True)),
                ('previous_company_names_effective_from', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyHouse_Registered_Office_Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_number', models.CharField(max_length=10, null=True)),
                ('address_line_1', models.CharField(max_length=50, null=True)),
                ('address_line_2', models.CharField(max_length=50, null=True)),
                ('locality', models.CharField(max_length=50, null=True)),
                ('region', models.CharField(max_length=50, null=True)),
                ('postal_code', models.CharField(max_length=50, null=True)),
                ('kind', models.CharField(max_length=50, null=True)),
                ('etag', models.CharField(max_length=50, null=True)),
                ('links_self', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='eTagAudit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_number', models.CharField(max_length=3000, null=True)),
                ('second_id', models.CharField(max_length=3000, null=True)),
                ('etag', models.CharField(max_length=3000, null=True)),
                ('checked', models.CharField(max_length=3000, null=True)),
                ('checked_date', models.DateTimeField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('link', models.CharField(max_length=3000, null=True)),
                ('agreements_affected', models.CharField(max_length=3000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_url', models.CharField(max_length=250, null=True)),
                ('status_code', models.CharField(max_length=10)),
                ('response', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameter_type', models.CharField(blank=True, choices=[('QUERY_STRING', 'QUERY_STRING'), ('JSON_KEY_IN_POST_DATA', 'JSON_KEY_IN_POST_DATA')], max_length=50, null=True)),
                ('parameter_name', models.CharField(max_length=100)),
                ('parameter_key', models.CharField(max_length=100, null=True)),
                ('parameter_default_value', models.CharField(blank=True, max_length=250, null=True)),
                ('parameter_value_type', models.CharField(blank=True, choices=[('STRING', 'STRING'), ('DECIMAL', 'DECIMAL'), ('INTEGER', 'INTEGER'), ('DATE', 'DATE'), ('TIME', 'TIME')], max_length=10, null=True)),
                ('parameter_description', models.TextField(blank=True, null=True)),
                ('required', models.NullBooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('process_after', models.DateTimeField()),
                ('processed', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50)),
                ('description', models.TextField(null=True)),
                ('method', models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('HEAD', 'HEAD'), ('TRACE', 'TRACE'), ('DELETE', 'DELETE'), ('OPTIONS', 'OPTIONS'), ('CONNECT', 'CONNECT')], max_length=7)),
                ('url', models.CharField(max_length=250)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='requestset',
            name='request_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core_companies_house.RequestType'),
        ),
        migrations.AddField(
            model_name='requestlog',
            name='request_set',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core_companies_house.RequestSet'),
        ),
        migrations.AddField(
            model_name='requestlog',
            name='request_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core_companies_house.RequestType'),
        ),
        migrations.AddField(
            model_name='etagaudit',
            name='type_of_change',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core_companies_house.RequestType'),
        ),
        migrations.AddField(
            model_name='etagaudit',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]
