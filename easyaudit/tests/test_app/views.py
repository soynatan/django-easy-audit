from django.http import HttpResponse
from test_app.models import TestModel


def create_obj_view(request):
    return HttpResponse(TestModel.objects.create().id)
