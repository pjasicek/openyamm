"""Codex inputs from the true-handed MM9 renders."""
from PIL import Image
L = 'abc'
V = ['q34', 'front', 'left', 'back', 'right']
for i in (1, 2, 3):
    s = Image.new('RGB', (5 * 640, 1000), (107, 107, 107))
    for k, v in enumerate(V):
        im = Image.open(f'review/mm9_true/t{i}_{v}.png').convert('RGB').crop((130, 100, 1270, 1300 + 100)).resize((640, 730))
        im = Image.open(f'review/mm9_true/t{i}_{v}.png').convert('RGB').crop((100, 0, 1300, 1400)).resize((640, 747))
        s.paste(im, (k * 640, 0))
    s = s.crop((0, 0, 3200, 747))
    s.save(f'references_hd/mm9_views_{L[i-1]}.png')
    h = Image.new('RGB', (4 * 700, 700), (107, 107, 107))
    for k, v in enumerate(['front', 'q34', 'left', 'back']):
        h.paste(Image.open(f'review/mm9_true/h{i}_{v}.png').convert('RGB').resize((700, 700)), (k * 700, 0))
    h.save(f'references_hd/mm9_head_views_{L[i-1]}.png')
    Image.open(f'source/z{i}/skins/zombie{i}.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(f'references_hd/mm9_skin_x4_{L[i-1]}.png')
s = Image.new('RGB', (3 * 700, 700), (107, 107, 107))
for k, v in enumerate(['front', 'q34', 'back']):
    s.paste(Image.open(f'review/mm9_true/s1_{v}.png').convert('RGB').resize((700, 700)), (k * 700, 0))
s.save('references_hd/mm9_shin_views.png')
