from django.conf import settings
from django.utils.module_loading import import_string


# Improved usability
JET_CHANGE_FORM_SIBLING_LINKS = getattr(settings, "JET_CHANGE_FORM_SIBLING_LINKS", True)

TABULAR_PERMISSIONS_CONFIG = {
    "template": "tabular_permissions/admin/tabular_permissions.html",
    "exclude": {
        "override": False,
        "apps": [],
        "models": [],
        "function": "wagtail_django_admin.helpers.dummy_permissions_exclude",
    },
    "auto_implement": True,
    "use_for_concrete": True,
    "custom_permission_translation": "wagtail_django_admin.helpers.custom_permissions_translator",
    "apps_customization_func": "wagtail_django_admin.helpers.apps_customization_func",
}
user_conf = getattr(settings, "TABULAR_PERMISSIONS_CONFIG", False)

if user_conf:
    # we update the exclude dict first
    TABULAR_PERMISSIONS_CONFIG["exclude"].update(user_conf.get("exclude", {}))
    user_conf["exclude"] = TABULAR_PERMISSIONS_CONFIG["exclude"]
    # update the rest if the configuration
    TABULAR_PERMISSIONS_CONFIG.update(user_conf)

AUTO_IMPLEMENT = TABULAR_PERMISSIONS_CONFIG["auto_implement"]
TEMPLATE = TABULAR_PERMISSIONS_CONFIG["template"]

_base_exclude_apps = ["sessions", "contenttypes", "admin"]
user_exclude = TABULAR_PERMISSIONS_CONFIG["exclude"]
if not user_exclude.get("override", False):
    EXCLUDE_APPS = _base_exclude_apps + user_exclude.get("apps", [])
else:
    EXCLUDE_APPS = user_exclude.get("apps", [])
EXCLUDE_APPS = [x.lower() for x in EXCLUDE_APPS]

EXCLUDE_MODELS = user_exclude.get("models", [])
EXCLUDE_MODELS = [x.lower() for x in EXCLUDE_MODELS]

model_exclude_func = user_exclude.get("function")
EXCLUDE_FUNCTION = import_string(model_exclude_func)

USE_FOR_CONCRETE = TABULAR_PERMISSIONS_CONFIG["use_for_concrete"]
TRANSLATION_FUNC = import_string(
    TABULAR_PERMISSIONS_CONFIG["custom_permission_translation"]
)

APPS_CUSTOMIZATION_FUNC = import_string(
    TABULAR_PERMISSIONS_CONFIG["apps_customization_func"]
)

WAGTAIL_ADMIN_LANGUAGES = getattr(
    settings, "WAGTAIL_ADMIN_LANGUAGES", settings.LANGUAGES
)
