# Generated by Django 1.11.6 on 2018-01-05 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('easyaudit', '0006_auto_20171018_1242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crudevent',
            name='event_type',
            field=models.SmallIntegerField(choices=[(1, 'Create'), (2, 'Update'), (3, 'Delete'), (4, 'Many-to-Many Change'), (5, 'Reverse Many-to-Many Change')]),
        ),
        migrations.AlterField(
            model_name='crudevent',
            name='user_pk_as_string',
            field=models.CharField(blank=True, help_text='String version of the user pk', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='loginevent',
            name='login_type',
            field=models.SmallIntegerField(choices=[(0, 'Login'), (1, 'Logout'), (2, 'Failed login')]),
        ),
    ]
