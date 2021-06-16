django-fsm-wagtail
==================

Mixin to integrate django-fsm_ state transitions into the
Wagtail Admin.


Installation
------------

from GitHub:

.. code:: sh

   $ pip install -e git://github.com/abahnihi/wagtail-django-admin.git#egg=wagtail-django-admin


Usage
-----

1. Add ``grappelli``, ``wagtail_django_admin`` then ``django.contrib.admin`` at the end of your ``INSTALLED_APPS``.

.. code:: python

   INSTALLED_APPS = [
      ...
      "wagtail_django_admin",
      "grappelli",
      "django.contrib.admin",
   ]

2. In ``settings.py`` you can add the following settings (OPTIONAL). If not defined all apps and all models are considered

.. code:: python

   WAGTAIL_ADMIN_CUSTOM_MENU = {
      "<app_name>": [..., "<model_name>", ...]
   }

