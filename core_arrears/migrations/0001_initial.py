# Generated by Django 2.0.9 on 2019-05-16 14:39

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
            name='arrears_allocation_type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arr_allocation_code', models.CharField(blank=True, max_length=20, null=True)),
                ('arr_allocation_description', models.CharField(max_length=100)),
                ('arr_allocation_src_id', models.CharField(blank=True, max_length=10, null=True)),
                ('arr_allocation_src_type', models.SmallIntegerField(null=True)),
                ('arr_allocation_value_net', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_allocation_value_gross', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_allocation_applied_auto', models.BooleanField(default=False)),
                ('arr_allocation_status', models.CharField(max_length=1)),
            ],
            options={
                'verbose_name': 'Arrears Allocation Type',
                'verbose_name_plural': 'Arrears Allocation Types',
                'ordering': ('arr_allocation_code',),
            },
        ),
        migrations.CreateModel(
            name='arrears_detail_arrear_level',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ard_agreement_id', models.CharField(max_length=50)),
                ('ard_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('ard_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('ard_arrears_id', models.IntegerField(blank=True, null=True)),
                ('ard_return_description', models.CharField(blank=True, max_length=500, null=True)),
                ('ard_effective_date', models.DateTimeField(blank=True, null=True)),
                ('ard_due_date', models.DateTimeField(blank=True, null=True)),
                ('ard_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('ard_referencestrip', models.CharField(blank=True, max_length=50, null=True)),
                ('ard_arrears_count', models.IntegerField(blank=True, null=True)),
                ('ard_arrears_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_arrears_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_arrears_last_date', models.DateField(blank=True, null=True)),
                ('ard_collected_count', models.IntegerField(blank=True, null=True)),
                ('ard_collected_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_collected_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_collected_last_date', models.DateField(blank=True, null=True)),
                ('ard_writtenoff_count', models.IntegerField(blank=True, null=True)),
                ('ard_writtenoff_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_writtenoff_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_writtenoff_last_date', models.DateField(blank=True, null=True)),
                ('ard_balance_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_balance_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ard_balance_last_date', models.DateField(blank=True, null=True)),
                ('ard_status_date', models.DateField(blank=True, null=True)),
                ('ard_file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('ard_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('ard_arrears_charge_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_allocation_type')),
            ],
            options={
                'verbose_name': 'Arrears Summary at Arrear Level',
                'verbose_name_plural': 'Arrears Summaries at Arrear Level',
                'ordering': ('ard_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='arrears_status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arr_status_code', models.CharField(max_length=1, unique=True)),
                ('arr_status_description', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Arrears Status',
                'verbose_name_plural': 'Arrears Statuses',
                'ordering': ('arr_status_code',),
            },
        ),
        migrations.CreateModel(
            name='arrears_summary_agreement_level',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arr_agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('arr_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('arr_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('arr_arrears_count', models.IntegerField(blank=True, null=True)),
                ('arr_arrears_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_arrears_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_arrears_last_date', models.DateField(blank=True, null=True)),
                ('arr_collected_count', models.IntegerField(blank=True, null=True)),
                ('arr_collected_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_collected_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_collected_last_date', models.DateField(blank=True, null=True)),
                ('arr_writtenoff_count', models.IntegerField(blank=True, null=True)),
                ('arr_writtenoff_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_writtenoff_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_writtenoff_last_date', models.DateField(blank=True, null=True)),
                ('arr_balance_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_balance_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('arr_balance_last_date', models.DateField(blank=True, null=True)),
                ('arr_status_date', models.DateField(blank=True, null=True)),
                ('arr_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('arr_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status')),
            ],
            options={
                'verbose_name': 'Arrears Summary by Agreement',
                'verbose_name_plural': 'Arrears Summaries by Agreement',
                'ordering': ('arr_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='arrears_summary_arrear_level',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ara_agreement_id', models.CharField(max_length=50)),
                ('ara_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('ara_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('ara_effective_date', models.DateTimeField(blank=True, null=True)),
                ('ara_due_date', models.DateTimeField(blank=True, null=True)),
                ('ara_transactionsourceid', models.CharField(blank=True, max_length=10, null=True)),
                ('ara_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('ara_referencestrip', models.CharField(blank=True, max_length=50, null=True)),
                ('ara_return_description', models.CharField(blank=True, max_length=500, null=True)),
                ('ara_arrears_id', models.IntegerField(blank=True, null=True)),
                ('ara_arrears_count', models.IntegerField(blank=True, null=True)),
                ('ara_arrears_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_arrears_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_arrears_last_date', models.DateField(blank=True, null=True)),
                ('ara_collected_count', models.IntegerField(blank=True, null=True)),
                ('ara_collected_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_collected_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_collected_last_date', models.DateField(blank=True, null=True)),
                ('ara_writtenoff_count', models.IntegerField(blank=True, null=True)),
                ('ara_writtenoff_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_writtenoff_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_writtenoff_last_date', models.DateField(blank=True, null=True)),
                ('ara_balance_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_balance_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ara_balance_last_date', models.DateField(blank=True, null=True)),
                ('ara_status_date', models.DateField(blank=True, null=True)),
                ('ara_file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('ara_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('ara_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status')),
            ],
            options={
                'verbose_name': 'Arrears Summary at Arrear Level',
                'verbose_name_plural': 'Arrears Summaries at Arrear Level',
                'ordering': ('ara_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='receipt_allocations_by_agreement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rag_agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('rag_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('rag_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('rag_received_count', models.IntegerField(blank=True, null=True)),
                ('rag_received_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_received_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_received_last_date', models.DateField(blank=True, null=True)),
                ('rag_allocated_count', models.IntegerField(blank=True, null=True)),
                ('rag_allocated_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_allocated_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_allocated_last_date', models.DateField(blank=True, null=True)),
                ('rag_unallocated_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_unallocated_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rag_unallocated_last_date', models.DateField(blank=True, null=True)),
                ('rag_status_date', models.DateField(blank=True, null=True)),
                ('rag_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('rag_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status')),
            ],
            options={
                'verbose_name': 'Receipts Summary at Agreement Level',
                'verbose_name_plural': 'Receipts Summary at Agreement Level',
                'ordering': ('rag_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='receipt_allocations_by_arrears',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ras_agreement_id', models.CharField(max_length=50)),
                ('ras_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('ras_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('ras_effective_date', models.DateTimeField(blank=True, null=True)),
                ('ras_due_date', models.DateTimeField(blank=True, null=True)),
                ('ras_transactionsourceid', models.CharField(blank=True, max_length=10, null=True)),
                ('ras_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('ras_referencestrip', models.CharField(blank=True, max_length=50, null=True)),
                ('ras_return_description', models.CharField(blank=True, max_length=500, null=True)),
                ('ras_arrears_id', models.IntegerField(blank=True, null=True)),
                ('ras_allocation_id', models.IntegerField(blank=True, null=True)),
                ('ras_arrears_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_arrears_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_collected_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_collected_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_adjustment_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_adjustment_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_balance_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_balance_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('ras_status_date', models.DateField(blank=True, null=True)),
                ('ras_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('ras_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status')),
            ],
            options={
                'verbose_name': 'Receipts Summary at Arrear Level',
                'verbose_name_plural': 'Receipts Summaries at Arrear Level',
                'ordering': ('ras_agreement_id',),
            },
        ),
        migrations.CreateModel(
            name='receipt_allocations_by_detail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rad_agreement_id', models.CharField(max_length=50)),
                ('rad_customernumber', models.CharField(blank=True, max_length=10, null=True)),
                ('rad_customercompanyname', models.CharField(blank=True, max_length=60, null=True)),
                ('rad_effective_date', models.DateTimeField(blank=True, null=True)),
                ('rad_due_date', models.DateTimeField(blank=True, null=True)),
                ('rad_reference', models.CharField(blank=True, max_length=50, null=True)),
                ('rad_referencestrip', models.CharField(blank=True, max_length=50, null=True)),
                ('rad_arrears_id', models.IntegerField(blank=True, null=True)),
                ('rad_allocation_id', models.IntegerField(blank=True, null=True)),
                ('rad_arrears_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_arrears_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_collected_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_collected_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_adjustment_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_adjustment_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_balance_value_netofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_balance_value_grossofvat', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rad_status_date', models.DateField(blank=True, null=True)),
                ('rad_agent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('rad_allocation_charge_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_allocation_type')),
                ('rad_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status')),
            ],
            options={
                'verbose_name': 'Receipts Allocations at Detail Level',
                'verbose_name_plural': 'Receipts Allocations at Detail Level',
                'ordering': ('rad_agreement_id',),
            },
        ),
        migrations.AddField(
            model_name='arrears_detail_arrear_level',
            name='ard_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core_arrears.arrears_status'),
        ),
    ]
