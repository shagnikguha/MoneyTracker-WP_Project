# Generated by Django 4.2.19 on 2025-04-09 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_subscribed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscribed',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]
