# Generated by Django 3.0.5 on 2020-04-30 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0037_auto_20200430_0912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requirement',
            name='inverter',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='requirement',
            name='panel',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.DeleteModel(
            name='Inverter',
        ),
        migrations.DeleteModel(
            name='Panel',
        ),
    ]
