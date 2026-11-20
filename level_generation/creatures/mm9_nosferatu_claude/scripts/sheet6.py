import sys
from PIL import Image
pre, out = sys.argv[1:3]; s = int(sys.argv[3]) if len(sys.argv) > 3 else 600
ks = sys.argv[4] if len(sys.argv) > 4 else 'qflbru'
im = Image.new('RGB', (s * 3, s * ((len(ks) + 2) // 3)))
for i, k in enumerate(ks): im.paste(Image.open(f'{pre}_{k}.png').convert('RGB').resize((s, s)), (s * (i % 3), s * (i // 3)))
im.save(out)
