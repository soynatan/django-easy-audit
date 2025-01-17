from django.contrib import admin
from easyaudit.crudhistory_admin_mixin import CRUDHistoryAdminMixin


from tests.test_app.models import Model


@admin.register(Model)
class ModelCRUDHistoryAdmin(CRUDHistoryAdminMixin):
    list_display = (
        "id",
        "crud_history_link",
    )
