import uuid

from django.db import models


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


class VisibleOnlyManager(models.Manager):
    """Manager hiding some rows, the way soft-delete managers do."""

    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)


class HidableModel(models.Model):
    """Model whose default manager filters rows out. See issue #175."""

    name = models.CharField(max_length=50, default="test data")
    hidden = models.BooleanField(default=False)

    objects = VisibleOnlyManager()


class Tag(models.Model):
    name = models.CharField(max_length=50)


class Article(models.Model):
    title = models.CharField(max_length=200)
    tags = models.ManyToManyField(Tag, blank=True)
