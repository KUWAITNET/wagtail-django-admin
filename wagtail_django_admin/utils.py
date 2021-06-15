import re

from django.contrib import admin
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.admin import AdminSite
from django.utils.text import capfirst
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.apps.registry import apps


def reverse_no_i18n(viewname, *args, **kwargs):
    result = reverse(viewname, *args, **kwargs)
    m = re.match(r"(/[^/]*)(/.*$)", result)
    return m.groups()[1]


def url_no_i18n(url, *args, **kwargs):
    m = re.match(r"(/[^/]*)(/.*$)", url)
    return m.groups()[1]


def get_app_list(context, order=True):
    admin_site = get_admin_site(context)
    request = context["request"]

    app_dict = {}
    for model, model_admin in admin_site._registry.items():
        app_label = model._meta.app_label
        try:
            has_module_perms = model_admin.has_module_permission(request)
        except AttributeError:
            has_module_perms = True if not request else False

        if has_module_perms:
            if request:
                perms = model_admin.get_model_perms(request)
            else:
                perms = {
                    "add": True,
                    "change": True,
                    "delete": True,
                    "view": True,
                }

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                info = (app_label, model._meta.model_name)
                model_dict = {
                    "name": capfirst(model._meta.verbose_name_plural),
                    "object_name": model._meta.object_name,
                    "perms": perms,
                    "model_name": model._meta.model_name,
                }
                if perms.get("change", False):
                    try:
                        model_dict["admin_url"] = reverse_no_i18n(
                            "admin:%s_%s_changelist" % info, current_app=admin_site.name
                        )
                    except NoReverseMatch:
                        pass
                if perms.get("add", False):
                    try:
                        model_dict["add_url"] = reverse_no_i18n(
                            "admin:%s_%s_add" % info, current_app=admin_site.name
                        )
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]["models"].append(model_dict)
                else:
                    try:
                        name = apps.get_app_config(app_label).verbose_name
                    except NameError:
                        name = app_label.title()
                    app_dict[app_label] = {
                        "name": name,
                        "app_label": app_label,
                        "app_url": reverse_no_i18n(
                            "admin:app_list",
                            kwargs={"app_label": app_label},
                            current_app=admin_site.name,
                        ),
                        "has_module_perms": has_module_perms,
                        "models": [model_dict],
                    }

    # Sort the apps alphabetically.
    app_list = list(app_dict.values())

    if order:
        app_list.sort(key=lambda x: x["name"].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app["models"].sort(key=lambda x: x["name"])

    return app_list


def get_admin_site(context):
    try:
        current_resolver = resolve(context.get("request").path)
        index_resolver = resolve(
            reverse_no_i18n("%s:index" % current_resolver.namespaces[0])
        )

        if hasattr(index_resolver.func, "admin_site"):
            return index_resolver.func.admin_site

        for func_closure in index_resolver.func.__closure__:
            if isinstance(func_closure.cell_contents, AdminSite):
                return func_closure.cell_contents
    except:
        pass

    return admin.site
