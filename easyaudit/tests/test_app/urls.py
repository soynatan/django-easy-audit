from django.urls import re_path
from test_app import views

app_name = 'test_easyaudit'

urlpatterns = [
    re_path("index", views.index, name="index"),
    re_path("create-obj", views.create_obj_view, name="create-obj"),
    re_path("update-obj", views.update_obj_view, name="update-obj"),

    re_path("create-uuid-obj", views.create_uuid_obj_view, name="create-uuid-obj"),
    re_path("update-uuid-obj", views.update_uuid_obj_view, name="update-uuid-obj"),

    re_path("create-big-obj", views.create_big_obj_view, name="create-big-obj"),
    re_path("update-big-obj", views.update_big_obj_view, name="update-big-obj"),
]
