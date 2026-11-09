"""Codex inputs from the true-handed MM9 renders (references_hd/mm9_*): flat-lit views of each tier, head, hand and foot sheets, skins x4."""
from PIL import Image
R = 'references_hd'
V = ['q34', 'front', 'left', 'back', 'right']
for i, L in ((1, 'a'), (2, 'b'), (3, 'c')):
    s = Image.new('RGB', (5 * 640, 640), (107, 107, 107))
    for k, v in enumerate(V):
        s.paste(Image.open(f'{R}/mm9_flat/t{i}_{v}.png').convert('RGB').resize((640, 640), Image.LANCZOS), (k * 640, 0))
    s.save(f'{R}/mm9_views_{L}.png')
    Image.open(f'source/t{i}/skins/colloidal{i}.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(f'{R}/mm9_skin_x4_{L}.png')
    h = Image.new('RGB', (4 * 700, 700), (107, 107, 107))
    for k, v in enumerate(['front', 'q34', 'left', 'back']):
        h.paste(Image.open(f'{R}/mm9_head/t{i}_{v}.png').convert('RGB').resize((700, 700), Image.LANCZOS), (k * 700, 0))
    h.save(f'{R}/mm9_head_views_{L}.png')
for nm, d, p in (('hand', 'mm9_hand', 'b'), ('foot', 'mm9_foot', 'b')):
    w = Image.new('RGB', (5 * 560, 560), (107, 107, 107))
    for k, v in enumerate(V):
        w.paste(Image.open(f'{R}/{d}/{p}_{v}.png').convert('RGB').resize((560, 560), Image.LANCZOS), (k * 560, 0))
    w.save(f'{R}/mm9_{nm}_views_b.png')
