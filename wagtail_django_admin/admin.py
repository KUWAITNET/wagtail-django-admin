from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, Group, GroupAdmin
from django.contrib.auth import get_user_model


from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu
from wagtail_django_admin.utils import get_app_list
from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu

from .utils import url_no_i18n
from .widgets import TabularPermissionsWidget
from . import settings



User = get_user_model()


class UserTabularPermissionsMixin:
    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super(UserTabularPermissionsMixin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'user_permissions':
            field.widget = TabularPermissionsWidget(db_field.verbose_name, db_field.name in self.filter_vertical)
            field.help_text = ''
        return field


class GroupTabularPermissionsMixin:
    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super(GroupTabularPermissionsMixin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'permissions':
            field.widget = TabularPermissionsWidget(db_field.verbose_name, db_field.name in self.filter_vertical,
                                                    'permissions')
            field.help_text = ''
        return field



class TabularPermissionsUserAdmin(admin.site._registry[User].__class__):
    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super(TabularPermissionsUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'user_permissions':
            field.widget = TabularPermissionsWidget(db_field.verbose_name, db_field.name in self.filter_vertical)
            field.help_text = ''
        return field


class TabularPermissionsGroupAdmin(GroupTabularPermissionsMixin, GroupAdmin):
    pass


# if settings.AUTO_IMPLEMENT:
#     try:
# UserAdmin = admin.site._registry[User].__class__
admin.site.unregister(User)
admin.site.register(User, TabularPermissionsUserAdmin)
UserAdmin = admin.site._registry[User].__class__
admin.site.unregister(Group)
admin.site.register(Group, TabularPermissionsGroupAdmin)

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
    WAGTAIL_ADMIN_CUSTOM_MENU = getattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU", {})
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
                hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
                and type(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU) is dict
                and app_name in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU.keys()
                and type(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]) is list
                and model_name in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
            ) or not hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU") or (
                hasattr(django_settings, "WAGTAIL_ADMIN_CUSTOM_MENU")
                and type(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU) is dict
                and app_name in django_settings.WAGTAIL_ADMIN_CUSTOM_MENU.keys()
                and type(django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]) is list
                and not django_settings.WAGTAIL_ADMIN_CUSTOM_MENU[app_name]
            ):

                @hooks.register("register_wagtail_django_admin_menu_item" + app_name)
                def register_users_menu_item(
                    model_name=model_name, admin_url=admin_url
                ):
                    item = CustomMenuItem(
                        model_name, admin_url, icon_name="folder-inverse", order=10000
                    )
                    return item
