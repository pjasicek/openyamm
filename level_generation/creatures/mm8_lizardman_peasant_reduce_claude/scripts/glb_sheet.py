#!/usr/bin/env python3
"""review/glbclose sheet: rows = labels (e.g. src fr75), columns = spots, textured then clay.
Usage: glb_sheet.py <out.png> <label> [label ...] [-- spot,spot,...]"""
import sys
from PIL import Image, ImageDraw
args = sys.argv[2:]; spots = ['head_front', 'head_q34', 'head_side', 'torso', 'apron', 'hand_r', 'hand_l', 'feet', 'back', 'fidget']
if '--' in args:
    spots = args[args.index('--') + 1].split(','); args = args[:args.index('--')]
S = 240; sheet = Image.new('RGB', (S * len(spots), S * 2 * len(args)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for r, lab in enumerate(args):
    for m, mode in enumerate(['tex', 'clay']):
        for c, sp in enumerate(spots):
            im = Image.open(f'review/glbclose/{lab}_{sp}_{mode}.png').convert('RGB').resize((S, S))
            sheet.paste(im, (c * S, (r * 2 + m) * S)); d.text((c * S + 4, (r * 2 + m) * S + 4), f'{lab} {sp}', fill=(255, 230, 120))
sheet.save(sys.argv[1])
