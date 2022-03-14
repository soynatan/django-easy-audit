from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.shortcuts import render

try: # Django 2.0
    from django.urls import reverse
except: # Django < 2.0
    from django.core.urlresolvers import reverse

from django.urls import re_path
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.html import escape
from . import settings

import json


def prettify_json(json_string):
    """Given a JSON string, it returns it as a
    safe formatted HTML"""
    escaped = escape(json_string)
    try:
        data = json.loads(escaped)
        # html = '<pre>' + json.dumps(data, sort_keys=True, indent=4) + '</pre>'
        html = json.dumps(data, sort_keys=True, indent=4)
    except Exception:
        html = escaped
    return html


class EasyAuditModelAdmin(admin.ModelAdmin):
    def get_changelist_instance(self, *args, **kwargs):
        changelist_instance = super().get_changelist_instance(*args, **kwargs)
        user_ids = [obj.user_id for obj in changelist_instance.result_list]
        self.users_by_id = {user.id: user for user in get_user_model().objects.filter(id__in=user_ids)}
        return changelist_instance

    def get_readonly_fields(self, request, obj=None):
        "Mark all fields of model as readonly if configured to do so."
        if settings.READONLY_EVENTS:
            return [f.name for f in self.model._meta.get_fields()]
        else:
            return self.readonly_fields

    def user_link(self, obj):
        user = self.users_by_id.get(obj.user_id)
        #return mark_safe(get_user_link(user))
        if user is None:
            return '-'
        escaped = escape(str(user))
        try:
            user_model = get_user_model()
            url = reverse("admin:%s_%s_change" % (
                user_model._meta.app_label,
                user_model._meta.model_name,
            ), args=(user.id,))
            html = '<a href="%s">%s</a>' % (url, escaped)
        except Exception:
            html = escaped
        return mark_safe(html)
    user_link.short_description = 'user'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if settings.READONLY_EVENTS:
            return False
        return super().has_delete_permission(request, obj)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(EasyAuditModelAdmin, self).get_urls()
        my_urls = [
            re_path(r'^purge/$', self.admin_site.admin_view(self.purge), {}, name="%s_%s_purge" % info),
        ]
        return my_urls + urls

    def purge(self, request):
        return self.purge_objects(request)

    # Helper view to remove all rows in a table
    def purge_objects(self, request):
        """
        Removes all objects in this table.
        This action first displays a confirmation page;
        next, it deletes all objects and redirects back to the change list.
        """

        if settings.READONLY_EVENTS:
            raise PermissionDenied

        def truncate_table(model):
            if settings.TRUNCATE_TABLE_SQL_STATEMENT:
                from django.db import connection
                sql = settings.TRUNCATE_TABLE_SQL_STATEMENT.format(db_table=model._meta.db_table)
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
        if request.method == 'POST':
            if 'btn-confirm' in request.POST:
                try:
                    n = modeladmin.model.objects.count()
                    truncate_table(modeladmin.model)
                    modeladmin.message_user(request, _("Successfully removed %d rows" % n), messages.SUCCESS);
                except Exception as e:
                    modeladmin.message_user(request, _(u'ERROR') + ': %r' % e, messages.ERROR)
            else:
                modeladmin.message_user(request, _("Action cancelled by user"), messages.SUCCESS);
            return HttpResponseRedirect(reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name)))

        context = {
            "title": _("Purge all %s ... are you sure?") % opts.verbose_name_plural,
            "opts": opts,
            "app_label": opts.app_label,
        }

        # Display the confirmation page
        return render(
            request,
            'admin/easyaudit/purge_confirmation.html',
            context
        )
