"""Review goblin enhanced vest R and trousers/bracers G masks."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
names = list(json.loads((HERE/'registration.json').read_text()))
for start in range(0, len(names), 32):
    selected = names[start:start+32]
    out = Image.new('RGB', (960, ((len(selected)+3)//4)*270), (30,30,30))
    draw = ImageDraw.Draw(out)
    for i,name in enumerate(selected):
        im = Image.open(HERE/f'aligned_2x/{name}.png')
        mask = Image.open(HERE/f'masks_2x/{name}.png')
        rgb = mask.convert('RGBA')
        rgb.putalpha(im.getchannel('A'))
        rgb = rgb.crop(im.getbbox())
        rgb.thumbnail((225,245))
        x=i%4*240; y=i//4*270
        out.paste(rgb,(x+(240-rgb.width)//2,y+25),rgb)
        draw.text((x+4,y+4),name,fill='white')
    out.save(HERE/f'review/mask_review_{start//32}.png')
