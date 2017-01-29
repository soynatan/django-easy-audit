# django-easy-audit

Yet another Django audit log app, hopefully the easiest one.

This app allows you to keep track of every action taken by your users.

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

3. Add django-easy-audit's middleware to your MIDDLEWARE (or MIDDLEWARE_CLASSES) setting like this:

  ```
  MIDDLEWARE = (
      ...
      'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
  )
  ```

4. Run `python manage.py migrate easyaudit` to create the app's models.

5. That's it! Now every CRUD event on your whole project will be registered in the audit models,
which you will be able to query from the Django admin app. Additionally, this app will also log
everytime a user logs in, out or fails to login.

## Settings

django-easy-audit allows some level of configuration. In your project's settings.py file,
you can define the following settings:

* `DJANGO_EASY_AUDIT_WATCH_LOGIN_EVENTS`

  Set to `False` it won't log your project's login events (log in, log out, and failed logins). Defaults to `True`.

* `DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_DEFAULT`

  The default list of classes django-easy-audit will ignore. Don't override this setting
  unless you know what you are doing; it may create an infinite loop and break your project.
  If you want django-easy-audit to stop logging one of your models please use the following setting.

* `DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA`

  A list of classes django-easy-audit will ignore. Use it to avoid logging some of your
  project's models if necessary. It can be a class or a string with `app_name.model_name`
  format. Defaults to `[]`.

## What does it do

django-easy-audit uses [Django signals](https://docs.djangoproject.com/en/dev/topics/signals/)
to listen to the events going on in your project, such as when a user creates, updates or deletes
a registry. This applies to every model of every app in your project.

When any of these events takes place, django-easy-audit will log it in the model `CRUDEvent`.
You can query this information in the Django Admin app.

Besides logging CRUD events, django-easy-audit will log every time a user logs in, out,
or fails to log in. This information is stored in the model `LoginEvent`.

## Why should I use it

There are many Django auditing apps out there, but most them require you to change very important
parts of your project's code. For example, they require you to add fields to your models, or make
them inherit from a certain class. Other apps create a mirror for each of your models, which means
duplicate migrations. Etc.

It is not that they don't work or that they are not great apps. But in case you need something
easier, and you don't want your project to depend so much on a third-party app, django-easy-audit
may be your best choice.

The good thing about this app is that it is easy and quick to install, and it begins logging
events right away, without you having to inject code anywhere in your project.

## To-Do

* Admin columns need to be polished, to display more meaningful information.
* Admin needs better filters.

## Contact

Find me on Twitter at [@soynatan](https://twitter.com/soynatan),
or send me an email to [natancalzolari@gmail.com](mailto:natancalzolari@gmail.com).

## Thanks

* [@jheld](https://github.com/jheld)

* [@sergeibershadsky](https://github.com/sergeibershadsky)
