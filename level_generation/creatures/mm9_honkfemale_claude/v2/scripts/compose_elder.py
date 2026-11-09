#!/usr/bin/env python3
"""Elder Honk (HONKF3) head base colour from the Meshy head retexture on the paid head UVs, 2026-10-30 night pass: the 4K return goes once
to the head square of the set (lower left, 0.8 of the side, as compose_head_texpass.py); hands and everything outside the square stay
from the tier A set. Replaces the recolour of tier A (kept as v2/textures/honkf_elder_head_basecolor_recolour.png, written by
head_tier_f3.py). Run from the project folder."""
import shutil
from pathlib import Path
from PIL import Image
T = Path('v2/textures')
old = T / 'honkf_elder_head_basecolor_recolour.png'
if not old.exists():
    shutil.copy2(T / 'honkf_elder_head_basecolor.png', old)
a = Image.open(T / 'honkf_head_basecolor.png').convert('RGB')
n = a.size[0]
k = int(round(n * 0.8))
a.paste(Image.open('meshy/head_retexture_elder/texture_urls_0_base_color.png').convert('RGB').resize((k, k), Image.LANCZOS), (0, n - k))
a.save(T / 'honkf_elder_head_basecolor.png')
print('ELDER', n, k)
