"""Contact sheets: inventory, baseline, clay, textured above/quarter/low/underside."""
import json
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[2]
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)


def main():
    rows=json.loads((PROJECT/'ownership.json').read_text())
    for start in range(0,len(rows),8):
        sheet=Image.new('RGB',(1760,min(8,len(rows)-start)*285+36),(34,37,43));draw=ImageDraw.Draw(sheet)
        for i,label in enumerate(('ICON','BASELINE','CLAY','ABOVE','THREE QUARTER','LOW SIDE','UNDERSIDE')):
            draw.text((i*250+12,8),label,font=FONT,fill='#aeb8c5')
        for j,row in enumerate(rows[start:start+8]):
            icon=row['icon'];y=36+j*285
            draw.line((0,y,1760,y),fill='#5c6571')
            name=icon+' — '+row['items'][0]['name']
            draw.text((10,y+5),name,font=FONT,fill='white')
            files=[ROOT/row['icon_reference'],PROJECT/f'review/baseline/{icon}_above.png',PROJECT/f'review/clay/{icon}_three_quarter.png',
                   PROJECT/f'review/replacement/{icon}_above.png',PROJECT/f'review/replacement/{icon}_three_quarter.png',
                   PROJECT/f'review/replacement/{icon}_low.png',PROJECT/f'review/replacement/{icon}_underside.png']
            for col,f in enumerate(files):
                if not f.exists():continue
                im=Image.open(f).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((236,240),Image.Resampling.LANCZOS)
                sheet.paste(im,(col*250+(250-im.width)//2,y+35+(240-im.height)//2),im)
        sheet.save(PROJECT/f'review/comparison_{start//8+1:02}.jpg',quality=94)
    receipts=json.loads((PROJECT/'work/build_receipts.json').read_text())
    lod_rows=[row for row in rows if receipts[row['icon']].get('lod_triangles')]
    sheet=Image.new('RGB',(1240,len(lod_rows)*250+36),(34,37,43));draw=ImageDraw.Draw(sheet)
    for col,label in enumerate(('ICON','LOD 0','LOD 1','LOD 2','LOD 3')):draw.text((col*248+12,8),label,font=FONT,fill='#aeb8c5')
    for j,row in enumerate(lod_rows):
        icon=row['icon'];y=36+j*250;draw.text((8,y+4),icon,font=FONT,fill='white')
        counts=[receipts[icon]['triangles']]+receipts[icon]['lod_triangles']
        files=[ROOT/row['icon_reference'],PROJECT/f'review/replacement/{icon}_three_quarter.png']
        files.extend(PROJECT/f'review/lod{level}/{icon}_three_quarter.png' for level in (1,2,3))
        for col,f in enumerate(files):
            if not f.exists():continue
            im=Image.open(f).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((232,210),Image.Resampling.LANCZOS)
            sheet.paste(im,(col*248+(248-im.width)//2,y+28+(210-im.height)//2),im)
            if col:draw.text((col*248+8,y+4),str(counts[col-1])+' tris',font=FONT,fill='#cccccc')
    sheet.save(PROJECT/'review/lod_comparison.jpg',quality=94)
    print('Saved nine icon/baseline/clay/four-view sheets and the LOD comparison')


if __name__=='__main__':main()
