# Generated by Django 3.0.7 on 2020-09-16 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20200914_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='reference_code',
            field=models.CharField(default='rrr', max_length=30),
            preserve_default=False,
        ),
    ]