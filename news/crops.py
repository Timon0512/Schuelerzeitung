import re

MIN_ZOOM = 100
MAX_ZOOM = 300
TEXT_RATIOS = {"original": None, "4-3": "4 / 3", "1-1": "1 / 1", "16-9": "16 / 9"}
CROP_PATTERN = re.compile(r"(original|4-3|1-1|16-9)/([0-9]{1,3})/([0-9]{1,3})/([0-9]{3})")


def text_crop(value):
    match = CROP_PATTERN.fullmatch(value or "")
    if not match:
        return None
    ratio = match[1]
    x, y, zoom = map(int, match.groups()[1:])
    if x > 100 or y > 100 or not MIN_ZOOM <= zoom <= MAX_ZOOM:
        return None
    if ratio == "original" and zoom == MIN_ZOOM:
        return None
    return ratio, x, y, zoom


def crop_style(x, y, zoom):
    return f"--crop-x:{x}%;--crop-y:{y}%;--crop-zoom:{zoom / 100:g}"
