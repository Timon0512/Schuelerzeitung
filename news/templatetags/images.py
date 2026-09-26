from django import template
from django.utils.html import format_html
from news.image_variants import image_attributes

register = template.Library()


@register.simple_tag
def responsive_image(media, private=False, sizes="100vw"):
    attrs = image_attributes(media, private=private)
    if attrs["srcset"]:
        return format_html('src="{}" srcset="{}" sizes="{}"', attrs["src"], attrs["srcset"], sizes)
    return format_html('src="{}"', attrs["src"])
