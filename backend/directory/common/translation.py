from modeltranslation.translator import TranslationOptions, register  # type: ignore

from .models import (
    Category,
    Group,
    Brand,
    Series,
    Type,
    ProtectionDegree,
    Color,
    TypeModel,
    Execution,
)




@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = (
        "cat_name",
        "cat_description",
    )


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = (
        "grp_name",
        "grp_description",
    )


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = (
        "brd_name",
        "brd_description",
    )


@register(Series)
class SeriesTranslationOptions(TranslationOptions):
    fields = (
        "ser_name",
        "ser_description",
    )


@register(Type)
class TypeTranslationOptions(TranslationOptions):
    fields = (
        "typ_name",
        "typ_description",
    )    

@register(ProtectionDegree)
class ProtectionDegreeTranslationOptions(TranslationOptions):
    fields = (
       "ptd_description",
    )    

@register(Color)
class ColorTranslationOptions(TranslationOptions):
    fields = ("clr_name", "clr_description")    

@register(TypeModel)
class TypeModelTranslationOptions(TranslationOptions):
    fields = ("mdl_name", "mdl_description")

@register(Execution)
class ExecutionTranslationOptions(TranslationOptions):
    fields = ("exc_name", "exc_description")        