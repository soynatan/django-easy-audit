from django.http import HttpResponse
from test_app.models import TestModel
import pdb


def create_obj_view(request):
    return HttpResponse(TestModel.objects.create().id)


def update_obj_view(request):
    tm = TestModel.objects.get(pk=request.GET['id'])
    tm.name = request.GET['id']
    tm.save()
    return HttpResponse(tm.id)
