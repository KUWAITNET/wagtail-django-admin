from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu
from wagtail_django_admin.utils import get_app_list
from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu

from .utils import url_no_i18n


app_list = get_app_list(context={"request": None})


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


for app in app_list:
    app_name = str(app["app_label"])
    if (
        hasattr(settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
        and type(settings.WAGTAIL_ADMIN_CUSTOM_MENU) is dict
        and app_name in settings.WAGTAIL_ADMIN_CUSTOM_MENU.keys()
    ) or not hasattr(settings, "WAGTAIL_ADMIN_CUSTOM_MENU"):
        wagtail_django_admin_menu = Menu(
            register_hook_name="register_wagtail_django_admin_menu_item" + app_name,
            construct_hook_name="construct_main_menu",
        )

        @hooks.register("register_admin_menu_item")
        def register_wagtail_django_admin_menu(
            app_name=app_name, wagtail_django_admin_menu=wagtail_django_admin_menu
        ):

            return CustomSubmenuMenuItem(
                app_name,
                wagtail_django_admin_menu,
                icon_name="folder-inverse",
                order=10000,
            )

        for model in app["models"]:
            model_name = str(model["model_name"])
            admin_url = model["admin_url"]
            if (
                hasattr(settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
                and type(settings.WAGTAIL_ADMIN_CUSTOM_MENU) is dict
                and app_name in settings.WAGTAIL_ADMIN_CUSTOM_MENU.keys()
                and type(settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]) is list
                and model_name in settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
            ) or not hasattr(settings, "WAGTAIL_ADMIN_CUSTOM_MENU"):

                @hooks.register("register_wagtail_django_admin_menu_item" + app_name)
                def register_users_menu_item(
                    model_name=model_name, admin_url=admin_url
                ):
                    item = CustomMenuItem(
                        model_name, admin_url, icon_name="folder-inverse", order=10000
                    )
                    return item
