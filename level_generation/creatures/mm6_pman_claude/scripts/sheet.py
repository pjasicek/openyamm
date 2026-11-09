import sys
from PIL import Image
tag = sys.argv[1]; views = sys.argv[2].split(',') if len(sys.argv) > 2 else ['front', 'left', 'back', 'right']
ims = [Image.open(f'review/{tag}_{v}.png') for v in views]
out = Image.new('RGB', (sum(i.width for i in ims), max(i.height for i in ims)), 'white'); x = 0
for i in ims: out.paste(i, (x, 0)); x += i.width
out.save(f'review/{tag}_sheet.png')
