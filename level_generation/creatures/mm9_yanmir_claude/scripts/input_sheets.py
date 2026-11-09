"""Codex inputs from the true-handed MM9 renders (references_hd/renders, scripts/make_refs.sh): full views without the staff,
torso, legs and head sheets, the skin x4. Run from the project folder."""
from PIL import Image
R = 'references_hd'
V = ['q34', 'front', 'left', 'back', 'right']


def sheet(prefix, views, size, out):
    s = Image.new('RGB', (len(views) * size, size), (107, 107, 107))
    for k, v in enumerate(views):
        s.paste(Image.open(f'{R}/renders/{prefix}_{v}.png').convert('RGB').resize((size, size), Image.LANCZOS), (k * size, 0))
    s.save(f'{R}/{out}.png')


sheet('full', V, 640, 'mm9_views')
sheet('fullw', V, 640, 'mm9_views_staff')
sheet('torso', ['front', 'left', 'back', 'q34'], 700, 'mm9_torso_views')
sheet('legs', ['front', 'left', 'back', 'q34'], 700, 'mm9_leg_views')
sheet('head', ['front', 'q34', 'left', 'back'], 700, 'mm9_head_views')
Image.open('source/true/skins/yanmir.png').convert('RGB').resize((2048, 2048), Image.LANCZOS).save(f'{R}/mm9_skin_x4.png')
