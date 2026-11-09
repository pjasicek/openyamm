from PIL import Image
import sys
for v in ('front','q34','back','left','right'):
    s=Image.new('RGB',(2100,700))
    for i in (1,2,3): s.paste(Image.open(f'review/mm9/z{i}_{v}.png').convert('RGB'),((i-1)*700,0))
    s.save(f'review/mm9/row_{v}.png')
