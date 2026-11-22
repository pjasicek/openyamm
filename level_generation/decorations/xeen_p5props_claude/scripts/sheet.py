import sys, glob
from PIL import Image
prefix, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
views = ['front', 'q', 'side', 'top']
S = Image.new('RGB', (300 * 4, 300 * n))
for i in range(n):
    for j, v in enumerate(views):
        S.paste(Image.open(f'{prefix}_{i}_{v}.png').convert('RGB').resize((300, 300)), (j * 300, i * 300))
S.save(out)
