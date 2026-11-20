#!/usr/bin/env python3
"""Compose the native Obsidian frame pieces (art/frame_tl, frame_top, frame_left) into one 9-slice image,
art/frame9.png (corners 164 px, edges 256 px, empty centre), for CSS border-image with a slice of 164."""
from pathlib import Path

from PIL import Image, ImageOps

ART = Path(__file__).resolve().parent / 'art'
C, E = 164, 256
tl = Image.open(ART / 'frame_tl.png').convert('RGBA')
top = Image.open(ART / 'frame_top.png').convert('RGBA')
left = Image.open(ART / 'frame_left.png').convert('RGBA')
out = Image.new('RGBA', (2 * C + E, 2 * C + E))
out.alpha_composite(tl, (0, 0))
out.alpha_composite(ImageOps.mirror(tl), (C + E, 0))
out.alpha_composite(ImageOps.flip(tl), (0, C + E))
out.alpha_composite(tl.rotate(180), (C + E, C + E))
out.alpha_composite(top, (C, 0))
out.alpha_composite(ImageOps.flip(top), (C, C + E))
out.alpha_composite(left, (0, C))
out.alpha_composite(ImageOps.mirror(left), (C + E, C))
out.save(ART / 'frame9.png')
