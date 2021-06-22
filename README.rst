wagtail-django-admin
====================

Installation
------------

from GitHub:

.. code:: sh

   $ pip install -e git+https://github.com/abahnihi/wagtail-django-admin.git#egg=wagtail_django_admin


Usage
-----

1. Add ``wagtail_django_admin`` then ``django.contrib.admin`` at the end of your ``INSTALLED_APPS``.

.. code:: python

   INSTALLED_APPS = [
      ...
      "wagtail_django_admin",
      "django.contrib.admin",
   ]

2. In ``settings.py`` you can add the following settings (OPTIONAL). If not defined all apps and all models are considered

.. code:: python

   WAGTAIL_ADMIN_CUSTOM_MENU = {
      "<app_name>": [..., "<model_name>", ...]
   }

3. In project ``urls.py`` add the following line:
   
.. code:: python

   path("^wagtail_django_admin/", include("wagtail_django_admin.urls", "wagtail_django_admin")),

