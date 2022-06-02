import re
from datetime import datetime
import calendar

from django.db import models
from django.contrib import admin, messages
from django.urls import resolve, NoReverseMatch, reverse
from django.utils.text import capfirst
from django.apps.registry import apps
from django.utils.encoding import smart_str
from django.conf import settings
from django.forms import forms
from django.utils.translation import gettext_lazy as _, ngettext, activate, get_language
from django.http.response import (
    HttpResponseBase,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.safestring import mark_safe

from django.contrib.admin.views.main import ERROR_FLAG
from django.template.response import SimpleTemplateResponse

from wagtail.contrib.modeladmin.views import IndexView
from wagtail.search.backends import get_search_backend


LANGUAGES = [lang[0] for lang in settings.LANGUAGES]


def url_no_i18n(url, *args, **kwargs):
    if settings.USE_I18N:
        m = re.match(r"(/[^/]*)(/.*$)", url)
        url_lang = m.groups()[0][1:]
        if url_lang in LANGUAGES:
            return m.groups()[1]
        else:
            return url
    else:
        return url


def get_app_list(context, order=True):
    admin_site = get_admin_site(context)
    request = context["request"]
    activate("en")
    app_dict = {}
    for model, model_admin in admin_site._registry.items():
        app_label = model._meta.app_label
        try:
            has_module_perms = model_admin.has_module_permission(request)
        except AttributeError:
            has_module_perms = True if not request else False

        if has_module_perms:
            if request:
                perms = model_admin.get_model_perms(request)
            else:
                perms = {
                    "add": True,
                    "change": True,
                    "delete": True,
                    "view": True,
                }

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                info = (app_label, model._meta.model_name)
                model_dict = {
                    "name": capfirst(model._meta.verbose_name_plural),
                    "object_name": model._meta.object_name,
                    "perms": perms,
                    "model_name": model._meta.model_name,
                }
                if perms.get("change", False) or perms.get("add", False):
                    try:
                        model_dict["admin_url"] = reverse(
                            "admin:%s_%s_changelist" % info, current_app=admin_site.name
                        )
                    except NoReverseMatch:
                        pass
                if perms.get("add", False):
                    try:
                        model_dict["add_url"] = reverse(
                            "admin:%s_%s_add" % info, current_app=admin_site.name
                        )
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]["models"].append(model_dict)
                else:
                    try:
                        name = apps.get_app_config(app_label).verbose_name
                    except NameError:
                        name = app_label.title()
                    app_dict[app_label] = {
                        "name": name,
                        "app_label": app_label,
                        "app_url": reverse(
                            "admin:app_list",
                            kwargs={"app_label": app_label},
                            current_app=admin_site.name,
                        ),
                        "has_module_perms": has_module_perms,
                        "models": [model_dict],
                    }

    # Sort the apps alphabetically.
    app_list = list(app_dict.values())

    if order:
        app_list.sort(key=lambda x: x["name"].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app["models"].sort(key=lambda x: x["name"])

    return app_list


def get_admin_site(context):
    try:
        current_resolver = resolve(context.get("request").path)
        index_resolver = resolve(reverse("%s:index" % current_resolver.namespaces[0]))

        if hasattr(index_resolver.func, "admin_site"):
            return index_resolver.func.admin_site

        for func_closure in index_resolver.func.__closure__:
            if isinstance(func_closure.cell_contents, admin.AdminSite):
                return func_closure.cell_contents
    except:
        pass

    return admin.site


def get_model_instance_label(instance):
    if getattr(instance, "related_label", None):
        return instance.related_label()
    return smart_str(instance)


def get_admin_site(context):
    try:
        current_resolver = resolve(context.get("request").path)
        index_resolver = resolve(reverse("%s:index" % current_resolver.namespaces[0]))

        if hasattr(index_resolver.func, "admin_site"):
            return index_resolver.func.admin_site

        for func_closure in index_resolver.func.__closure__:
            if isinstance(func_closure.cell_contents, admin.AdminSite):
                return func_closure.cell_contents
    except:
        pass

    return admin.site


def get_admin_site_name(context):
    return get_admin_site(context).name


def get_possible_language_codes():
    language_code = get_language()

    language_code = language_code.replace("_", "-").lower()
    language_codes = []

    # making dialect part uppercase
    split = language_code.split("-", 2)
    if len(split) == 2:
        language_code = (
            "%s-%s" % (split[0].lower(), split[1].upper())
            if split[0] != split[1]
            else split[0]
        )

    language_codes.append(language_code)

    # adding language code without dialect part
    if len(split) == 2:
        language_codes.append(split[0].lower())

    return language_codes


def get_model_queryset(admin_site, model, request, preserved_filters=None):
    model_admin = admin_site._registry.get(model)

    if model_admin is None:
        return

    try:
        changelist_url = reverse(
            "%s:%s_%s_changelist"
            % (admin_site.name, model._meta.app_label, model._meta.model_name)
        )
    except NoReverseMatch:
        return

    changelist_filters = None

    if preserved_filters:
        changelist_filters = preserved_filters.get("_changelist_filters")

    if changelist_filters:
        changelist_url += "?" + changelist_filters

    if model_admin:
        queryset = model_admin.get_queryset(request)
    else:
        queryset = model.objects

    list_display = model_admin.get_list_display(request)
    list_display_links = model_admin.get_list_display_links(request, list_display)
    list_filter = model_admin.get_list_filter(request)
    search_fields = (
        model_admin.get_search_fields(request)
        if hasattr(model_admin, "get_search_fields")
        else model_admin.search_fields
    )
    list_select_related = (
        model_admin.get_list_select_related(request)
        if hasattr(model_admin, "get_list_select_related")
        else model_admin.list_select_related
    )

    actions = model_admin.get_actions(request)
    if actions:
        list_display = ["action_checkbox"] + list(list_display)

    ChangeList = model_admin.get_changelist(request)

    change_list_args = [
        request,
        model,
        list_display,
        list_display_links,
        list_filter,
        model_admin.date_hierarchy,
        search_fields,
        list_select_related,
        model_admin.list_per_page,
        model_admin.list_max_show_all,
        model_admin.list_editable,
        model_admin,
    ]

    try:
        sortable_by = model_admin.get_sortable_by(request)
        change_list_args.append(sortable_by)
    except AttributeError:
        # django version < 2.1
        pass

    try:
        cl = ChangeList(*change_list_args)
        queryset = cl.get_queryset(request)
    except admin.options.IncorrectLookupParameters:
        pass

    return queryset


class DateFilterIndexViewMixin(IndexView):
    """
    This View is ordered to create links to years for the years.
    """

    field_name = "created"

    def get_template_names(self):
        return "modeladmin/admin/index_date_filter.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["field"] = self.field_name

        year = self.request.GET.get(f"{self.field_name}__year", None)
        if not year:
            year = self.request.GET.get(self.field_name, None)
        month = self.request.GET.get(f"{self.field_name}__month", None)
        month = int(month) if month else month
        day = self.request.GET.get(f"{self.field_name}__day", None)

        if month:
            data["month_select"] = calendar.month_name[month]

        search_backend = get_search_backend()

        if isinstance(self.get_queryset(), type(search_backend)):
            results = self.get_queryset().results()

            # if provided field is not a date
            if results and not isinstance(
                getattr(results[0], self.field_name), datetime
            ):
                return data

            if month:
                data["days"] = list(
                    set([getattr(result, self.field_name).day for result in results])
                )
            elif year:
                data["months"] = list(
                    set(
                        [
                            (
                                getattr(result, self.field_name).month,
                                getattr(result, self.field_name).strftime("%B"),
                            )
                            for result in results
                        ]
                    )
                )
            else:
                data["years"] = list(
                    set([getattr(result, self.field_name).year for result in results])
                )

        else:

            # if provided field is not a date
            if self.field_name == "year":
                data["years"] = list(
                    set(self.get_queryset().values_list("year", flat=True))
                )
            else:
                try:
                    self.get_queryset().dates(self.field_name, "year")
                except AssertionError:
                    return data

                if month:
                    keywords_args = {
                        f"{self.field_name}__year": year,
                        f"{self.field_name}__month": month,
                    }
                    data["days"] = [
                        date.day
                        for date in self.get_queryset()
                        .filter(**keywords_args)
                        .dates(self.field_name, "day")
                    ]
                elif year:
                    keywords_args = {
                        f"{self.field_name}__year": year,
                    }
                    data["months"] = [
                        (date.month, date.strftime("%B"))
                        for date in self.get_queryset()
                        .filter(**keywords_args)
                        .dates(self.field_name, "month")
                    ]
                else:
                    data["years"] = [
                        date.year
                        for date in self.get_queryset().dates(self.field_name, "year")
                    ]

        [  # sorting all the things in descending order
            data[field].sort(key=lambda x: -x)
            if not data[field] or not isinstance(data[field][0], tuple)
            else data[field].sort(key=lambda x: -x[0])
            for field in data
            if field in ["days", "months", "years"]
        ]
        data["current_year"] = year
        data["current_month"] = month
        data["current_day"] = day

        opts = self.model._meta
        data["opts"] = opts
        return data


class ActionDateFilterAdminMixin:
    index_view_class = DateFilterIndexViewMixin

    actions = []
    action_form = admin.helpers.ActionForm
    actions_selection_counter = True
    delete_selected_confirmation_template = (
        "modeladmin/delete_selected_confirmation.html"
    )
    media = None

    # the methods below is copied from django/contrib/admin/options.py
    def action_checkbox(self, obj):
        """
        A list_display column containing a checkbox widget.
        """
        return admin.helpers.checkbox.render(
            admin.helpers.ACTION_CHECKBOX_NAME, str(obj.pk)
        )

    action_checkbox.short_description = mark_safe(
        '<input type="checkbox" id="action-toggle">'
    )

    def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        """
        Return a list of choices for use in a form object.  Each choice is a
        tuple (name, description).
        """
        choices = [] + default_choices
        for func, name, description in self.get_actions(request).values():
            choice = (name, description % admin.utils.model_format_dict(self.opts))
            choices.append(choice)
        return choices

    def get_action(self, action):
        """
        Return a given action from a parameter, which can either be a callable,
        or the name of a method on the ModelAdmin.  Return is a tuple of
        (callable, name, description).
        """
        # If the action is a callable, just use it.
        if callable(action):
            func = action
            action = action.__name__

        # Next, look for a method. Grab it off self.__class__ to get an unbound
        # method instead of a bound one; this ensures that the calling
        # conventions are the same for functions and methods.
        elif hasattr(self.__class__, action):
            func = getattr(self.__class__, action)

        # Finally, look for a named method on the admin site
        else:
            try:
                func = self.admin_site.get_action(action)
            except KeyError:
                return None

        if hasattr(func, "short_description"):
            description = func.short_description
        else:
            description = capfirst(action.replace("_", " "))
        return func, action, description

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method must be
        called before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import DELETION, LogEntry

        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=admin.options.get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=DELETION,
        )

    def delete_queryset(self, request, queryset):
        """Given a queryset, delete it from the database."""
        queryset.delete()

    def message_user(
        self, request, message, level=messages.INFO, extra_tags="", fail_silently=False
    ):
        """
        Send a message to the user. The default implementation
        posts a message using the django.contrib.messages backend.

        Exposes almost the same API as messages.add_message(), but accepts the
        positional arguments in a different order to maintain backwards
        compatibility. For convenience, it accepts the `level` argument as
        a string rather than the usual level number.
        """
        if not isinstance(level, int):
            # attempt to get the level if passed a string
            try:
                level = getattr(messages.constants, level.upper())
            except AttributeError:
                levels = messages.constants.DEFAULT_TAGS.values()
                levels_repr = ", ".join("`%s`" % level for level in levels)
                raise ValueError(
                    "Bad message level string: `%s`. Possible values are: %s"
                    % (level, levels_repr)
                )

        messages.add_message(
            request, level, message, extra_tags=extra_tags, fail_silently=fail_silently
        )

    def _get_base_actions(self):
        """Return the list of actions, prior to any request-based filtering."""
        actions = []
        base_actions = (self.get_action(action) for action in self.actions or [])
        # get_action might have returned None, so filter any of those out.
        base_actions = [action for action in base_actions if action]
        base_action_names = {name for _, name, _ in base_actions}

        # Gather actions from the admin site first
        for (name, func) in self.admin_site.actions:
            if name in base_action_names:
                continue
            description = getattr(func, "short_description", name.replace("_", " "))
            actions.append((func, name, description))
        # Add actions from this ModelAdmin.
        actions.extend(base_actions)
        return actions

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        if (
            self.list_display
            and "action_checkbox" not in self.list_display
            and "/change_order/" not in request.path
        ):
            self.list_display = ["action_checkbox", *self.list_display]
        elif (
            self.list_display
            and "action_checkbox" in self.list_display
            and "/change_order/" in request.path
        ):
            self.list_display.remove("action_checkbox")

        return self.list_display

    def get_actions(self, request):
        """
        Return a dictionary mapping the names of all actions for this
        ModelAdmin to a tuple of (callable, name, description) for each action.
        """
        # If self.actions is set to None that means actions are disabled on
        # this page.
        if self.actions is None or "_popup" in request.GET:

            return {}

        # actions = self._filter_actions_by_permissions(request, self._get_base_actions())
        actions = self._get_base_actions()
        return {name: (func, name, desc) for func, name, desc in actions}

    def get_deleted_objects(self, objs, request):
        """
        Hook for customizing the delete process for the delete view and the
        "delete selected" action.
        """
        return admin.utils.get_deleted_objects(objs, request, self.admin_site)

    def response_action(self, request, queryset):
        """
        Handle an admin action. This is called if a request is POSTed to the
        changelist; it returns an HttpResponse if the action was handled, and
        None otherwise.
        """

        # There can be multiple action forms on the page (at the top
        # and bottom of the change list, for example). Get the action
        # whose button was pushed.
        try:
            action_index = int(request.POST.get("index", 0))
        except ValueError:
            action_index = 0

        # Construct the action form.
        data = request.POST.copy()
        data.pop(admin.helpers.ACTION_CHECKBOX_NAME, None)
        data.pop("index", None)

        # Use the action whose button was pushed
        try:
            data.update({"action": data.getlist("action")[action_index]})
        except IndexError:
            # If we didn't get an action from the chosen form that's invalid
            # POST data, so by deleting action it'll fail the validation check
            # below. So no need to do anything here
            pass

        action_form = self.action_form(data, auto_id=None)
        action_form.fields["action"].choices = self.get_action_choices(request)

        # If the form's valid we can handle the action.
        if action_form.is_valid():
            action = action_form.cleaned_data["action"]
            select_across = action_form.cleaned_data["select_across"]
            func = self.get_actions(request)[action][0]

            # Get the list of selected PKs. If nothing's selected, we can't
            # perform an action on it, so bail. Except we want to perform
            # the action explicitly on all objects.
            selected = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)

            if not selected and not select_across:
                # Reminder that something needs to be selected or nothing will happen
                msg = _(
                    "Items must be selected in order to perform "
                    "actions on them. No items have been changed."
                )
                messages.warning(request, msg)
                return None

            if not select_across:
                # Perform the action only on the selected objects
                queryset = queryset.filter(pk__in=selected)

            response = func(self, request, queryset)

            # Actions may return an HttpResponse-like object, which will be
            # used as the response from the POST. If not, we'll be a good
            # little HTTP citizen and redirect back to the changelist page.

            if isinstance(response, HttpResponseBase):
                return response
            else:

                return HttpResponseRedirect(request.get_full_path())
        else:
            msg = _("No action selected.")
            messages.success(request, msg)
            # self.message_user(request, msg, messages.WARNING)
            return None

    # changelist_view in options.py
    def index_view(self, request):
        response = super().index_view(request)
        opts = self.model._meta
        app_label = opts.app_label

        # if not self.has_view_or_change_permission(request):
        #     raise PermissionDenied

        try:
            cl = self
        except admin.options.IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET:
                # needs to be reviwed
                return SimpleTemplateResponse(
                    "admin/invalid_setup.html", {"title": _("Database error")}
                )
            return HttpResponseRedirect(request.path + "?" + ERROR_FLAG + "=1")

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.

        action_failed = False
        selected = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
        actions = self.get_actions(request)

        # Actions with no confirmation
        if (
            actions
            and request.method == "POST"
            and "index" in request.POST
            and "_save" not in request.POST
        ):
            if selected:
                response = self.response_action(
                    request, queryset=cl.get_queryset(request)
                )
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _(
                    "Items must be selected in order to perform "
                    "actions on them. No items have been changed."
                )
                messages.success(request, msg)
                action_failed = True
        # Actions with confirmation
        if (
            actions
            and request.method == "POST"
            and admin.helpers.ACTION_CHECKBOX_NAME in request.POST
            and "index" not in request.POST
            and "_save" not in request.POST
        ):
            if selected:
                response = self.response_action(
                    request, queryset=cl.get_queryset(request)
                )
                if response:
                    return response

                else:
                    action_failed = True

        if action_failed:
            # Redirect back to the changelist page to avoid resubmitting the
            # form if the user refreshes the browser or uses the "No, take
            # me back" button on the action confirmation page.
            return HttpResponseRedirect(request.get_full_path())
        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        # formset = cl.formset = None

        # needs to be reviewed
        if isinstance(response, HttpResponseNotAllowed):
            # print("HttpResponseNotAllowed")
            response.context_data = {}

        extra = "" if settings.DEBUG else ".min"
        response.context_data["media"] = forms.Media(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "admin/js/core.js",
                "admin/js/admin/RelatedObjectLookups.js",
                "admin/js/actions%s.js" % extra,
                "admin/js/urlify.js",
                "admin/js/prepopulate%s.js" % extra,
                "admin/js/vendor/xregexp/xregexp%s.js" % extra,
            ]
        )
        self.media = response.context_data["media"]
        # response.context_data["media"] = forms.Media(js=['admin/js/%s' % url for url in js])

        # Build the action form and populate it with available actions.
        if actions:

            action_form = self.action_form(auto_id=None)
            action_form.fields["action"].choices = self.get_action_choices(request)

            response.context_data["media"] = (
                response.context_data["media"] + action_form.media
            )
            # media += action_form.media
        else:
            action_form = None

        # calculate result_count and result_list

        self.page_num = int(request.GET.get("p", 0))

        paginator = Paginator(self.get_queryset(request), self.list_per_page)
        result_count = paginator.count

        try:
            result_list = paginator.page((self.page_num + 1)).object_list
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            result_list = paginator.page(1).object_list
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            result_list = paginator.page(self.page_num + 1).object_list

        # cl = {"result_count": result_count, "result_list": result_list}

        cl = {"result_count": result_count, "result_list": result_list}

        selection_note_all = ngettext(
            "%(total_count)s selected",
            "All %(total_count)s selected",
            cl["result_count"],
        )

        response.context_data["module_name"] = str(opts.verbose_name_plural)
        response.context_data["selection_note"] = _(
            "0 of %(cnt)s selected" % {"cnt": len(cl["result_list"])},
        )
        response.context_data["selection_note_all"] = _(
            selection_note_all % {"total_count": cl["result_count"]},
        )
        response.context_data["cl"] = cl
        response.context_data["opts"] = opts
        response.context_data["action_form"] = action_form
        response.context_data[
            "actions_selection_counter"
        ] = self.actions_selection_counter

        return response
