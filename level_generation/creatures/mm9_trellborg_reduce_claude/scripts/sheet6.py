import sys
from PIL import Image
tag, out = sys.argv[1], sys.argv[2]; views = sys.argv[3].split(',') if len(sys.argv) > 3 else ['front', 'q34', 'side', 'back', 'top', 'low']
ims = [Image.open(f'review/labels/{tag}_{v}.png').convert('RGB') for v in views]; s = ims[0].size[0]
W = Image.new('RGB', (s * 3, s * ((len(ims) + 2) // 3)), 'white')
for i, im in enumerate(ims): W.paste(im, ((i % 3) * s, (i // 3) * s))
W.save(out)
