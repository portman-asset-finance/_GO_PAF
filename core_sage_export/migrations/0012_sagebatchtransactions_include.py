# Generated by Django 2.0.9 on 2019-06-26 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0011_sagebatchdetails_account_reference'),
    ]

    operations = [
        migrations.AddField(
            model_name='sagebatchtransactions',
            name='include',
            field=models.BooleanField(default=False),
        ),
    ]
