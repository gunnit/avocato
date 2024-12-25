from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter(is_safe=True)
def to_json(value):
    """Convert a Python object to a JSON string."""
    if value is None:
        return 'null'
    return mark_safe(json.dumps(value))
