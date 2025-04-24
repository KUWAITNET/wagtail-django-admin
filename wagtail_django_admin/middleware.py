from django.utils.translation import activate, get_language
from django.conf import settings
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from wagtail.users.models import UserProfile


class WagtailDjangoAdminLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to handle language switching in the wagtail-django-admin interface.
    This middleware ensures that the correct language is activated for the admin interface.
    """
    
    def process_request(self, request):
        # Get the current language from the request
        current_language = get_language()
        
        # Get the URL resolver for the request path
        resolver_match = resolve(request.path)
        request.resolver_match = resolver_match
        view_name = resolver_match.view_name
        
        # Check if we're in the wagtail admin area

        if view_name in ["wagtailadmin_home", "wagtail_django_admin",] or view_name.startswith("admin:") or "_modeladmin_" in view_name or view_name.startswith("wagtailadmin"):
            # Get the language from the URL if present
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and path_parts[1] in [lang[0] for lang in settings.LANGUAGES]:
                # If language is in URL, activate it
                lang = path_parts[1]
                activate(lang)
                # Update user profile if user is authenticated
                if request.user.is_authenticated:
                    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
                    user_profile.preferred_language = lang
                    user_profile.save()
            else:
                # If no language in URL, use the default language
                activate(settings.LANGUAGE_CODE)
        
        return None
