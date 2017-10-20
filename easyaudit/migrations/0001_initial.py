# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CRUDEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_type', models.SmallIntegerField(choices=[(1, b'Create'), (2, b'Update'), (3, b'Delete')])),
                ('object_id', models.IntegerField()),
                ('object_repr', models.CharField(max_length=255, null=True, blank=True)),
                ('object_json_repr', models.TextField(null=True, blank=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-datetime'],
                'verbose_name': 'CRUD event',
                'verbose_name_plural': 'CRUD events',
            },
        ),
        migrations.CreateModel(
            name='LoginEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('login_type', models.SmallIntegerField(choices=[(0, b'Login'), (1, b'Logout'), (2, b'Login fallido')])),
                ('username', models.CharField(max_length=255, null=True, blank=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-datetime'],
                'verbose_name': 'login event',
                'verbose_name_plural': 'login events',
            },
        ),
    ]
