"""Join <prefix>_{q34,front,side,back}.png into <prefix>.png. Args: prefix [size]"""
import sys
from PIL import Image
p = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 600
v = ['q34', 'front', 'side', 'back']
s = Image.new('RGB', (n * 4, n))
for i, k in enumerate(v): s.paste(Image.open(f'{p}_{k}.png').convert('RGB').resize((n, n)), (i * n, 0))
s.save(p + '.png')
