# Generated by Django 3.2.25 on 2024-03-19 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basic_info',
            name='sku',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
