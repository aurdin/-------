from django.db import models
from django.utils.translation import gettext_lazy as _

from .services.codes import generate_code


# Справочник категорий
class Category(models.Model):
    cat_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    cat_name = models.CharField(
        max_length=255,
    )

    cat_description = models.TextField(
        null=True,
        blank=True,
    )

    cat_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "catalog_category"
        ordering = ("cat_name",)
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def save(self, *args, **kwargs):
        if not self.cat_code:
            self.cat_code = generate_code(Category, "cat_code", "cat")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.cat_name


# Справочник групп
class Group(models.Model):
    grp_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    grp_name = models.CharField(
        max_length=255,
    )

    grp_description = models.TextField(
        null=True,
        blank=True,
    )

    grp_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "catalog_group"
        ordering = ("grp_name",)
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    def save(self, *args, **kwargs):
        if not self.grp_code:
            self.grp_code = generate_code(Group, "grp_code", "grp")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.grp_name
