from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Trim, Upper
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Цены товаров в базе данных. Каждая запись содержит артикул товара, цену, статус, даты действия и информацию о создании и обновлении записи.
class Prices(models.Model):
    article = models.CharField(max_length=255, verbose_name=_("Article")) # Артикул товара
    article_key = models.GeneratedField(
        expression=Upper(Trim("article")),
        output_field=models.CharField(max_length=255),
        db_persist=True,
        verbose_name=_("Normalized article"),
    ) # Артикул товара в верхнем регистре без пробелов
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Base price (UAH)")) # Цена товара
    status = models.BooleanField(default=True, verbose_name=_("Status")) # Статус записи
    valid_from = models.DateField(default=timezone.localdate, verbose_name=_("Valid from")) # Дата начала действия
    valid_to = models.DateField(null=True, blank=True, verbose_name=_("Valid to")) # Дата окончания действия
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at")) # Дата создания
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at")) # Дата обновления
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_base_prices",
        verbose_name=_("Created by"),
    ) # Автор создания записи
    updated_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_base_prices",
        verbose_name=_("Updated by"),
    ) # Автор обновления записи

    class Meta:
        db_table = "prices_prices"
        db_table_comment = "Цены товаров"
        verbose_name = _("Base price")
        verbose_name_plural = _("Base prices")
        ordering = ("-valid_from", "-created_at", "-pk")
        indexes = [  # noqa: RUF012
            models.Index(
                fields=("article_key", "status", "valid_from", "valid_to"),
                name="idx_prices_article_date",
            ),
        ]
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="ck_prices_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(valid_to__isnull=True)
                    | models.Q(valid_to__gte=models.F("valid_from"))
                ),
                name="ck_prices_valid_period",
            ),
        ]

    def clean(self):
        super().clean()
        if self.article:
            self.article = self.article.strip()
        if not self.article:
            raise ValidationError({"article": "Артикул обязателен."})
        if self.amount is not None and self.amount.as_tuple().exponent < -2:
            raise ValidationError(
                {"amount": "Цена должна содержать не более двух знаков после запятой."}
            )

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self)._base_manager.filter(pk=self.pk).values(
                "article", "amount", "valid_from", "valid_to"
            ).first()
            if original:
                immutable_fields = ("article", "amount", "valid_from", "valid_to")
                if any(original[field] != getattr(self, field) for field in immutable_fields):
                    raise ValidationError(
                        "Артикул, цена и даты действия существующей записи неизменяемы."
                    )
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.article} — {self.amount} UAH"






class Promotion(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        verbose_name=_("Discount percent"),
    )
    status = models.BooleanField(default=True, verbose_name=_("Status"))
    allow_other_discounts = models.BooleanField(
        default=True,
        verbose_name=_("Other discounts apply"),
    )
    valid_from = models.DateField(default=timezone.localdate, verbose_name=_("Valid from"))
    valid_to = models.DateField(null=True, blank=True, verbose_name=_("Valid to"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_promotions",
        verbose_name=_("Created by"),
    )
    updated_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_promotions",
        verbose_name=_("Updated by"),
    )

    class Meta:
        db_table = "prices_promotion"
        db_table_comment = "Акции"
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ("-valid_from", "-created_at", "-pk")
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=(
                    models.Q(valid_to__isnull=True)
                    | models.Q(valid_to__gte=models.F("valid_from"))
                ),
                name="ck_promo_valid_period",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(discount_percent__isnull=True)
                    | models.Q(discount_percent__gt=0, discount_percent__lte=100)
                ),
                name="ck_promo_discount_percent",
            ),
        ]

    def clean(self):
        super().clean()
        if self.discount_percent is None:
            raise ValidationError({"discount_percent": _("Discount percent is required.")})
        if self.discount_percent <= 0 or self.discount_percent > 100:
            raise ValidationError({"discount_percent": _("Discount must be greater than 0 and no more than 100 percent.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def is_active_on(self, on_date=None):
        on_date = on_date or timezone.localdate()
        return (
            self.status
            and (self.valid_from is None or self.valid_from <= on_date)
            and (self.valid_to is None or self.valid_to >= on_date)
        )

    def blocks_other_discounts(self, on_date=None):
        return self.is_active_on(on_date) and not self.allow_other_discounts

    def __str__(self):
        return self.name


class PromotionTarget(models.Model):
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name="targets",
        verbose_name=_("Promotion"),
    )
    article = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Article"),
    )
    article_key = models.GeneratedField(
        expression=Upper(Trim("article")),
        output_field=models.CharField(max_length=255, null=True),
        db_persist=True,
        null=True,
        verbose_name=_("Normalized article"),
    )
    category = models.ForeignKey(
        "common.Category",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotion_targets",
        verbose_name=_("Category"),
    )
    group = models.ForeignKey(
        "common.Group",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotion_targets",
        verbose_name=_("Group"),
    )
    type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotion_targets",
        verbose_name=_("Type"),
    )
    color = models.ForeignKey(
        "common.Color",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotion_targets",
        verbose_name=_("Color"),
    )

    class Meta:
        db_table = "prices_promotion_target"
        db_table_comment = "Целевые объекты акций"
        verbose_name = _("Promotion target")
        verbose_name_plural = _("Promotion targets")
        ordering = ("promotion", "pk")
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=(
                    models.Q(
                        article__isnull=False,
                        category__isnull=True,
                        group__isnull=True,
                        type__isnull=True,
                        color__isnull=True,
                    )
                    | models.Q(
                        article__isnull=True,
                        category__isnull=False,
                        group__isnull=True,
                        type__isnull=True,
                        color__isnull=True,
                    )
                    | models.Q(
                        article__isnull=True,
                        category__isnull=True,
                        group__isnull=False,
                        type__isnull=True,
                        color__isnull=True,
                    )
                    | models.Q(
                        article__isnull=True,
                        category__isnull=True,
                        group__isnull=True,
                        type__isnull=False,
                        color__isnull=True,
                    )
                    | models.Q(
                        article__isnull=True,
                        category__isnull=True,
                        group__isnull=True,
                        type__isnull=True,
                        color__isnull=False,
                    )
                ),
                name="ck_promo_target_one_scope",
            ),
            models.UniqueConstraint(
                fields=("promotion", "article_key"),
                condition=models.Q(article__isnull=False),
                name="uq_promo_target_article",
            ),
            models.UniqueConstraint(
                fields=("promotion", "category"),
                condition=models.Q(category__isnull=False),
                name="uq_promo_target_category",
            ),
            models.UniqueConstraint(
                fields=("promotion", "group"),
                condition=models.Q(group__isnull=False),
                name="uq_promo_target_group",
            ),
            models.UniqueConstraint(
                fields=("promotion", "type"),
                condition=models.Q(type__isnull=False),
                name="uq_promo_target_type",
            ),
            models.UniqueConstraint(
                fields=("promotion", "color"),
                condition=models.Q(color__isnull=False),
                name="uq_promo_target_color",
            ),
        ]

    def clean(self):
        super().clean()
        if self.article is not None:
            self.article = self.article.strip() or None
        scopes = (
            self.article is not None,
            self.category_id is not None,
            self.group_id is not None,
            self.type_id is not None,
            self.color_id is not None,
        )
        if sum(scopes) != 1:
            raise ValidationError(
                _("Choose exactly one promotion target: article, category, group, type, or color.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        target = self.article or self.category or self.group or self.type or self.color
        return f"{self.promotion}: {target}"


class OrderDiscountSchedule(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    status = models.BooleanField(default=True, verbose_name=_("Status"))
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid from"),
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid to"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        db_table = "prices_order_discount_schedule"
        db_table_comment = "Наборы постоянных и срочных скидок от суммы заказа"
        verbose_name = _("Discount")
        verbose_name_plural = _("Discounts")
        ordering = ("-valid_from", "name")
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=(
                    models.Q(valid_from__isnull=True)
                    | models.Q(valid_to__isnull=True)
                    | models.Q(valid_to__gte=models.F("valid_from"))
                ),
                name="ck_order_schedule_valid_period",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to < self.valid_from
        ):
            raise ValidationError(
                {"valid_to": _("The end date must not be earlier than the start date.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrderDiscountTier(models.Model):
    schedule = models.ForeignKey(
        OrderDiscountSchedule,
        on_delete=models.CASCADE,
        related_name="tiers",
        verbose_name=_("Order volume discount schedule"),
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Minimum order amount (UAH)"),
    )
    max_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Upper order amount (exclusive, UAH)"),
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Discount percent"),
    )

    class Meta:
        db_table = "prices_order_discount_tier"
        db_table_comment = "Ступени скидок в зависимости от суммы заказа"
        verbose_name = _("Order discount tier")
        verbose_name_plural = _("Order discount tiers")
        ordering = ("min_order_amount", "pk")
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=models.Q(min_order_amount__gte=0),
                name="ck_order_tier_min_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(max_order_amount__isnull=True)
                    | models.Q(max_order_amount__gt=models.F("min_order_amount"))
                ),
                name="ck_order_tier_amount_range",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_percent__gt=0, discount_percent__lte=100),
                name="ck_order_tier_discount_percent",
            ),
        ]

    def clean(self):
        super().clean()
        if self.min_order_amount is not None and self.min_order_amount < 0:
            raise ValidationError(
                {"min_order_amount": _("The minimum order amount cannot be negative.")}
            )
        if (
            self.max_order_amount is not None
            and self.min_order_amount is not None
            and self.max_order_amount <= self.min_order_amount
        ):
            raise ValidationError(
                {"max_order_amount": _("The upper order amount must be greater than the minimum.")}
            )
        if self.discount_percent is not None and (
            self.discount_percent <= 0 or self.discount_percent > 100
        ):
            raise ValidationError(
                {"discount_percent": _("Discount must be greater than 0 and no more than 100 percent.")}
            )
        if self.schedule_id and self.min_order_amount is not None:
            overlapping = type(self)._default_manager.filter(
                schedule_id=self.schedule_id
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            overlapping = overlapping.filter(
                models.Q(max_order_amount__isnull=True)
                | models.Q(max_order_amount__gt=self.min_order_amount)
            )
            if self.max_order_amount is not None:
                overlapping = overlapping.filter(
                    min_order_amount__lt=self.max_order_amount
                )
            if overlapping.exists():
                raise ValidationError(
                    _("Order discount tiers in one schedule must not overlap.")
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        upper = (
            f"< {self.max_order_amount} UAH"
            if self.max_order_amount is not None
            else "and above"
        )
        return (
            f"{self.min_order_amount} UAH {upper}: "
            f"{self.discount_percent}%"
        )
