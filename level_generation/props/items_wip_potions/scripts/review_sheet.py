"""Source icon, baseline low angle, replacement above and low angle in owned inventory order."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT=Path(__file__).resolve().parents[1]
items=json.loads((PROJECT/'ownership.json').read_text())
size=200
for page in range(0,len(items),14):
    rows=items[page:page+14]
    sheet=Image.new('RGB',(size*8,235*7),(30,34,42))
    draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(rows):
        icon=row['icon']; x=(i%2)*size*4; y=(i//2)*235
        draw.text((x+8,y+5),f'{icon}: {row["names"][0]}',fill='white')
        paths=[PROJECT/f'references/{icon}.png',PROJECT/f'review/baseline/{icon}_low.png',
               PROJECT/f'review/vessels/{icon}_above.png',PROJECT/f'review/vessels/{icon}_low.png']
        if icon=='7item182':
            paths[2:]=[PROJECT/f'review/baseline/{icon}_above.png',PROJECT/f'review/baseline/{icon}_low.png']
        for k,path in enumerate(paths):
            if path.exists():
                im=Image.open(path).convert('RGBA');im.thumbnail((size-8,size-8))
                sheet.paste(im,(x+k*size+(size-im.width)//2,y+25+(size-im.height)//2),im)
            draw.text((x+k*size+8,y+220),['Icon','Old low','New above','New low'][k],fill=(170,180,190))
    output=PROJECT/f'review/contact_{page//14+1:02}.png'
    sheet.save(output)
    print(output)
