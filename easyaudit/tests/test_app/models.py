from django.db import models, transaction


class TestModel(models.Model):
    name = models.CharField(max_length=50, default='test data')


class TestForeignKey(models.Model):
    name = models.CharField(max_length=50)
    test_fk = models.ForeignKey(TestModel, on_delete=models.CASCADE)


class TestM2M(models.Model):
    name = models.CharField(max_length=50)
    test_m2m = models.ManyToManyField(TestModel)


@transaction.atomic
def create_in_transaction():
    m = TestModel.objects.create(name='Transaction')
    fk = TestForeignKey.objects.create(name='TransactionFK', test_fk=m)
    m2m = TestM2M(name='TrasactionM2M')
    m2m.save()
    m2m.test_m2m.add(m)
    m2m.save()

    return m
