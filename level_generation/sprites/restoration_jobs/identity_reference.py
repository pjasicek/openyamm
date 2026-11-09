"""Present accepted alpha faithfully to image tools that may expose hidden RGB."""
from PIL import Image


def write_identity_reference(source, destination, matte):
    """Keep the master's size; composite alpha only for the supporting reference."""
    with Image.open(source) as image:
        foreground = image.convert('RGBA')
        backdrop = Image.new('RGBA', foreground.size, (*matte, 255))
        Image.alpha_composite(backdrop, foreground).convert('RGB').save(destination)
