from django.templatetags.static import static
from django.utils.html import format_html

try:
    from wagtail.core import hooks
except ModuleNotFoundError:
    from wagtail import hooks


@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Add wagtail_django_admin/css/wagtail_custom.css to the admin."""
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_django_admin/css/wagtail_custom.css"),
    )
