from django.contrib.auth import get_user_model

from .utils import get_app_list

# Create your models here.

User = get_user_model()


def all_allowed_url(instance, request=None):
    app_list = get_app_list(context={"request": request})
    all_allowed_url = []
    for app in app_list:
        if "has_module_perms" in app and app["has_module_perms"]:
            all_allowed_url.append(app["app_url"])

        for model in app["models"]:
            if (
                "admin_url" in model
                and "perms" in model
                and "add" in model["perms"]
                and model["perms"]["add"]
            ):
                all_allowed_url.append(model["add_url"])
            if (
                model["perms"]["add"]
                or model["perms"]["change"]
                or model["perms"]["delete"]
                or model["perms"]["view"]
            ):
                if "admin_url" in model:
                    all_allowed_url.append(model["admin_url"])
    return all_allowed_url


User.all_allowed_url = all_allowed_url
