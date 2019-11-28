# Generated by Django 2.1.12 on 2019-09-18 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_eazycollect', '0014_auto_20190917_0937'),
    ]

    operations = [
        migrations.CreateModel(
            name='BacsIssues',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('new_status', models.CharField(blank=True, max_length=100, null=True)),
                ('object_id', models.CharField(blank=True, max_length=100, null=True)),
                ('change_date', models.DateTimeField(blank=True, null=True)),
                ('entity', models.CharField(blank=True, max_length=100, null=True)),
                ('source', models.CharField(blank=True, max_length=100, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CallbackLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('http_method', models.CharField(blank=True, max_length=10, null=True)),
                ('body_data', models.TextField(blank=True, null=True)),
                ('get_data', models.TextField(blank=True, null=True)),
                ('post_data', models.TextField(blank=True, null=True)),
                ('meta_data', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Payments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(blank=True, max_length=50, null=True)),
                ('ez_payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('ez_contract_id', models.CharField(blank=True, max_length=100, null=True)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.DeleteModel(
            name='RequestTemp',
        ),
    ]