# Generated by Django 3.0.5 on 2020-04-25 02:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0011_auto_20200425_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='customer_check',
            field=models.BooleanField(default=False),
        ),
    ]
