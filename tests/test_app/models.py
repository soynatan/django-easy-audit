# ruff: noqa: A003
import uuid

from django.db import models

from .managers import SoftDeleteManager


class Model(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default="test data")


class ForeignKeyModel(models.Model):
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(Model, on_delete=models.CASCADE)


class M2MModel(models.Model):
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(Model)


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50, default="test data")


class UUIDForeignKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(UUIDModel, on_delete=models.CASCADE)


class UUIDM2MModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(UUIDModel)


class BigIntModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, default="test data")


class BigIntForeignKeyModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(BigIntModel, on_delete=models.CASCADE)


class BigIntM2MModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(BigIntModel)


class CustomManagerModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, default="test data")
    deleted = models.BooleanField(default=False)

    all_objects = models.Manager()
    objects = SoftDeleteManager()
