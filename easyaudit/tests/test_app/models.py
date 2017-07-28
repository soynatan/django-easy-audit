from django.db import models


class TestModel(models.Model):
    name = models.CharField(max_length=50, default='test data')


class TestForeignKey(models.Model):
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(TestModel)

class TestM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(TestModel)
