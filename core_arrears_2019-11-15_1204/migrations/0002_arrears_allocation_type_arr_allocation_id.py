# Generated by Django 2.0.9 on 2019-05-22 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_arrears', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrears_allocation_type',
            name='arr_allocation_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]