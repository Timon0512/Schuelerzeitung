"""The only HTML boundary: images are resolved from explicit article grants."""
from html import escape
from html.parser import HTMLParser
import nh3


def clean_body(value, images=(), *, private=False, render=False, captions=None):
    allowed = {str(image.pk): image for image in images}
    cleaned = nh3.clean(value, tags={"p", "h2", "h3", "strong", "em", "ul", "ol", "li", "blockquote", "a", "br", "img"},
                        attributes={"a": {"href", "title"}, "img": {"data-media-id"}},
                        url_schemes={"http", "https", "mailto"})

    class Images(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.output = []

        def handle_starttag(self, tag, attrs):
            if tag != "img":
                self.output.append(self.get_starttag_text())
                return
            image = allowed.get(dict(attrs).get("data-media-id"))
            if image:
                route = "/redaktion/medien/" if private else "/medien/"
                tag = f'<img data-media-id="{image.pk}" src="{route}{image.pk}" alt="{escape(image.alt_text, quote=True)}">'
                if render:
                    # Inline-safe wrapper: editor images may be inside a paragraph.
                    dimensions = f' width="{image.width}" height="{image.height}" loading="lazy"'
                    tag = tag[:-1] + dimensions + ">"
                caption = (captions or {}).get(str(image.pk)) or image.caption
                if (private or render) and caption:
                    tag = f'<span class="text-image">{tag}<span class="caption">{escape(caption)}</span></span>'
                self.output.append(tag)

        def handle_endtag(self, tag):
            if tag != "img":
                self.output.append(f"</{tag}>")

        def handle_data(self, data):
            self.output.append(data)

        def handle_entityref(self, name):
            self.output.append(f"&{name};")

        def handle_charref(self, name):
            self.output.append(f"&#{name};")

    parser = Images()
    parser.feed(cleaned)
    return "".join(parser.output)
