# Generated by Django 3.2.23 on 2024-01-29 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_app', '0003_testbigintforeignkey_testbigintm2m_testbigintmodel_testuuidforeignkey_testuuidm2m_testuuidmodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestM2MProxy',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('test_app.testm2m',),
        ),
        migrations.CreateModel(
            name='TestMultiM2M',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('test_m2m_a', models.ManyToManyField(related_name='testmultim2m_a', to='test_app.TestModel')),
                ('test_m2m_b', models.ManyToManyField(related_name='testmultim2m_b', to='test_app.TestModel')),
            ],
        ),
    ]