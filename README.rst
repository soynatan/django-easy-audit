=================
django-easy-audit
=================

Yet another Django audit log app, hopefully the simplest one.

Quick start
-----------

1. Add "djangoeasyaudit" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'djangoeasyaudit',
    ]

2. Add django-easy-audit's middleware to your MIDDLEWARE_CLASSES setting like this::

    MIDDLEWARE_CLASSES = (
        ...
        'djangoeasyaudit.middleware.djangoeasyaudit.DjangoEasyAuditMiddleware',
    )

3. Run 'python manage.py migrate djangoeasyaudit' to create the audit models.

4. That's it! Now every CRUD event on your whole project will be registered in the audit logs, which you will be able to query from the Django admin app. Additionally, this app will also log everytime a user logs in, out or fails to login.
