from urllib.parse import urlencode

from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _


class BaseProcessActionsAdminMixin:
    def get_action_methods(self):
        return {}

    def _get_path_info(self):
        return self.model._meta.app_label, self.model._meta.model_name

    def get_redirect_url__to_referer(self, request: HttpRequest):
        preserved_filters = self.get_preserved_filters(request)
        opts = self.model._meta

        return add_preserved_filters(
            {"preserved_filters": preserved_filters, "opts": opts},
            request.META.get("HTTP_REFERER", "/"),
        )

    def process_action(
        self,
        request,
        obj_id,
        action_key,
        **kwargs,
    ):
        action_methods = self.get_action_methods()
        action = action_methods[action_key]
        obj = self.get_object(request, obj_id)
        return action(request, obj)


class CRUDHistoryAdminMixin(BaseProcessActionsAdminMixin, admin.ModelAdmin):
    CRUD_HISTORY = "crud_history"
    crud_history_translated_title = _("CRUD history")

    def get_urls(self) -> list:
        urls = super().get_urls()
        info = self._get_path_info()
        crud_history_urls = [
            path(
                f"<path:object_id>/{self.CRUD_HISTORY}/",
                self.admin_site.admin_view(self.crud_history_view),
                name=f"%s_%s_{self.CRUD_HISTORY}" % info,
            )
        ]
        return crud_history_urls + urls

    def get_action_methods(self) -> dict:
        methods = super().get_action_methods()
        methods.update({self.CRUD_HISTORY: self.crud_history_action})
        return methods

    def crud_history_view(self, request: HttpRequest, object_id: int):
        return self.process_action(request, object_id, self.CRUD_HISTORY)

    def crud_history_action(self, request: HttpRequest, obj: Model) -> HttpResponseRedirect:
        base_history_url = reverse(
            "admin:easyaudit_crudevent_changelist",
        )
        app_label, model_name = self._get_path_info()
        content_type = ContentType.objects.get_by_natural_key(app_label, model_name)
        params = {"content_type__id": content_type.id, "object_id": obj.id}
        params = urlencode(params)
        history_url = f"{base_history_url}?{params}"

        return redirect(history_url)

    crud_history_action.short_description = crud_history_translated_title

    def get_crud_history_url(self, obj: Model) -> str:
        info = self._get_path_info()
        return reverse(f"admin:%s_%s_{self.CRUD_HISTORY}" % info, args=[obj.pk])

    def crud_history_link(self, obj: Model) -> str:
        crud_history_url = self.get_crud_history_url(obj=obj)
        crud_history_a = (
            f"<a href={crud_history_url}>> {self.crud_history_translated_title}</a>"
        )
        return format_html(crud_history_a)

    crud_history_link.allow_tags = True
    crud_history_link.short_description = crud_history_translated_title


# Example
class SomeModelAdmin(CRUDHistoryAdminMixin):
    list_display = (
        "id",
        "crud_history_link",
    )
