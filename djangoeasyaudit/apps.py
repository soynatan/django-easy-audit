from django.apps import AppConfig

class DjangoEasyAuditConfig(AppConfig):
    name = 'djangoeasyaudit'
    verbose_name = 'Django Easy Audit Application'

    def ready(self):
        import djangoeasyaudit.signals