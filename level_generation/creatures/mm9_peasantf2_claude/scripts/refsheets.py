"""Five-view sheets of the MM9 reference renders + the skin x4. Args: <refs dir> <out dir>"""
import sys
from PIL import Image
refs, out = sys.argv[1:3]
for pre, name in [('mm9', 'views'), ('chest', 'chest_views'), ('head', 'head_views'), ('skirt', 'skirt_views')]:
    for t in 'ab':
        ims = [Image.open(f'{refs}/{pre}_{t}_{v}.png').convert('RGB').resize((512, 512)) for v in ('q34', 'front', 'left', 'back', 'right')]
        S = Image.new('RGB', (512 * 5, 512))
        for k, im in enumerate(ims):
            S.paste(im, (512 * k, 0))
        S.save(f'{out}/mm9_{name}_{t}.png')
