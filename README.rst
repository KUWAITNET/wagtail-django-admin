wagtail-django-admin
====================

Installation
------------

from GitHub:

.. code:: sh

   $ pip install -e git+https://github.com/KuwaitNET/wagtail-django-admin.git#egg=wagtail_django_admin


Usage
-----

1. Add ``wagtail_django_admin`` before ``wagtail.admin`` at the end of your ``INSTALLED_APPS``.

.. code:: python

   INSTALLED_APPS = [
      ...
      "wagtail_django_admin",
      "django.contrib.admin",
      "wagtail.admin",
   ]

1. In ``settings.py`` you can add the following settings (OPTIONAL). If not defined all apps and all models are considered

.. code:: python

   WAGTAIL_ADMIN_CUSTOM_MENU = {
      "<app_name>": [..., "<model_name>", ...]
   }


More advanced option if you want to control the order and icon_name

.. code:: python

   WAGTAIL_ADMIN_CUSTOM_MENU = {
      "<app_name>": [
         ...
         {
            "order": 200,
            "icon_name": "list-ul",
            "models": {
               ...
               "<model_name>": {"order": 200, "icon_name": "mail"},
               ...
            },
         }
         ...
      ]
   }

3. In project ``urls.py`` add the following line:
   
.. code:: python

   path("^wagtail_django_admin/", include("wagtail_django_admin.urls", "wagtail_django_admin")),
