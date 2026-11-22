import json, os
from PIL import Image
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(here, 'work', '_frames.json')))
ims = [Image.open(p) for p in d['tiles']]
cols = min(5, len(ims)); rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (500 * cols, 500 * rows), (255, 255, 255))
for i, im in enumerate(ims):
    S.paste(im, ((i % cols) * 500, (i // cols) * 500)); os.remove(d['tiles'][i])
S.save(os.path.join(here, 'review', d['out']))
