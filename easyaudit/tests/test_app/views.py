from datetime import datetime

from django.http import HttpResponse
from test_app.models import TestModel, TestUUIDModel, TestBigIntModel


def create_obj(Model):
    return Model.objects.create()


def update_obj(Model, pk, name):
    tm = Model.objects.get(pk=pk)
    tm.name = name
    tm.save()
    return tm


def create_obj_view(request):
    return HttpResponse(create_obj(TestModel).id)


def update_obj_view(request):
    name = datetime.now().isoformat()
    return HttpResponse(update_obj(
        TestModel, request.GET['id'], name
    ).id)


def create_uuid_obj_view(request):
    return HttpResponse(create_obj(TestUUIDModel).id)


def update_uuid_obj_view(request):
    name = datetime.now().isoformat()
    return HttpResponse(update_obj(
        TestUUIDModel, request.GET['id'], name
    ).id)


def create_big_obj_view(request):
    return HttpResponse(create_obj(TestBigIntModel).id)


def update_big_obj_view(request):
    name = datetime.now().isoformat()
    return HttpResponse(update_obj(
        TestBigIntModel, request.GET['id'], name
    ).id)
