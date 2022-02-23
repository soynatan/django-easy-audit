from django.apps import AppConfig

class EasyAuditConfig(AppConfig):
    name = 'easyaudit'
    verbose_name = 'Easy Audit Application'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from easyaudit.signals import auth_signals, model_signals, request_signals