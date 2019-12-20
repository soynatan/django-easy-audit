from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.shortcuts import render

try: # Django 2.0
    from django.urls import reverse
except: # Django < 2.0
    from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.conf.urls import url
from django.utils.safestring import mark_safe
from . import settings

import json


def prettify_json(json_string):
    """Given a JSON string, it returns it as a
    safe formatted HTML"""
    try:
        data = json.loads(json_string)
        html = '<pre>' + json.dumps(data, sort_keys=True, indent=4) + '</pre>'
    except:
        html = json_string
    return mark_safe(html)


class EasyAuditModelAdmin(admin.ModelAdmin):

    def user_link(self, obj):
        user = get_user_model().objects.filter(id=obj.user_id).first()
        #return mark_safe(get_user_link(user))
        if user is None:
            return '-'
        try:
            user_model = get_user_model()
            url = reverse("admin:%s_%s_change" % (
                user_model._meta.app_label,
                user_model._meta.model_name,
            ), args=(user.id,))
            html = '<a href="%s">%s</a>' % (url, str(user))
        except:
            html = str(user)
        return mark_safe(html)
    user_link.short_description = 'user'

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(EasyAuditModelAdmin, self).get_urls()
        my_urls = [
            url(r'^purge/$', self.admin_site.admin_view(self.purge), {}, name="%s_%s_purge" % info),
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
