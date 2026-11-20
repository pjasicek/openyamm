"""Review all enhanced two-channel cloth stripe masks as colored overlays."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
names = list(json.loads((HERE / 'registration.json').read_text()))
for start in range(0, len(names), 42):
    out = Image.new('RGB', (1080, 1680), (48, 48, 48))
    draw = ImageDraw.Draw(out)
    for i, name in enumerate(names[start:start+42]):
        im = Image.open(HERE / f'aligned_2x/{name}.png').convert('RGBA')
        a = np.array(im)
        weight = np.array(Image.open(HERE / f'masks_2x/{name}.png')) / 255
        total=weight.sum(axis=2)[:,:,None]
        colors=weight[:,:,:1]*np.array([255,50,50])+weight[:,:,1:2]*np.array([50,150,255])
        a[:,:,:3]=np.round(a[:,:,:3]*(1-total*.65)+colors*.65).astype(np.uint8)
        tile = Image.fromarray(a).crop(im.getbbox())
        tile.thumbnail((170, 212), Image.Resampling.LANCZOS)
        x, y = i % 6 * 180, i // 6 * 240
        out.paste(tile, (x + (180-tile.width)//2, y+22), tile)
        draw.text((x+3, y+3), name, fill='white')
    out.save(HERE / f'review/mask_overlay_{start//42}.png')
