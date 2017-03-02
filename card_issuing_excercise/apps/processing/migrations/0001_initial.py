# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-28 19:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_type', models.CharField(choices=[('b', 'Basic account'), ('r', 'Reserved account')], max_length=1, verbose_name='Account type')),
                ('amount', models.DecimalField(decimal_places=4, default=0.0, max_digits=19, verbose_name='Amount')),
            ],
        ),
        migrations.CreateModel(
            name='AccountDayLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('amount', models.DecimalField(decimal_places=4, default=0.0, max_digits=19, verbose_name='Amount')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='account_logs', to='processing.Account', verbose_name='Account')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=9, verbose_name='Transaction ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('status', models.CharField(choices=[('a', 'Authorization'), ('p', 'Presentment'), ('z', 'Money shortage'), ('t', 'Presentment is exceeded TTL'), ('r', 'Rollback'), ('l', 'Load money'), ('s', 'Settle day transactions')], max_length=1, verbose_name='Status')),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=4, default=0.0, max_digits=19, verbose_name='Amount')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='processing.Account', verbose_name='Account')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='processing.Transaction', verbose_name='Transaction')),
            ],
        ),
        migrations.CreateModel(
            name='UserAccountsUnion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_id', models.CharField(max_length=8, unique=True, verbose_name='Account ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('role', models.CharField(choices=[('b', 'Real user'), ('is', 'Inner settlement account'), ('el', 'External load money account'), ('es', 'External settlement account'), ('r', 'Inner revenue account')], default='b', max_length=2, verbose_name='Role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Owner')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='transaction',
            unique_together=set([('code', 'status')]),
        ),
        migrations.AddField(
            model_name='account',
            name='user_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='processing.UserAccountsUnion', verbose_name='User account'),
        ),
        migrations.AlterUniqueTogether(
            name='accountdaylog',
            unique_together=set([('account', 'date')]),
        ),
    ]