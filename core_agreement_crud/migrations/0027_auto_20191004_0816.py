# Generated by Django 2.1.12 on 2019-10-04 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0026_go_agreement_index_companies_house_status_flag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='go_account_transaction_detail',
            name='transtypedesc',
            field=models.CharField(blank=True, db_column='TransTypeDescription', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='go_account_transaction_summary',
            name='transtypedesc',
            field=models.CharField(blank=True, db_column='TransTypeDescription', max_length=100, null=True),
        ),
    ]