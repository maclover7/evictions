# Generated by Django 3.0.8 on 2020-07-01 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Court',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('friendly_court_id', models.CharField(max_length=200)),
                ('court_id', models.CharField(max_length=200)),
                ('judge_name', models.CharField(max_length=200)),
            ],
        ),
    ]
