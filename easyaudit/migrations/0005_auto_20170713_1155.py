# Generated by Django 1.11.2 on 2017-07-13 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('easyaudit', '0004_auto_20170620_1354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudevent',
            name='event_type',
            field=models.SmallIntegerField(choices=[(1, b'Create'), (2, b'Update'), (3, b'Delete'), (4, b'Many-to-Many Change'), (5, b'Reverse Many-to-Many Change')]),
        ),
    ]
