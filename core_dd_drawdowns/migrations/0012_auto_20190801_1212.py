# Generated by Django 2.0.9 on 2019-08-01 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_dd_drawdowns', '0011_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='request_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='log',
            name='response_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
