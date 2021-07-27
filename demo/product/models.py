from django.db import models
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    name = models.CharField(_("Name"), max_length=50)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Product(models.Model):
    category = models.ForeignKey("product.Category", verbose_name=_(""), on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=50)
    description = models.TextField(_("Description"))
