import re
from inspect import getfullargspec

from django.template import Library
from django.conf import settings
from django.utils.translation import activate
from django.template.library import InclusionNode, parse_bits
from django.template.loader import render_to_string


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
    if settings.USE_I18N:
        m = re.match(r"(/[^/]*)(/.*$)", url)
        url_lang = m.groups()[0][1:]
        if url_lang in LANGUAGES:
            return f"/{lang_code}{m.groups()[1]}"
        else:
            return url
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

        return wagtail_sidebar_props(context)
    except Exception:
        return


@register.simple_tag(takes_context=True)
def old_wagtail_menu(context):
    try:
        return render_to_string("admin/old_wagtail_menu.html", context)
    except TypeError:
        return render_to_string("admin/old_wagtail_menu.html", context.__dict__)
