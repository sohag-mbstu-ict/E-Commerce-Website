from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Usage: {{ some_dict|get_item:key }} - looks up a dict value by a variable key in templates."""
    if not isinstance(dictionary, dict):
        return ''
    return dictionary.get(key, '')
