# Generated by Django 2.1.12 on 2019-10-10 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20191010_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ncf_auddis_addacs_advices',
            name='dd_due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ncf_auddis_addacs_advices',
            name='dd_effective_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ncf_dd_audit_log',
            name='da_original_process_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ncf_ddic_advices',
            name='ddic_DateOfDocumentDebit',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ncf_ddic_advices',
            name='ddic_DateOfOriginalDD',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ncf_udd_advices',
            name='dd_original_process_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]