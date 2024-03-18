import json

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import re_path, reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .settings import READONLY_EVENTS, TRUNCATE_TABLE_SQL_STATEMENT


def prettify_json(json_string):
    """Given a JSON string, it returns it as a safe formatted HTML."""
    escaped = escape(json_string)
    try:
        data = json.loads(escaped)
        html = json.dumps(data, sort_keys=True, indent=4)
    except Exception:
        html = escaped
    return html


class EasyAuditModelAdmin(admin.ModelAdmin):
    def get_changelist_instance(self, *args, **kwargs):
        changelist_instance = super().get_changelist_instance(*args, **kwargs)
        user_ids = [obj.user_id for obj in changelist_instance.result_list]
        self.users_by_id = {
            user.id: user for user in get_user_model().objects.filter(id__in=user_ids)
        }
        return changelist_instance

    def get_readonly_fields(self, request, obj=None):
        """Mark all fields of model as readonly if configured to do so."""
        if READONLY_EVENTS:
            return [f.name for f in self.model._meta.get_fields()]
        return self.readonly_fields

    @admin.display(description="User")
    def user_link(self, obj):
        user = self.users_by_id.get(obj.user_id)
        if user is None:
            return "-"
        escaped = escape(str(user))
        try:
            user_model = get_user_model()
            url = reverse(
                f"admin:{user_model._meta.app_label}_{user_model._meta.model_name}_change"
            )
            html = f'<a href="{url}">{escaped}</a>'
            html = f'<a href="{url}">{escaped}</a>'
        except Exception:
            html = escaped
        return mark_safe(html)  # noqa: S308

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if READONLY_EVENTS:
            return False
        return super().has_delete_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            re_path(
                r"^purge/$",
                self.admin_site.admin_view(self.purge),
                {},
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_purge",
            ),
        ]
        return my_urls + urls

    def purge(self, request):
        return self.purge_objects(request)

    # Helper view to remove all rows in a table
    def purge_objects(self, request):
        """Remove all objects in this table.

        This action first displays a confirmation page; next, it deletes all objects and
        redirects back to the change list.
        """
        if READONLY_EVENTS:
            raise PermissionDenied

        def truncate_table(model):
            if TRUNCATE_TABLE_SQL_STATEMENT:
                from django.db import connection

                sql = TRUNCATE_TABLE_SQL_STATEMENT.format(db_table=model._meta.db_table)
                cursor = connection.cursor()
                cursor.execute(sql)
            else:
                model.objects.all().delete()

        modeladmin = self
        opts = modeladmin.model._meta

        # Check that the user has delete permission for the actual model
        if not request.user.is_superuser:
            raise PermissionDenied
        if not modeladmin.has_delete_permission(request):
            raise PermissionDenied

        # If the user has already confirmed or cancelled the deletion,
        # (eventually) do the deletion and return to the change list view again.
        if request.method == "POST":
            if "btn-confirm" in request.POST:
                try:
                    n = modeladmin.model.objects.count()
                    truncate_table(modeladmin.model)
                    modeladmin.message_user(
                        request, _("Successfully removed %d rows" % n), messages.SUCCESS
                    )
                except Exception as e:
                    modeladmin.message_user(
                        request, _("ERROR") + ": %r" % e, messages.ERROR
                    )
            else:
                modeladmin.message_user(
                    request, _("Action cancelled by user"), messages.SUCCESS
                )
            return HttpResponseRedirect(
                reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
            )

        context = {
            "title": _("Purge all %s ... are you sure?") % opts.verbose_name_plural,
            "opts": opts,
            "app_label": opts.app_label,
        }

        # Display the confirmation page
        return render(request, "admin/easyaudit/purge_confirmation.html", context)
