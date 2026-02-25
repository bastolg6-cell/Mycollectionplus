from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Permet de récupérer une valeur dans un dictionnaire 
    via une clé dynamique dans un template Django.
    Usage: {{ mon_dict|get_item:ma_cle }}
    """
    if dictionary:
        # On convertit la clé en string car les clés de JSONField 
        # sont souvent stockées en tant que chaînes de caractères.
        return dictionary.get(str(key))
    return None
