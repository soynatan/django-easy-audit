import uuid

from django.db import models


class TestModel(models.Model):
    name = models.CharField(max_length=50, default='test data')


class TestForeignKey(models.Model):
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(TestModel, on_delete=models.CASCADE)


class TestM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(TestModel)


class TestUUIDModel(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    name = models.CharField(max_length=50, default='test data')


class TestUUIDForeignKey(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(TestUUIDModel, on_delete=models.CASCADE)


class TestUUIDM2M(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(TestUUIDModel)


class TestBigIntModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, default='test data')


class TestBigIntForeignKey(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(TestBigIntModel, on_delete=models.CASCADE)


class TestBigIntM2M(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(TestBigIntModel)
