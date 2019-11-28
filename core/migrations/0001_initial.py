# Generated by Django 2.0.9 on 2018-10-22 17:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('anchorimport', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='apellio_extensions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ap_extension_sequence', models.IntegerField(blank=True, null=True)),
                ('ap_extension_code', models.CharField(max_length=10)),
                ('ap_extension_description', models.CharField(max_length=50)),
                ('ap_extension_required_interface_frequency_days', models.IntegerField()),
                ('ap_extension_last_interface_run', models.DateField(blank=True, null=True)),
                ('ap_extension_next_interface_run', models.DateField(blank=True, null=True)),
                ('ap_extension_active', models.NullBooleanField()),
            ],
            options={
                'verbose_name_plural': '< 0.00 Apellio Extensions',
                'verbose_name': 'Apellio Extension',
                'ordering': ('ap_extension_sequence',),
            },
        ),
        migrations.CreateModel(
            name='ncf_advanced_payments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('agreement_name', models.CharField(blank=True, max_length=500, null=True)),
                ('advance_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('method', models.CharField(blank=True, max_length=50, null=True)),
                ('advance_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField()),
            ],
            options={
                'verbose_name_plural': '< 2.01 NCF Advance Payments',
                'verbose_name': 'Advance Payment',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_agreement_titles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(max_length=50)),
                ('title_date', models.DateField(null=True)),
                ('invoice_number', models.CharField(blank=True, max_length=50, null=True)),
                ('customer_name', models.CharField(blank=True, max_length=250)),
                ('amount_paid', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('paying_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('proforma', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('method', models.CharField(blank=True, max_length=20, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name_plural': '< 2.04 NCF Agreement Titles',
                'verbose_name': 'Agreement Title',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_applicationwide_text',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_text_code', models.IntegerField(unique=True)),
                ('app_text_set', models.IntegerField(blank=True, null=True)),
                ('app_text_description', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'verbose_name_plural': 'Applicationwide Text Item',
                'verbose_name': 'Applicationwide Text Item',
                'ordering': ('app_text_description',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_collected',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ac_collected_date', models.DateField(blank=True, null=True)),
                ('ac_agreement_id', models.CharField(max_length=50)),
                ('ac_agreement_name', models.CharField(blank=True, max_length=250, null=True)),
                ('ac_arrears_collected', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ac_method', models.CharField(blank=True, max_length=10, null=True)),
                ('ac_fees_collected', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ac_agent_name', models.CharField(blank=True, max_length=50, null=True)),
                ('ac_notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': '< 2.02 NCF Arrears Collected',
                'verbose_name': 'Arrears Collected',
                'ordering': ('ac_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_detail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('col_arrears_duedate', models.DateField(blank=True, null=True)),
                ('col_arrears_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_startdate', models.DateField(blank=True, null=True)),
                ('col_arrears_latestdate', models.DateField(blank=True, null=True)),
                ('col_arrears_detl_changedate', models.DateField(blank=True, null=True)),
                ('col_uuid', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Arrears Detail',
                'verbose_name': 'Arrears Detail',
                'ordering': ('col_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_detail_txn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('col_arrears_duedate', models.DateField(blank=True, null=True)),
                ('col_arrears_type_id', models.SmallIntegerField(blank=True, null=True)),
                ('col_arrears_type_desc', models.CharField(blank=True, max_length=30, null=True)),
                ('col_arrears_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_startdate', models.DateField(blank=True, null=True)),
                ('col_arrears_latestdate', models.DateField(blank=True, null=True)),
                ('col_arrears_txn_changedate', models.DateField(blank=True, null=True)),
                ('col_uuid', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Arrears Detail Transactions',
                'verbose_name': 'Arrears Detail Transaction',
                'ordering': ('col_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_phase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_phase_code', models.CharField(blank=True, max_length=5, null=True)),
                ('col_phase_description', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'verbose_name_plural': 'Collection Phases',
                'verbose_name': 'Collection Phase',
                'ordering': ('col_phase_description',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_status_code', models.CharField(blank=True, max_length=5, null=True)),
                ('col_status_description', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'verbose_name_plural': '< 5.03 Collection Statuses',
                'verbose_name': 'Collection Status',
                'ordering': ('col_status_description',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_summary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('col_arrears_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_collected_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_outstanding_gross_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('col_arrears_startdate', models.DateField(blank=True, null=True)),
                ('col_arrears_latestdate', models.DateField(blank=True, null=True)),
                ('col_arrears_sum_changedate', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': '< 5.01 Arrears Summaries',
                'verbose_name': 'Arrears Summary',
                'ordering': ('col_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_arrears_summary_uuid_xref',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('col_uuid', models.UUIDField(blank=True, null=True)),
                ('col_uuid_changedate', models.DateField(blank=True, null=True)),
                ('col_agreement_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='anchorimport.AnchorimportAgreement_QueryDetail', to_field='agreementnumber')),
                ('col_uuid_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_status')),
            ],
        ),
        migrations.CreateModel(
            name='ncf_auddis_addacs_advices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_payer_name', models.CharField(blank=True, max_length=500, null=True)),
                ('dd_reason_code', models.CharField(blank=True, max_length=1, null=True)),
                ('dd_reason', models.CharField(blank=True, max_length=500, null=True)),
                ('dd_payer_sort_code', models.CharField(blank=True, max_length=6, null=True)),
                ('dd_payer_account_number', models.CharField(blank=True, max_length=8, null=True)),
                ('dd_payer_new_sort_code', models.CharField(blank=True, max_length=6, null=True)),
                ('dd_payer_new_account_number', models.CharField(blank=True, max_length=8, null=True)),
                ('dd_effective_date', models.DateField(blank=True, null=True)),
                ('dd_due_date', models.DateField(blank=True, null=True)),
                ('file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': '< 1.03 BACS AUDDIS/ADDACS Advices',
                'verbose_name': 'Auddis/Addacs Advice',
                'ordering': ('dd_reference',),
            },
        ),
        migrations.CreateModel(
            name='ncf_bacs_files_processed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': '< 1.02 BACS Files Processed',
                'verbose_name': 'BACS File Processed',
                'ordering': ('file_name',),
            },
        ),
        migrations.CreateModel(
            name='ncf_bacs_files_to_process',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('network_path_source', models.CharField(max_length=500)),
                ('network_path_archive', models.CharField(max_length=500)),
                ('target_data_format', models.CharField(blank=True, max_length=10, null=True)),
                ('file_type', models.CharField(max_length=10)),
                ('file_identifier', models.CharField(max_length=500)),
            ],
            options={
                'verbose_name_plural': '< 0.01 BACS File Processing Control',
                'verbose_name': 'BACS File to Process',
                'ordering': ('file_identifier',),
            },
        ),
        migrations.CreateModel(
            name='ncf_bacs_reasons',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason_code', models.CharField(max_length=1)),
                ('reason_description', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name_plural': '< 1.01 BACS Reason Codes',
                'verbose_name': 'BACS Reason Code',
                'ordering': ('reason_code',),
            },
        ),
        migrations.CreateModel(
            name='ncf_collection_agents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bd_agent_primary_manager', models.NullBooleanField(default=False)),
                ('bd_agent_primary_active', models.NullBooleanField(default=False)),
                ('bd_agent_secondary_manager', models.NullBooleanField(default=False)),
                ('bd_agent_secondary_active', models.NullBooleanField(default=False)),
                ('bd_collection_agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': '< 4.03 Bounce Day Collection Agents',
                'verbose_name': 'Bounce Day Collection Agent',
                'ordering': ('bd_collection_agent',),
            },
        ),
        migrations.CreateModel(
            name='ncf_datacash_drawdowns',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(max_length=50)),
                ('dd_reference', models.CharField(max_length=50)),
                ('dd_setup_no', models.CharField(blank=True, max_length=20, null=True)),
                ('dd_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('dd_method', models.CharField(blank=True, max_length=20, null=True)),
                ('dd_request_date', models.DateField(blank=True, null=True)),
                ('dd_batch_status', models.CharField(blank=True, max_length=20, null=True)),
                ('dd_due_date', models.DateField(blank=True, null=True)),
                ('dd_response', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_stage', models.CharField(blank=True, max_length=20, null=True)),
                ('dd_bacs_reason', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'verbose_name_plural': '< 0.03 DataCash Drawdowns',
                'verbose_name': 'DataCash Drawdown',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_datacash_setups',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(max_length=50)),
                ('dd_reference', models.CharField(max_length=50)),
                ('dd_account_name', models.CharField(blank=True, max_length=250, null=True)),
                ('dd_stage', models.CharField(blank=True, max_length=20, null=True)),
                ('dd_method', models.CharField(blank=True, max_length=10, null=True)),
                ('dd_request_date', models.DateTimeField(blank=True, null=True)),
                ('dd_batch_status', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'verbose_name_plural': '< 3.01 DataCash Setups ',
                'verbose_name': 'DataCash Setup',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_audit_log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('da_agreement_id', models.CharField(max_length=50)),
                ('da_reference', models.CharField(max_length=50)),
                ('da_source', models.CharField(max_length=50)),
                ('da_account_name', models.CharField(blank=True, max_length=250, null=True)),
                ('da_reason_code', models.CharField(blank=True, max_length=20, null=True)),
                ('da_reason', models.CharField(blank=True, max_length=500, null=True)),
                ('da_effective_date', models.DateTimeField(blank=True, null=True)),
                ('da_payer_sort_code', models.CharField(blank=True, max_length=6, null=True)),
                ('da_payer_account_number', models.CharField(blank=True, max_length=8, null=True)),
                ('da_payer_new_sort_code', models.CharField(blank=True, max_length=6, null=True)),
                ('da_payer_new_account_number', models.CharField(blank=True, max_length=8, null=True)),
                ('file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('da_created_at', models.DateTimeField()),
            ],
            options={
                'verbose_name_plural': '< 1.05 BACS DD Audit Log Items',
                'verbose_name': 'DD Audit Log Item',
                'ordering': ('da_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_call_arrears',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ar_agreement_id', models.CharField(max_length=50)),
                ('ar_account_name', models.CharField(blank=True, max_length=250, null=True)),
                ('ar_salesperson', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_arrears_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_arrears_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_arrears_total', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_term', models.CharField(blank=True, max_length=10, null=True)),
                ('ar_date', models.DateField(blank=True, null=True)),
                ('ar_days', models.IntegerField(blank=True, null=True)),
                ('ar_notes', models.TextField(blank=True, null=True)),
                ('ar_agreement_phase', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_exclude_reason', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_dd_original_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_schedule_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('ar_calendar_due_date', models.DateField(blank=True, null=True)),
                ('ar_uuid', models.UUIDField(blank=True, null=True)),
                ('ar_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_collection_agents')),
            ],
            options={
                'verbose_name_plural': '< 4.01 Bounce Day Arrears',
                'verbose_name': 'Bounce Day Arrears',
                'ordering': ('ar_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_call_control',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dd_call_date', models.DateField(blank=True, null=True)),
                ('dd_due_date', models.DateField(blank=True, null=True)),
                ('dd_bounce_process_date', models.DateField(blank=True, null=True)),
                ('dd_arrears_process_date', models.DateField(blank=True, null=True)),
                ('dd_first_bounce_day', models.NullBooleanField(default=True)),
                ('dd_bacs_bounce_date01', models.DateField(blank=True, null=True)),
                ('dd_bacs_bounce_date02', models.DateField(blank=True, null=True)),
                ('dd_bacs_bounce_date03', models.DateField(blank=True, null=True)),
                ('dd_bacs_bounce_date04', models.DateField(blank=True, null=True)),
                ('dd_bacs_bounce_date05', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': '< 0.04 Bounce Day Controls',
                'verbose_name': 'Bounce Day Control',
                'ordering': ('dd_due_date',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_call_rejections',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ar_agreement_id', models.CharField(max_length=50)),
                ('ar_account_name', models.CharField(blank=True, max_length=250, null=True)),
                ('ar_salesperson', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_date_cancelled', models.DateField(blank=True, null=True)),
                ('ar_term', models.CharField(blank=True, max_length=10, null=True)),
                ('ar_reason_cancelled', models.CharField(blank=True, max_length=250, null=True)),
                ('ar_days_cancelled', models.IntegerField(blank=True, null=True)),
                ('ar_next_dd_due', models.DateField(blank=True, null=True)),
                ('ar_days_until_dd', models.IntegerField(blank=True, null=True)),
                ('ar_notes', models.TextField(blank=True, null=True)),
                ('ar_agreement_phase', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_exclude_reason', models.CharField(blank=True, max_length=50, null=True)),
                ('ar_dd_original_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_schedule_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ar_file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('ar_calendar_due_date', models.DateField(blank=True, null=True)),
                ('ar_uuid', models.UUIDField(blank=True, null=True)),
                ('ar_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_collection_agents')),
            ],
            options={
                'verbose_name_plural': '< 4.02 Bounce Day BACS UDDs',
                'verbose_name': 'Bounce Day BACS UDDs',
                'ordering': ('ar_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dd_calendar_due_date', models.DateField()),
                ('dd_working_due_date', models.DateField()),
                ('dd_process_date01', models.DateField()),
                ('dd_process_date02', models.DateField()),
                ('dd_bounce_date01', models.DateField()),
                ('dd_bounce_date02', models.DateField()),
                ('dd_change_cutoff_date', models.DateField()),
                ('dd_call_date', models.DateField()),
                ('dd_firstbounce_processed', models.NullBooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': '< 0.05 Bounce Day Controls',
                'verbose_name': 'Bounce Day Control',
                'ordering': ('dd_calendar_due_date',),
            },
        ),
        migrations.CreateModel(
            name='ncf_dd_schedule_status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dd_status_text_code', models.IntegerField(unique=True)),
                ('dd_status_text_description', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name_plural': 'DD Schedule Statuses',
                'verbose_name': 'DD Schedule Status',
                'ordering': ('dd_status_text_code',),
            },
        ),
        migrations.CreateModel(
            name='ncf_global_terminations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(max_length=50)),
                ('agreement_name', models.CharField(blank=True, max_length=500, null=True)),
                ('agreement_rep', models.CharField(blank=True, max_length=50, null=True)),
                ('written_off', models.NullBooleanField(default=True)),
                ('date_terminated', models.DateField(blank=True, null=True)),
                ('reason', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'verbose_name_plural': '< 2.05 NCF Global Terminations',
                'verbose_name': 'Global Termination',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_props_and_payouts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('regulated_flag', models.CharField(blank=True, max_length=10, null=True)),
                ('payout_date', models.DateField(blank=True, null=True)),
                ('customer_name', models.CharField(blank=True, max_length=500, null=True)),
                ('sales_person', models.CharField(blank=True, max_length=10, null=True)),
                ('rep_person', models.CharField(blank=True, max_length=10, null=True)),
                ('term_text', models.CharField(blank=True, max_length=10, null=True)),
                ('term_mm', models.IntegerField(blank=True, null=True)),
                ('gross_rental', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('net_invoice_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('net_gross_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('agreement_type', models.CharField(blank=True, max_length=10, null=True)),
                ('first_rental_date', models.DateField(blank=True, null=True)),
                ('final_rental_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': '< 0.02 NCF Interface Control',
                'verbose_name': 'Props & Payouts record',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_sentinel_dd_batches',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_account_name', models.CharField(blank=True, max_length=250, null=True)),
                ('dd_sortcode', models.CharField(blank=True, max_length=10, null=True)),
                ('dd_account_number', models.CharField(blank=True, max_length=10, null=True)),
                ('dd_record', models.CharField(blank=True, max_length=5, null=True)),
                ('dd_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('dd_new_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('dd_code', models.CharField(blank=True, max_length=5, null=True)),
                ('dd_warning', models.CharField(blank=True, max_length=250, null=True)),
            ],
            options={
                'verbose_name_plural': '< 3.02 DataCash/Sentinel Batch Items',
                'verbose_name': 'DataCash/Sentinel Batch Item',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_settled_agreements',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('agreement_name', models.CharField(blank=True, max_length=500, null=True)),
                ('settlement_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('method', models.CharField(blank=True, max_length=50, null=True)),
                ('settlement_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField()),
                ('received_from', models.CharField(blank=True, max_length=500, null=True)),
                ('agreement_type', models.CharField(blank=True, max_length=10, null=True)),
                ('vat_status', models.CharField(blank=True, max_length=10, null=True)),
                ('removed_from_sentinel', models.NullBooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': '< 2.03 NCF Settled Agreements',
                'verbose_name': 'Settled Agreement',
                'ordering': ('agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='ncf_udd_advices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('dd_original_process_date', models.DateField(blank=True, null=True)),
                ('dd_transcode', models.CharField(blank=True, max_length=2, null=True)),
                ('dd_currency', models.CharField(blank=True, max_length=5, null=True)),
                ('dd_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('dd_return_description', models.CharField(blank=True, max_length=500, null=True)),
                ('file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': '< 1.04 BACS UDD Advices',
                'verbose_name': 'UDD Advice',
                'ordering': ('dd_reference',),
            },
        ),
        migrations.AddField(
            model_name='ncf_dd_schedule',
            name='dd_status',
            field=models.ForeignKey(blank=True, default=921, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.ncf_dd_schedule_status', to_field='dd_status_text_code'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_summary',
            name='col_agent_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_collection_agents'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_summary',
            name='col_arrears_sum_phase',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_phase'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_summary',
            name='col_arrears_sum_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_status'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail_txn',
            name='col_agent_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_collection_agents'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail_txn',
            name='col_arrears_txn_phase',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_phase'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail_txn',
            name='col_arrears_txn_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_status'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail',
            name='col_agent_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_collection_agents'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail',
            name='col_arrears_detl_phase',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_phase'),
        ),
        migrations.AddField(
            model_name='ncf_arrears_detail',
            name='col_arrears_detl_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ncf_arrears_status'),
        ),
    ]