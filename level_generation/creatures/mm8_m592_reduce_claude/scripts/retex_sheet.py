import sys
from PIL import Image, ImageDraw
d, step, out, spots = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
cols = [('a_r100', 'clay', 'clay src'), (f'a_{step}', 'clay', f'clay {step}')] + [(f'{t}_{v}', 'tex', f'{t.upper()} {"src" if v == "r100" else step}') for t in 'abc' for v in ('r100', step)]
S = 240; sh = Image.new('RGB', (S * len(cols), 18 + S * len(spots)), (18, 18, 18)); dr = ImageDraw.Draw(sh)
for j, (_, _, lab) in enumerate(cols): dr.text((j * S + 5, 3), lab, fill=(255, 230, 120))
for i, s in enumerate(spots):
    for j, (l, m, _) in enumerate(cols):
        sh.paste(Image.open(f'{d}/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 18 + i * S))
    dr.text((4, 22 + i * S), s, fill=(255, 255, 255))
sh.save(out); print(out)
