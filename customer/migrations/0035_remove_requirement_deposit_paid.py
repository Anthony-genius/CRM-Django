# Generated by Django 3.0.5 on 2020-04-29 21:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0034_auto_20200430_0709'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requirement',
            name='deposit_paid',
        ),
    ]
