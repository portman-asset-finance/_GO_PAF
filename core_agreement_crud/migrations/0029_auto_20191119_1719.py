# Generated by Django 2.1.12 on 2019-11-19 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0028_auto_20191119_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='go_agreement_index',
            name='agreement_delay_vat_until',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='go_agreement_index',
            name='agreement_structure_rentals',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='go_agreement_index',
            name='agreement_structure_upfront',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]
