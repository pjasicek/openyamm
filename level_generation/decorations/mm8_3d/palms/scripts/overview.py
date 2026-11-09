#!/usr/bin/env python3
"""review/overview.png: every palm's compare.png stacked; review/overview_lods.png: every lods.png stacked."""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as dc
for name, out, scale in (('compare.png', 'overview.png', 0.6), ('lods.png', 'overview_lods.png', 0.5)):
    ims = [Image.open(os.path.join(dc.PALMS, 'review', sid, name)) for sid in dc.ORDER]
    ims = [i.resize((int(i.width * scale), int(i.height * scale)), Image.LANCZOS) for i in ims]
    sheet = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims)), 'white')
    y = 0
    for i in ims:
        sheet.paste(i, (0, y)); y += i.height
    sheet.save(os.path.join(dc.PALMS, 'review', out))
    print('SHEET', out)
