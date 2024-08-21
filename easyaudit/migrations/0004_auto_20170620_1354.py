# Generated by Django 1.11.1 on 2017-06-20 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('easyaudit', '0003_auto_20170228_1505'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='crudevent',
            index=models.Index(fields=['object_id', 'content_type'], name='easyaudit_c_object__82020b_idx'),
        ),
    ]
