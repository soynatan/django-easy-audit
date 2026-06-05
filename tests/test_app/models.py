import uuid

from django.db import models
from django.utils import timezone


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


class Tag(models.Model):
    name = models.CharField(max_length=50)


class Article(models.Model):
    title = models.CharField(max_length=200)
    tags = models.ManyToManyField(Tag, blank=True)


class MetadataAModel(models.Model):
    name = models.CharField(max_length=50, default="metadata A")


class MetadataBModel(models.Model):
    name = models.CharField(max_length=50, default="metadata B")

    model_a = models.ForeignKey(MetadataAModel, on_delete=models.CASCADE)

    def get_easyaudit_metadata(self, changed_fields):
        metadata = {"model_a_id": self.model_a_id}

        if changed_fields and "name" in changed_fields:
            metadata.update({"last_name_change": str(timezone.now())})

        return metadata


class MetadataCModel(models.Model):
    EASY_AUDIT_METADATA_METHOD = "fetch_metadata"

    name = models.CharField(max_length=50, default="metadata C")

    model_b = models.ForeignKey(MetadataBModel, on_delete=models.CASCADE)

    def fetch_metadata(self, *args, **kwargs):
        return {
            "model_a_id": self.model_b.model_a_id,
            "model_b_id": self.model_b.id,
        }
