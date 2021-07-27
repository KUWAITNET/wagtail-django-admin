from django.db import models  # noqa
from django.utils.translation import gettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, FieldRowPanel
from wagtail.core.models import Page, Orderable

# Create your models here.


class SearchItem(Orderable):
    page = ParentalKey("HomePage", related_name="item")
    title = models.CharField(_("item text"), max_length=100, null=True)
    LIST_TYPE = (
        ("menu", _("menu")),
        ("category", _("category")),
        ("project_stage", _("project stage")),
    )
    list_type = models.CharField(_("List type"), max_length=50, choices=LIST_TYPE)
    panels = (
        FieldRowPanel(
            [
                FieldPanel("title", classname="col6"),
                FieldPanel("list_type", classname="col6"),
            ]
        ),
    )


class Banner(Orderable):
    page = ParentalKey("HomePage", related_name="banner")
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("image"),
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    heading = models.CharField(_("heading"), max_length=100, null=True)
    vedio_url = models.URLField(_("vedio URL"), max_length=200, null=True, blank=True)
    link_text = models.CharField(_("link text"), max_length=100, null=True, blank=True)
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("link page"),
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    link_url = models.URLField(
        _("link url"),
        max_length=200,
        null=True,
        blank=True,
        help_text=_("this will be used of you didn't select a page above"),
    )

    panels = [
        FieldPanel("heading"),
        FieldPanel("vedio_url"),
        FieldPanel("link_text"),
        FieldPanel("link_page"),
        FieldPanel("link_url"),
    ]

    @property
    def link(self):
        if self.link_page:
            return self.link_page.slug
        return self.link_url


class HomePage(Page):
    header_title = models.CharField(_("Header Title"), max_length=150)

    content_panels = Page.content_panels + [
        FieldPanel("header_title"),
        MultiFieldPanel(
            [InlinePanel("item", label=_("Item")),],
            heading=_("Search Items"),
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [InlinePanel("banner", label=_("Banner"))],
            heading=_("Banners"),
            classname="collapsible collapsed",
        ),
    ]