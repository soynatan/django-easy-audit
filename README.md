# django-easy-audit

Yet another Django audit log app, hopefully the easiest one.

This app allows you to keep track of every action taken by your users.

## Quickstart

1. Install Django Easy Audit by running `pip install django-easy-audit`.

   *Alternatively, you can download the [latest release](https://github.com/soynatan/django-easy-audit/releases) from GitHub, unzip it, and place the folder 'easyaudit' in the root of your project.*

2. Add 'easyaudit' to your `INSTALLED_APPS` like this:

    ```python
    INSTALLED_APPS = [
        ...
        'easyaudit',
    ]
    ```

3. Add Easy Audit's middleware to your `MIDDLEWARE` (or `MIDDLEWARE_CLASSES`) setting like this:

    ```python
    MIDDLEWARE = (
        ...
        'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
    )
    ```

4. Run `python manage.py migrate easyaudit` to create the app's models.

5. That's it! Now every CRUD event on your whole project will be registered in the audit models, which you will be able to query from the Django admin app. Additionally, this app will also log all authentication events and all URLs requested.

## Settings

For an exhaustive list of available settings, please [check our wiki](https://github.com/soynatan/django-easy-audit/wiki/Settings).

Below are some of the settings you may want to use. These should be defined in your project's `settings.py` file:

* `DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS`

* `DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS`

* `DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS`

  Set these to `False` to stop logging model, authentication, and/or request events.

* `DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA`

  A list of Django models which will be ignored by Django Easy Audit.
  Use it to prevent logging one or more of your project's models.
  List items can be classes or strings with `app_name.model_name` format.

* `DJANGO_EASY_AUDIT_UNREGISTERED_URLS_EXTRA`

  A list of URLs which will be ignored by Django Easy Audit.
  List items are expected to be regular expressions that
  will be matched against the URL path.
  [Check our wiki](https://github.com/soynatan/django-easy-audit/wiki/Settings#request-auditing)
  for more details on how to use it.

## What does it do

Django Easy Audit uses [Django signals](https://docs.djangoproject.com/en/dev/topics/signals/)
to listen to the events happenning in your project, such as when a user creates, updates or deletes
a registry. This applies to every model of every app in your project.

When any of these events takes place, Django Easy Audit will log it in the model `CRUDEvent`.
You can query this information in the Django Admin app.

Besides logging CRUD events, Django Easy Audit will log all authentication events (such as when a user logs in, out, or fails to log in) and all the URLs requested in the project. This information is stored in models `LoginEvent` and `RequestEvent`.

## Why you should use it

There are many Django auditing apps out there, but most them require you to change very important
parts of your project's code. For example, they require you to add fields to your models, or make
them inherit from a certain class. Some of them create a mirror for each of your models, which means
duplicate migrations.

It is not that they don't work or that they are not great apps. But in case you need something
easier to set up, and you don't want your code to depend so much on a third-party app, Django Easy Audit
may be your best choice.

The good thing about this app is that it doesn't get in the way. It is [easy and quick to install](https://github.com/soynatan/django-easy-audit/wiki/Installation), and it
begins logging everything right away, without you having to inject code anywhere in your project.

## Contact

Find me on Twitter at [@soynatan](https://twitter.com/soynatan),
or send me an email to [natancalzolari@gmail.com](mailto:natancalzolari@gmail.com).
