import sys
from PIL import Image
prefix, out = sys.argv[1], sys.argv[2]
views = sys.argv[3:] or ['front', 'q', 'side', 'top', 'back']
ims = [Image.open(f'{prefix}_{v}.png').convert('RGB').resize((360, 360)) for v in views]
s = Image.new('RGB', (360 * len(ims), 360)); [s.paste(im, (i * 360, 0)) for i, im in enumerate(ims)]; s.save(out)
