"""Same-camera evidence, preferring reviewed sculptural replacements to early component studies."""
import json
from pathlib import Path

from PIL import Image,ImageDraw

P=Path(__file__).resolve().parents[1]


def main():
    rows=json.loads((P/'ownership.json').read_text())
    headings=['Inventory','Old relief','New clay','Above','Three quarter','Low','Underside']
    for start in range(0,len(rows),7):
        subset=rows[start:start+7]
        sheet=Image.new('RGB',(1400,40+len(subset)*200),(44,46,50));draw=ImageDraw.Draw(sheet)
        for n,h in enumerate(headings):draw.text((n*200+8,10),h,fill='white')
        for y,r in enumerate(subset):
            icon=r['icon'];route='meshy' if (P/'work/meshy'/f'{icon}_export.glb').exists() else 'blender'
            inputs=[Path(r['icon_reference']),P/'review/baseline'/f'{icon}_above.png',
                    P/f'review/{route}_clay'/f'{icon}_above.png']
            inputs += [P/f'review/{route}'/f'{icon}_{v}.png' for v in ['above','three_quarter','low','underside']]
            for x,path in enumerate(inputs):
                assert path.exists(),path
                image=Image.open(path).convert('RGBA')
                if x in [1,2,3]:image=image.transpose(Image.Transpose.ROTATE_270)
                image.thumbnail((190,172),Image.Resampling.LANCZOS)
                sheet.paste(image,(x*200+(200-image.width)//2,40+y*200),image)
            draw.text((8,40+y*200+174),icon+' '+r['items'][0]['name'],fill='white')
        sheet.save(P/'review'/f'comparison_{start//7+1:02d}.png')


if __name__=='__main__':main()
