from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EasyAuditConfig(AppConfig):
    name = 'easyaudit'
<<<<<<< HEAD
    verbose_name = _('Easy Audit Application')
=======
    verbose_name = 'Easy Audit Application'
    default_auto_field = 'django.db.models.AutoField'
>>>>>>> ef5c3c73004a9e3a1bfc53da64f6f3c16da60fba

    def ready(self):
        from easyaudit.signals import auth_signals, model_signals, request_signals
