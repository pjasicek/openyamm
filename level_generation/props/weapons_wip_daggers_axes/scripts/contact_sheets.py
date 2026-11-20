"""Readable source/clay/PBR comparison sheets; every review angle remains individually inspectable."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

P=Path(__file__).resolve().parents[1]
R=P.parents[2]
owned=json.loads((P/'ownership.json').read_text())
for start in range(0,len(owned),8):
    rows=owned[start:start+8]
    available=[r for r in rows if (P/'review/revised'/f'{r["icon"]}_above.png').exists()]
    if not available: continue
    cols=[('icon',None),('clay','three_quarter'),('revised','above'),('revised','three_quarter'),('clay','low'),('revised','back'),('revised','underside')]
    sheet=Image.new('RGB',(7*200,len(available)*220),(51,55,61)); draw=ImageDraw.Draw(sheet)
    for y,row in enumerate(available):
        for x,(mode,view) in enumerate(cols):
            path=R/row['icon_reference'] if mode=='icon' else P/'review'/mode/f'{row["icon"]}_{view}.png'
            im=Image.open(path).convert('RGBA'); im.thumbnail((190,190))
            sheet.paste(im,(x*200+(200-im.width)//2,y*220+24+(190-im.height)//2),im)
            draw.text((x*200+5,y*220+5),row['icon'] if x==0 else f'{mode} {view}',fill='white')
    sheet.save(P/'review'/f'contact_{start//8+1:02}.png')
    print(start//8+1,[r['icon'] for r in available])
