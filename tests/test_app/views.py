from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from easyaudit.models import RequestEvent
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


def count_request_events_view(request):
    return HttpResponse(RequestEvent.objects.count())


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


def token_auth_view(request):
    """Authenticate inside the view, the way Django REST framework does.

    DRF resolves the user in the view layer and writes the result through to the
    underlying ``HttpRequest`` as ``request.user`` and ``request.auth``. This view
    does the same with a fake ``Token <username>`` scheme, so the test suite needs
    no dependency on DRF.
    """
    scheme, _, username = request.META.get("HTTP_AUTHORIZATION", "").partition(" ")
    user = None
    if scheme == "Token":
        user = get_user_model().objects.filter(username=username).first()

    if user is None:
        request.user = AnonymousUser()
        request.auth = None
        return HttpResponse(status=401)

    request.user = user
    request.auth = username
    return HttpResponse()
