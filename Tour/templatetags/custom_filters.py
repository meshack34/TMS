from django import template

register = template.Library()

# @register.filter
# def split(value, delimiter=","):
#     return value.split(delimiter)
# tour/templatetags/custom_filters.py
from django import template
from django.template.defaultfilters import date as _date
from django.utils.text import slugify as _slugify

register = template.Library()

@register.filter
def split(value, sep=","):
    if value is None:
        return []
    return [v.strip() for v in value.split(sep)]

@register.filter
def nice_date(value, fmt="j M Y"):
    if not value:
        return ""
    return _date(value, fmt)

@register.filter
def slugify(value):
    if not value:
        return ""
    return _slugify(value)
