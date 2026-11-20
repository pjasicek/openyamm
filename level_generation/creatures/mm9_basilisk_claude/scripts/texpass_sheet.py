#!/usr/bin/env python3
"""Before/after sheets of the texture pass from the review viewer's shots (review/shots/{before,after}_<tier>_<shot>.png,
scripts/texpass_shots.sh), identical cameras: review/texpass_before_after_sheet.png (close-ups, both tiers),
review/texpass_body_sheet.png (full body and tail, both tiers)."""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
D = HERE / 'review' / 'shots'
W, H = 690, 508


def tile(stage, tier, shot):
    im = Image.open(D / f'{stage}_{tier}_{shot}.png').convert('RGB').resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle((6, 6, 230, 24), fill=(20, 20, 20))
    d.text((12, 9), f'{stage}  tier {tier.upper()}  {shot}', fill=(255, 255, 255))
    return im


def sheet(shots, out):
    s = Image.new('RGB', (W * 4, H * len(shots)), (30, 30, 30))
    for r, shot in enumerate(shots):
        for c, (stage, tier) in enumerate((('before', 'a'), ('after', 'a'), ('before', 'c'), ('after', 'c'))):
            s.paste(tile(stage, tier, shot), (c * W, r * H))
    s.save(HERE / 'review' / out)
    print('SHEET', out, s.size)


sheet(['head_q', 'head_front', 'mouth', 'frill_left', 'frill_right', 'back_top', 'flank', 'leg_front', 'leg_hind'],
      'texpass_before_after_sheet.png')
sheet(['body_q', 'body_left', 'tail'], 'texpass_body_sheet.png')
