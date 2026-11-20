#!/usr/bin/env python3
"""Stack the per-model review sheets: review/overview_cacti.png (bushes) and review/overview_pots.png (potted
plants). Usage: overview.py"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REVIEW
groups = {'overview_bushes.png': 'bush03 bush10 bush11 bush13 bush16 bush12 bush02'.split(),
          'overview_pots.png': 'plant01a plant11a plant02a plant01b plant07b plant03b plant04b'.split()}
for out, ids in groups.items():
    ims = [Image.open(os.path.join(REVIEW, i, 'sheet.png')) for i in ids if os.path.exists(os.path.join(REVIEW, i, 'sheet.png'))]
    sheet = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims)), 'white'); y = 0
    for i in ims:
        sheet.paste(i, (0, y)); y += i.height
    sheet.save(os.path.join(REVIEW, out)); print('OVERVIEW', os.path.join(REVIEW, out))
