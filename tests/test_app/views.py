from datetime import datetime, timezone

from django.http import HttpResponse

from tests.test_app.models import BigIntModel, Model, UUIDModel


def create_obj(model):
    return model.objects.create()


def update_obj(model, pk, name):
    tm = model.objects.get(pk=pk)
    tm.name = name
    tm.save()
    return tm


def create_obj_view(request):
    obj = create_obj(Model)
    return HttpResponse(obj.id)


def index(request):
    return HttpResponse()


def update_obj_view(request):
    name = datetime.now(timezone.utc).isoformat()
    return HttpResponse(update_obj(Model, request.GET["id"], name).id)


def create_uuid_obj_view(request):
    return HttpResponse(create_obj(UUIDModel).id)


def update_uuid_obj_view(request):
    name = datetime.now(timezone.utc).isoformat()
    return HttpResponse(update_obj(UUIDModel, request.GET["id"], name).id)


def create_big_obj_view(request):
    return HttpResponse(create_obj(BigIntModel).id)


def update_big_obj_view(request):
    name = datetime.now(timezone.utc).isoformat()
    return HttpResponse(update_obj(BigIntModel, request.GET["id"], name).id)
