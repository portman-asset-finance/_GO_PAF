# Generated by Django 2.0.9 on 2019-05-23 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0005_go_agreement_index_agreement_bamf_fee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='go_customers',
            name='customermobilenumber',
            field=models.CharField(blank=True, db_column='CustomerMobileNumber', max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='go_customers',
            name='customerphonenumber',
            field=models.CharField(blank=True, db_column='CustomerPhoneNumber', max_length=25, null=True),
        ),
    ]
