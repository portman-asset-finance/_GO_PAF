# Generated by Django 2.0.9 on 2019-07-02 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0024_sagebatchheaders_sage_batch_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='sagebatchtransactions',
            name='remove',
            field=models.NullBooleanField(default=True),
        ),
    ]
