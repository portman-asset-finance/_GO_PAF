# Generated by Django 2.0.9 on 2019-09-10 16:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0024_auto_20190910_1624'),
        ('core_dd_drawdowns', '0015_auto_20190823_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchheaders',
            name='funder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core_agreement_crud.go_funder'),
        ),
        migrations.AddField(
            model_name='drawdown',
            name='funder_id',
            field=models.CharField(max_length=250, null=True),
        ),
    ]
