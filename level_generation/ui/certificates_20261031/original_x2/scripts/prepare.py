"""Prepares the Codex inputs for the MM6 and MM7 certificate backgrounds (6winbg.pcx, 7winbg.pcx): the native image,
and a 1536 x 1024 canvas holding it scaled to 1365 x 1024 (Lanczos) between flat grey bars, the frame the restoration
must keep. Usage: python3 -I prepare.py"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
LEGACY = os.path.join(REPO, 'assets_legacy', 'icons_20260926', 'engine', 'icons')
CANVAS = (1536, 1024)
INNER = (1365, 1024)
BAR = (128, 128, 128)

for name in ('6winbg', '7winbg'):
    native = Image.open(os.path.join(LEGACY, name + '.pcx')).convert('RGB')
    native.save(os.path.join(HERE, f'{name}_native.png'))
    canvas = Image.new('RGB', CANVAS, BAR)
    canvas.paste(native.resize(INNER, Image.LANCZOS), ((CANVAS[0] - INNER[0]) // 2, 0))
    canvas.save(os.path.join(HERE, f'{name}_canvas.png'))
    print('prepared', name)
