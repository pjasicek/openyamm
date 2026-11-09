"""review/close/sheet_<name>.png: rows = spots, columns = labels (textured, then clay). Usage: close_sheet.py <name> <labels,> <spots,> [size]"""
import sys
from PIL import Image, ImageDraw
name, labels, spots = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
S = int(sys.argv[4]) if len(sys.argv) > 4 else 320
modes = ['tex', 'clay']
sheet = Image.new('RGB', (S * len(labels) * 2, (S + 18) * len(spots)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for i, sp in enumerate(spots):
    for m, mode in enumerate(modes):
        for j, lb in enumerate(labels):
            x = (m * len(labels) + j) * S; y = i * (S + 18)
            sheet.paste(Image.open(f'review/close/{lb}_{sp}_{mode}.png').convert('RGB').resize((S, S)), (x, y + 18))
            d.text((x + 4, y + 3), f'{sp} {lb} {mode}', fill=(240, 230, 140))
sheet.save(f'review/close/sheet_{name}.png'); print('SHEET', name)
