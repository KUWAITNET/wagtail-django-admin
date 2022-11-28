import re
from inspect import getfullargspec

from django.template import Library
from django.conf import settings
from django.utils.translation import activate
from django.template.library import InclusionNode, parse_bits
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import json_script


register = Library()


class CustomInclusionAdminNode(InclusionNode):
    """
    Template tag that allows its template to be overridden per model, per app,
    or globally.
    """

    def __init__(self, parser, token, func, template_name, takes_context=True):
        self.template_name = template_name
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(
            func
        )
        bits = token.split_contents()
        args, kwargs = parse_bits(
            parser,
            bits[1:],
            params,
            varargs,
            varkw,
            defaults,
            kwonly,
            kwonly_defaults,
            takes_context,
            bits[0],
        )
        super().__init__(func, takes_context, args, kwargs, filename=None)

    def render(self, context):
        # opts = context["opts"]
        # app_label = opts.app_label.lower()
        # object_name = opts.object_name.lower()
        # Load template for this render call. (Setting self.filename isn't
        # thread-safe.)
        context.render_context[self] = context.template.engine.select_template(
            [
                self.template_name,
            ]
        )
        return super().render(context)


def admin_actions(context):
    """
    Track the number of times the action field has been rendered on the page,
    so we know which value to use.
    """
    context["action_index"] = context.get("action_index", -1) + 1
    return context


@register.tag(name="wagtail_admin_actions")
def admin_actions_tag(parser, token):
    return CustomInclusionAdminNode(
        parser,
        token,
        func=admin_actions,
        template_name="modeladmin/wagtail_actions.html",
    )


@register.filter
def correct_i18n(url, lang_code):
    LANGUAGES = [lang[0] for lang in settings.LANGUAGES]
    activate(lang_code)
    if settings.FORCE_SCRIPT_NAME:
        url = url[len(settings.FORCE_SCRIPT_NAME) :]

    if settings.USE_I18N:
        m = re.match(r"(/[^/]*)(/.*$)", url)
        url_lang = m.groups()[0][1:]
        if url_lang in LANGUAGES:
            new_url = f"/{lang_code}{m.groups()[1]}"
        else:
            new_url = url

        if settings.FORCE_SCRIPT_NAME:
            new_url = f"{settings.FORCE_SCRIPT_NAME}{new_url}"
        return new_url
    else:
        return url


@register.simple_tag()
def slim_sidebar_enabled():
    from wagtail import VERSION

    if VERSION[0] >= 3:
        return True
    else:
        try:
            from wagtail.admin.templatetags.wagtailadmin_tags import (
                slim_sidebar_enabled as wagtail_slim_sidebar_enabled,
            )

            return wagtail_slim_sidebar_enabled()
        except Exception:
            return


@register.simple_tag(takes_context=True)
def sidebar_props(context):
    try:
        from wagtail.admin.templatetags.wagtailadmin_tags import (
            sidebar_props as wagtail_sidebar_props,
        )

        res = wagtail_sidebar_props(context)
        return res
    except Exception:
        return


@register.simple_tag(takes_context=True)
def sidebar_props_respect_lang(context):
    from wagtail.admin.ui import sidebar  # noqa
    from wagtail.admin.search import admin_search_areas  # noqa
    from wagtail.admin.menu import admin_menu  # noqa
    from wagtail.telepath import JSContext  # noqa
    from wagtail import hooks
    
    request = context["request"]
    search_areas = admin_search_areas.search_items_for_request(request)
    if search_areas:
        search_area = search_areas[0]
    else:
        search_area = None

    account_menu = [
        sidebar.LinkMenuItem(
            "account", _("Account"), reverse("wagtailadmin_account"), icon_name="user"
        ),
        sidebar.LinkMenuItem(
            "logout", _("Log out"), reverse("wagtailadmin_logout"), icon_name="logout"
        ),
    ]

    current_lang = request.LANGUAGE_CODE

    def _registered_menu_items(self):
        activate(current_lang)
        self._registered_menu_items = [
            fn() for fn in hooks.get_hooks(self.register_hook_name)
        ]
        return self._registered_menu_items
        
    admin_menu.registered_menu_items_set = _registered_menu_items(admin_menu)

    modules = [
        sidebar.WagtailBrandingModule(),
        sidebar.SearchModule(search_area) if search_area else None,
        sidebar.MainMenuModule(
            admin_menu.render_component(request), account_menu, request.user
        ),
    ]

    def correct_menu_items(module):
        if hasattr(module, "menu_items") and isinstance(module.menu_items, list):
            for menu_item in module.menu_items:
                if hasattr(menu_item, "menu_items") and isinstance(
                    menu_item.menu_items, list
                ):
                    correct_menu_items(menu_item)
                elif hasattr(menu_item, "url") and menu_item.url:
                    url = menu_item.url
                    if isinstance(menu_item.url, list):
                        url = "/".join(menu_item.url)
                    menu_item.url = correct_i18n(url, current_lang)
                    label = _(menu_item.label)
                    menu_item.label = str(label)
        elif hasattr(module, "url") and module.url:
            url = module.url
            if isinstance(module.url, list):
                url = "/".join(module.url)
            module.url = correct_i18n(url, current_lang)
            label = _(menu_item.label)
            menu_item.label = str(label)

    renderd_modules = []
    activate(current_lang)
    for module in modules:
        if module is not None:
            correct_menu_items(module)
            renderd_modules.append(module)

    return json_script(
        {
            "modules": JSContext().pack(renderd_modules),
        },
        element_id="wagtail-sidebar-props",
    )


@register.simple_tag(takes_context=True)
def old_wagtail_menu(context):
    try:
        return render_to_string("admin/old_wagtail_menu.html", context)
    except TypeError:
        return render_to_string("admin/old_wagtail_menu.html", context.__dict__)
