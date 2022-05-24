from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class EasyAuditConfig(AppConfig):
    name = 'easyaudit'
    verbose_name = _('Easy Audit Application')
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from easyaudit.signals import auth_signals, model_signals, request_signals