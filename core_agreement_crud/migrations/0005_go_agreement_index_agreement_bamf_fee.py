# Generated by Django 2.0.9 on 2019-05-23 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0004_auto_20190523_0811'),
    ]

    operations = [
        migrations.AddField(
            model_name='go_agreement_index',
            name='agreement_bamf_fee',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=19, null=True),
        ),
    ]