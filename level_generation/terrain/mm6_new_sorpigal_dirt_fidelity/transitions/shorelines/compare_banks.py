"""Compare native, previous and current shoreline banks over the same accepted water."""
from PIL import Image, ImageDraw
from build import P, TERRAIN
out = Image.new('RGB', (1200, 1250), '#202933')
draw = ImageDraw.Draw(out)
for row, name in enumerate(('6wtrdrn', '6wtrdrne', '6wtrdrxne')):
    sources = [('Original', TERRAIN / 'mm6_new_sorpigal/rgba'),
               ('Previous', P / 'versions/v1/runtime_x2/worlds/mm6/terrain_x2'),
               ('New bank', P / 'runtime_x2/worlds/mm6/terrain_x2')]
    for col, (label, base) in enumerate(sources):
        a = Image.open(base / (name + '.png')).convert('RGBA').resize((400, 400))
        water = Image.open(P / 'runtime_x2/worlds/mm6/terrain_x2/6hdwtr000.png').convert('RGBA').resize((400, 400))
        water.alpha_composite(a)
        out.paste(water.convert('RGB'), (col * 400, row * 416 + 16))
        draw.text((col * 400, row * 416), label + ' ' + name)
out.save(P / 'bank_comparison.png')
