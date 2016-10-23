# django-easy-audit

Yet another Django audit log app, hopefully the simplest one.

## Quickstart

1. Install django-easy-audit by running: `pip install django-easy-audit`

   *Alternatively, you can download the code from Github,
   and place the folder 'easyaudit' in the root of your project.*

2. Add "easyaudit" to your INSTALLED_APPS setting like this:

  ```
  INSTALLED_APPS = [
      ...
      'easyaudit',
  ]
  ```

3. Add django-easy-audit's middleware to your MIDDLEWARE_CLASSES setting like this:

  ```
  MIDDLEWARE_CLASSES = (
      ...
      'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
  )
  ```

4. Run `python manage.py migrate easyaudit` to create the audit models.

5. That's it! Now every CRUD event on your whole project will be registered in the audit models,
which you will be able to query from the Django admin app. Additionally, this app will also log
everytime a user logs in, out or fails to login.

## What it does

django-easy-audit uses [Django signals](https://docs.djangoproject.com/en/dev/topics/signals/)
to listen to the events going on in your project, such as when a user creates, updates or deletes
a registry. This applies to every model of every app your project is using.

When any of these events takes place, django-easy-audit will log it in the model `CRUDEvent`.

Besides logging CRUD events, django-easy-audit will log every time your users log in, out,
or fail to log in. This information is stored in the model `LoginEvent`.

You can query this information in the Django Admin app.
