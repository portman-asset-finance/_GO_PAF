# Generated by Django 2.1.12 on 2019-10-25 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_ncf_bacs_file_signatures_processed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ncf_bacs_file_signatures_processed',
            name='file_signature',
            field=models.CharField(max_length=4000),
        ),
    ]
