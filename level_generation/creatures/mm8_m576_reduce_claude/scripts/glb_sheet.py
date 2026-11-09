"""review/glbclose/<label>_<spot>_<mode>.png -> one sheet per mode: rows = labels, columns = spots.
Usage: glb_sheet.py <out.png> <mode tex|clay> <label,...> [spot,...]"""
import sys
from PIL import Image, ImageDraw
out, mode, labels = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
spots = sys.argv[4].split(',') if len(sys.argv) > 4 else ['head_front', 'head_q34', 'head_back', 'torso', 'hand_l', 'hand_r',
                                                          'back', 'legs', 'attack']
S = 300; im = Image.new('RGB', (S * len(spots), S * len(labels)))
for j, lab in enumerate(labels):
    for i, sp in enumerate(spots):
        im.paste(Image.open(f'review/glbclose/{lab}_{sp}_{mode}.png').convert('RGB').resize((S, S)), (i * S, j * S))
        ImageDraw.Draw(im).text((i * S + 4, j * S + 4), f'{lab} {sp}', fill=(255, 255, 0))
im.save(out); print(out)
