# Generated by Django 2.0.9 on 2019-09-05 16:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_arrears', '0006_auto_20190902_1536'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='receipt_allocations_by_detail',
            options={'ordering': ('rad_agreement_id', '-rad_due_date'), 'verbose_name': 'Receipts Allocations at Detail Level', 'verbose_name_plural': 'Receipts Allocations at Detail Level'},
        ),
    ]
