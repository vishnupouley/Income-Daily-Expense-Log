from django.utils.safestring import mark_safe
from django import template
import json

register = template.Library()


@register.filter(name='tojson')
def tojson(dict: dict) -> json:
    """ Convert dictionary to JSON string """
    return mark_safe(json.dumps(dict))


@register.filter(name='get_item')
def get_item(dictionary: dict, key: str):
    """ Get item from dictionary by key """
    return dictionary.get(key)


@register.filter(name='get_title')
def get_title(title: str):
    """ Convert snake_case to Title Case """
    return title.replace("_", " ").title()
