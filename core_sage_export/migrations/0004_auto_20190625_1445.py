# Generated by Django 2.0.9 on 2019-06-25 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0003_auto_20190625_1026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sagebatchtransactions',
            old_name='transagreementdefname',
            new_name='sage_batch_agreementdefname',
        ),
        migrations.RenameField(
            model_name='sagebatchtransactions',
            old_name='transcustomercompany',
            new_name='sage_batch_customercompany',
        ),
        migrations.RenameField(
            model_name='sagebatchtransactions',
            old_name='transgrosspayment',
            new_name='sage_batch_netpayment',
        ),
        migrations.RenameField(
            model_name='sagebatchtransactions',
            old_name='transagreementauthority',
            new_name='sage_batch_typedesc',
        ),
        migrations.RenameField(
            model_name='sagebatchtransactions',
            old_name='transtypeid',
            new_name='sage_batch_typeid',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transactionbatch_id',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transagreementagreementdate',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transagreementcloseddate',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transddpayment',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transfallendue',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transflag',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transnetpayment',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transnetpaymentcapital',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transnetpaymentinterest',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transrunningtotal',
        ),
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='transtypedesc',
        ),
        migrations.AddField(
            model_name='sagebatchheaders',
            name='updated',
            field=models.DateField(auto_now=True),
        ),
        migrations.AddField(
            model_name='sagebatchtransactions',
            name='sage_batch_ref',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core_sage_export.SageBatchHeaders', to_field='sage_batch_ref'),
        ),
        migrations.AlterField(
            model_name='sagebatchheaders',
            name='status',
            field=models.CharField(choices=[('NOT RECORDED', 'NOT RECORDED'), ('RECORDED', 'RECORDED')], max_length=20, null=True),
        ),
    ]
