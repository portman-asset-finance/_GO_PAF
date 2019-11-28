# Generated by Django 2.0.9 on 2019-06-26 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0016_sagebatchtransactions_include'),
    ]

    operations = [
        migrations.CreateModel(
            name='SageDependencyTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_type', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('sage_transaction_type', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('type', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('account_reference', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('nominal_account_ref', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('sage_batch_details', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('tax_code', models.CharField(blank=True, max_length=50, null=True, unique=True)),
            ],
            options={
                'db_table': 'core_sage_dependency_table',
            },
        ),
    ]