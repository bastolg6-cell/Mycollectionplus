from django import template

register = template.Library()

@register.filter(name='get_qty') # On force le nom pour être sûr
def get_qty(dictionary, key):
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)