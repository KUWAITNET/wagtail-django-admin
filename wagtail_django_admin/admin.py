from django.utils.translation import gettext_lazy as _, activate
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model

from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu
from wagtail_django_admin.utils import get_app_list

from .utils import url_no_i18n


User = get_user_model()


class CustomSubmenuMenuItem(SubmenuMenuItem):
    template = "wagtail_django_admin/menu_submenu_item.html"

    def get_context(self, request):
        context = super().get_context(request)
        context["menu_html"] = self.menu.render_html(request)
        context["request"] = request
        return context


class CustomMenuItem(MenuItem):
    template = "wagtail_django_admin/menu_item.html"

    def get_context(self, request):
        """Defines context for the template, overridable to use more data"""
        if "all_allowed_url" in request.session:
            all_allowed_url = request.session["all_allowed_url"]
        else:
            all_allowed_url = (
                request.user.all_allowed_url(request=request)
                if request.user.is_staff
                else []
            )

            request.session["all_allowed_url"] = all_allowed_url
        return {
            "name": self.name,
            "url": self.url,
            "classnames": self.classnames,
            "icon_name": self.icon_name,
            "attr_string": self.attr_string,
            "label": self.label,
            "active": self.is_active(request),
            "has_permission": self.url in all_allowed_url,
        }

    def is_active(self, request):
        return url_no_i18n(url=request.path).startswith(str(self.url))


app_list = get_app_list(context={"request": None})


for app in app_list:
    app_name = str(app["app_label"])
    app_menu_name = str(app["name"])
    WAGTAIL_ADMIN_CUSTOM_MENU = getattr(
        django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU", {}
    )
    WAGTAIL_ADMIN_DEFAULT_MENU_LANG = (
        django_settings.WAGTAIL_ADMIN_DEFAULT_MENU_LANG
        if hasattr(django_settings, "WAGTAIL_ADMIN_DEFAULT_MENU_LANG")
        else None
    )
    if WAGTAIL_ADMIN_DEFAULT_MENU_LANG:
        activate(WAGTAIL_ADMIN_DEFAULT_MENU_LANG)
    all_apps = WAGTAIL_ADMIN_CUSTOM_MENU.keys()
    if (
        hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
        and type(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU) is dict
        and app_name in all_apps
    ) or not hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU"):
        wagtail_django_admin_menu = Menu(
            register_hook_name="register_wagtail_django_admin_menu_item" + app_name,
            construct_hook_name="construct_main_menu",
        )

        @hooks.register("register_admin_menu_item")
        def register_wagtail_django_admin_menu(
            app_name=app_name,
            app_menu_name=app_menu_name,
            wagtail_django_admin_menu=wagtail_django_admin_menu,
        ):
            if (
                app_name in WAGTAIL_ADMIN_CUSTOM_MENU
                and isinstance(WAGTAIL_ADMIN_CUSTOM_MENU[app_name], dict)
                and "order" in WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
            ):
                order = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["order"]
            else:
                order = 10000

            if (
                app_name in WAGTAIL_ADMIN_CUSTOM_MENU
                and isinstance(WAGTAIL_ADMIN_CUSTOM_MENU[app_name], dict)
                and "icon_name" in WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
            ):
                icon_name = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["icon_name"]
            else:
                icon_name = "folder-inverse"

            return CustomSubmenuMenuItem(
                _(app_menu_name),
                wagtail_django_admin_menu,
                icon_name=icon_name,
                order=order,
            )

        for model in app["models"]:
            model_name = str(model["model_name"])
            object_name = str(model["object_name"])
            model_menu_name = str(model["name"])
            admin_url = model["admin_url"]
            if not hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU") or (
                hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
                and isinstance(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU, dict)
                and app_name in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU
                and (
                    isinstance(
                        django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name], list
                    )
                    and (
                        model_name
                        in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
                        or object_name
                        in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
                        or not django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
                    )
                    or isinstance(
                        django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name], dict
                    )
                    and "models" in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
                    and (
                        model_name
                        in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"]
                        or object_name
                        in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"]
                        or not django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name][
                            "models"
                        ]
                    )
                )
            ):

                @hooks.register("register_wagtail_django_admin_menu_item" + app_name)
                def register_users_menu_item(
                    model_name=model_name,
                    model_menu_name=model_menu_name,
                    admin_url=admin_url,
                    app_name=app_name,
                ):
                    try:
                        order = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"][
                            model_name
                        ]["order"]
                    except (KeyError, TypeError):
                        try:
                            order = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"][
                                object_name
                            ]["order"]
                        except (KeyError, TypeError):
                            order = 10000

                    try:
                        icon_name = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"][
                            model_name
                        ]["icon_name"]
                    except (KeyError, TypeError):
                        try:
                            icon_name = WAGTAIL_ADMIN_CUSTOM_MENU[app_name]["models"][
                                object_name
                            ]["icon_name"]
                        except (KeyError, TypeError):
                            icon_name = "folder-inverse"

                    item = CustomMenuItem(
                        _(model_menu_name),
                        admin_url,
                        icon_name=icon_name,
                        order=order,
                    )
                    return item
