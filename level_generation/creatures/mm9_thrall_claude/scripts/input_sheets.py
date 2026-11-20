"""Codex inputs from the true-handed MM9 renders (work/ref)."""
from PIL import Image
L = 'abc'
for i in (1, 2, 3):
    s = Image.new('RGB', (5 * 640, 640), (107, 107, 107))
    for k, v in enumerate(['q34', 'front', 'left', 'back', 'right']):
        s.paste(Image.open(f'work/ref/b{i}_{v}.png').convert('RGB').resize((640, 640), Image.LANCZOS), (k * 640, 0))
    s.save(f'references_hd/mm9_views_{L[i-1]}.png')
    h = Image.new('RGB', (4 * 700, 700), (107, 107, 107))
    for k, v in enumerate(['front', 'q34', 'left', 'back']):
        h.paste(Image.open(f'work/ref/h{i}_{v}.png').convert('RGB').resize((700, 700)), (k * 700, 0))
    h.save(f'references_hd/mm9_head_views_{L[i-1]}.png')
    w = Image.new('RGB', (5 * 560, 560), (107, 107, 107))
    for k, v in enumerate(['q34', 'front', 'left', 'back', 'right']):
        w.paste(Image.open(f'work/ref/w{i}_{v}.png').convert('RGB').resize((560, 560)), (k * 560, 0))
    w.save(f'references_hd/mm9_waist_views_{L[i-1]}.png')
    Image.open(f'source/t{i}/skins/thrall{i}.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(f'references_hd/mm9_skin_x4_{L[i-1]}.png')
