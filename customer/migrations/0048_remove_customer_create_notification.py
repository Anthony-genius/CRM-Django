# Generated by Django 3.0.5 on 2020-05-21 20:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0047_customer_create_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='create_notification',
        ),
    ]
