"""Icon beside the five review views."""
import sys
from PIL import Image
prefix, out = sys.argv[1:3]
views = ['front', 'three_quarter', 'side', 'back', 'above']
sheet = Image.new('RGB', (6 * 320, 360), (40, 42, 46))
icon = Image.open('references/icon_7item263.png').convert('RGBA')
icon.thumbnail((300, 340))
sheet.paste(icon, (10, 10), icon)
for i, view in enumerate(views):
    image = Image.open(f'{prefix}_{view}.png').convert('RGBA').resize((320, 320))
    sheet.paste(image, ((i + 1) * 320, 20), image)
sheet.save(out)
