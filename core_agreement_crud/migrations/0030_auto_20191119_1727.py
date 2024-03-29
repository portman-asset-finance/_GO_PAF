# Generated by Django 2.1.12 on 2019-11-19 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_agreement_crud', '0029_auto_20191119_1719'),
    ]

    operations = [
        migrations.CreateModel(
            name='go_payment_method',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.SmallIntegerField(blank=True, null=True)),
                ('payment_method_description', models.CharField(blank=True, max_length=50, null=True)),
                ('payment_method_group', models.CharField(blank=True, max_length=50, null=True)),
                ('selectable', models.NullBooleanField()),
            ],
        ),
        migrations.AddField(
            model_name='go_account_transaction_summary',
            name='transactionpaymentmethod',
            field=models.CharField(default='', max_length=15, null=True),
        ),
    ]
