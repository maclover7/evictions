# Generated by Django 3.0.8 on 2020-07-01 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evictions', '0002_case'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='disposition_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
