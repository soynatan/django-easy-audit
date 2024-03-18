import csv
import datetime

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .admin_helpers import EasyAuditModelAdmin, prettify_json
from .models import CRUDEvent, LoginEvent, RequestEvent
from .settings import (
    ADMIN_SHOW_AUTH_EVENTS,
    ADMIN_SHOW_MODEL_EVENTS,
    ADMIN_SHOW_REQUEST_EVENTS,
    CRUD_EVENT_LIST_FILTER,
    CRUD_EVENT_SEARCH_FIELDS,
    LOGIN_EVENT_LIST_FILTER,
    LOGIN_EVENT_SEARCH_FIELDS,
    REQUEST_EVENT_LIST_FILTER,
    REQUEST_EVENT_SEARCH_FIELDS,
)


@admin.display(description="Export to CSV")
def export_to_csv(modeladmin, request, queryset):
    """Export event audits to csv."""
    opts = modeladmin.model._meta
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment;filename={opts.verbose_name}.csv"
    writer = csv.writer(response)
    fields = [
        field
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            data_row.append(value)
        writer.writerow(data_row)

    return response


# CRUD events
class CRUDEventAdmin(EasyAuditModelAdmin):
    list_display = [
        "get_event_type_display",
        "get_content_type",
        "object_id",
        "object_repr_link",
        "user_link",
        "datetime",
    ]
    date_hierarchy = "datetime"
    list_filter = CRUD_EVENT_LIST_FILTER
    search_fields = CRUD_EVENT_SEARCH_FIELDS
    readonly_fields = [
        "event_type",
        "object_id",
        "get_content_type",
        "object_repr",
        "object_json_repr_prettified",
        "get_user",
        "user_pk_as_string",
        "datetime",
        "changed_fields_prettified",
    ]
    exclude = ["object_json_repr", "changed_fields"]

    def get_changelist_instance(self, *args, **kwargs):
        changelist_instance = super().get_changelist_instance(*args, **kwargs)
        content_type_ids = [obj.content_type_id for obj in changelist_instance.result_list]
        self.content_types_by_id = {
            ct.id: ct for ct in ContentType.objects.filter(id__in=content_type_ids)
        }
        return changelist_instance

    @admin.display(description="Content Type")
    def get_content_type(self, obj):
        return self.content_types_by_id[obj.content_type_id]

    @admin.display(description="User")
    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    @admin.display(description="object repr")
    def object_repr_link(self, obj):
        if obj.event_type == CRUDEvent.DELETE:
            html = obj.object_repr
        else:
            escaped_obj_repr = escape(obj.object_repr)
            try:
                content_type = self.get_content_type(obj)
                url = reverse(
                    f"admin:{content_type.app_label}_{content_type.model}_change",
                    args=(obj.object_id,),
                )
                html = f'<a href="{url}">{escaped_obj_repr}</a>'
            except Exception:
                html = escaped_obj_repr
        return mark_safe(html)  # noqa: S308

    @admin.display(description="object json repr")
    def object_json_repr_prettified(self, obj):
        return prettify_json(obj.object_json_repr)

    @admin.display(description="changed fields")
    def changed_fields_prettified(self, obj):
        return prettify_json(obj.changed_fields)

    actions = [export_to_csv]


# Login events
class LoginEventAdmin(EasyAuditModelAdmin):
    list_display = [
        "datetime",
        "get_login_type_display",
        "user_link",
        "get_username",
        "remote_ip",
    ]
    date_hierarchy = "datetime"
    list_filter = LOGIN_EVENT_LIST_FILTER
    search_fields = LOGIN_EVENT_SEARCH_FIELDS
    readonly_fields = [
        "login_type",
        "get_username",
        "get_user",
        "remote_ip",
        "datetime",
    ]

    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    get_user.short_description = "User"

    def get_username(self, obj):
        user = self.get_user(obj)
        return user.get_username() if user else None

    get_username.short_description = "User name"

    actions = [export_to_csv]


# Request events
class RequestEventAdmin(EasyAuditModelAdmin):
    list_display = ["datetime", "user_link", "method", "url", "remote_ip"]
    date_hierarchy = "datetime"
    list_filter = REQUEST_EVENT_LIST_FILTER
    search_fields = REQUEST_EVENT_SEARCH_FIELDS
    readonly_fields = [
        "url",
        "method",
        "query_string",
        "get_user",
        "remote_ip",
        "datetime",
    ]

    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    get_user.short_description = "User"

    actions = [export_to_csv]


if ADMIN_SHOW_MODEL_EVENTS:
    admin.site.register(CRUDEvent, CRUDEventAdmin)
if ADMIN_SHOW_AUTH_EVENTS:
    admin.site.register(LoginEvent, LoginEventAdmin)
if ADMIN_SHOW_REQUEST_EVENTS:
    admin.site.register(RequestEvent, RequestEventAdmin)
