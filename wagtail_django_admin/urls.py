import django

try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url

from django.views.i18n import JavaScriptCatalog

javascript_catalog = JavaScriptCatalog.as_view()


app_name = "wagtail_django_admin"

urlpatterns = [
    url(
        r"^jsi18n/$",
        javascript_catalog,
        {"packages": "django.contrib.admin+wagtail_django_admin"},
        name="jsi18n",
    ),
]

if django.VERSION[:2] < (1, 8):
    from django.conf.urls import patterns

    urlpatterns = patterns("", *urlpatterns)
