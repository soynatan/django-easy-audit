from django.apps import AppConfig

class EasyAuditConfig(AppConfig):
    name = 'easyaudit'
    verbose_name = 'Easy Audit Application'

    def ready(self):
        import easyaudit.signals