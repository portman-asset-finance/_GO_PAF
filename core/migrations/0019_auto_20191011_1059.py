# Generated by Django 2.1.12 on 2019-10-11 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20191010_1814'),
    ]

    operations = [
        migrations.AddField(
            model_name='ncf_datacash_drawdowns',
            name='dd_agreement_valid',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='ncf_datacash_setups',
            name='dd_agreement_valid',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
    ]