# Generated by Django 2.1.7 on 2020-05-21 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0047_auto_20200522_0329'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='MNI',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='requirement',
            name='application',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='requirement',
            name='finance',
            field=models.BooleanField(default=False),
        ),
    ]