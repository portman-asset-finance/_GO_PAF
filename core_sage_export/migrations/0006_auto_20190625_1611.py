# Generated by Django 2.0.9 on 2019-06-25 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0005_remove_sagebatchtransactions_sage_batch_typeid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sagebatchheaders',
            name='sage_batch_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='sagebatchheaders',
            name='status',
            field=models.CharField(choices=[('NOT RECORDED', 'NOT RECORDED'), ('NOT RECORDED', 'NOT RECORDED'), ('RECORDED', 'RECORDED')], max_length=20, null=True),
        ),
    ]