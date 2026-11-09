"""Contact every enhanced frame in every deterministic native palette preset."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'mm7_m514'))
from process import apply_variant


def run():
    names = list(json.loads((HERE/'registration.json').read_text()))
    variants = json.loads((HERE/'variants.json').read_text())['variants']
    width, height, rows = 180, 240, 8
    for start in range(0,len(names),rows):
        selected = names[start:start+rows]
        contact = Image.new('RGB',(width*len(variants),height*len(selected)),(48,48,48))
        draw = ImageDraw.Draw(contact)
        for row,name in enumerate(selected):
            im = Image.open(HERE/f'aligned_2x/{name}.png')
            mask = Image.open(HERE/f'masks_2x/{name}.png')
            box = im.getbbox()
            for col,variant in enumerate(variants):
                tile = apply_variant(im,mask,variant).crop(box)
                tile.thumbnail((width-12,height-30),Image.Resampling.LANCZOS)
                x=col*width+(width-tile.width)//2;y=row*height+25+(height-30-tile.height)//2
                contact.paste(tile,(x,y),tile)
                draw.text((col*width+3,row*height+3),f'{name} / {variant["palette_id"]}',fill='white')
        contact.save(HERE/f'review/all_variants_{start//rows}.png')


if __name__ == '__main__':
    run()
