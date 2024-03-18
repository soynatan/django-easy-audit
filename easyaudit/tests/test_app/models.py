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

class TestM2MProxy(TestM2M):
    class Meta:
        proxy=True

class TestMultiM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m_a = models.ManyToManyField(
            TestModel,
            related_name="testmultim2m_a"
    )
    test_m2m_b = models.ManyToManyField(
            TestModel,
            related_name="testmultim2m_b"
    )

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

class TestUUIDM2MProxy(TestUUIDM2M):
    class Meta:
        proxy=True

class TestMultiUUIDM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m_a = models.ManyToManyField(
            TestUUIDModel,
            related_name="testmultim2m_a"
    )
    test_m2m_b = models.ManyToManyField(
            TestUUIDModel,
            related_name="testmultim2m_b"
    )



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

class TestBigIntM2MProxy(TestBigIntM2M):
    class Meta:
        proxy=True

class TestBigIntMultiM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m_a = models.ManyToManyField(
            TestBigIntModel,
            related_name="testmultim2m_a"
    )
    test_m2m_b = models.ManyToManyField(
            TestBigIntModel,
            related_name="testmultim2m_b"
    )


