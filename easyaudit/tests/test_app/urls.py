from django.conf.urls import url
from test_app import views


urlpatterns = [
    url("create-obj/", views.create_obj_view, name="create-obj"),
]
