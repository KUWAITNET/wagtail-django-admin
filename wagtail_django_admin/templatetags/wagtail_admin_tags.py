import re
from inspect import getfullargspec

from django.template import Library
from django.conf import settings
from django.utils.translation import activate
from django.template.library import InclusionNode, parse_bits


register = Library()


class CustomInclusionAdminNode(InclusionNode):
    """
    Template tag that allows its template to be overridden per model, per app,
    or globally.
    """

    def __init__(self, parser, token, func, template_name, takes_context=True):
        self.template_name = template_name
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        bits = token.split_contents()
        args, kwargs = parse_bits(
            parser, bits[1:], params, varargs, varkw, defaults, kwonly,
            kwonly_defaults, takes_context, bits[0],
        )
        super().__init__(func, takes_context, args, kwargs, filename=None)

    def render(self, context):
        opts = context['opts']
        # app_label = opts.app_label.lower()
        # object_name = opts.object_name.lower()
        # Load template for this render call. (Setting self.filename isn't
        # thread-safe.)
        context.render_context[self] = context.template.engine.select_template([
            self.template_name,
        ])
        return super().render(context)


def admin_actions(context):
    """
    Track the number of times the action field has been rendered on the page,
    so we know which value to use.
    """
    context['action_index'] = context.get('action_index', -1) + 1
    return context

@register.tag(name='wagtail_admin_actions')
def admin_actions_tag(parser, token):
    return CustomInclusionAdminNode(parser, token, func=admin_actions, template_name='modeladmin/wagtail_actions.html')


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
