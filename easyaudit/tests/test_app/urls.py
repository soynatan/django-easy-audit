from django.conf.urls import url
from test_app import views

app_name = 'test_easyaudit'

urlpatterns = [
    url("index", views.index, name="index"),
    url("create-obj", views.create_obj_view, name="create-obj"),
    url("update-obj", views.update_obj_view, name="update-obj"),

    url("create-uuid-obj", views.create_uuid_obj_view, name="create-uuid-obj"),
    url("update-uuid-obj", views.update_uuid_obj_view, name="update-uuid-obj"),

    url("create-big-obj", views.create_big_obj_view, name="create-big-obj"),
    url("update-big-obj", views.update_big_obj_view, name="update-big-obj"),
]
