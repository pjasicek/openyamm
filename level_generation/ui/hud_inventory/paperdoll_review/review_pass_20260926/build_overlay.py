"""Build the slice-only browser overlay and a complete native/old/repaired visual audit."""
import json
from pathlib import Path
from urllib.parse import unquote
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parent
HERE=OUT.parent

def main():
    read=lambda name:json.loads((OUT/name).read_text())
    review=read('review.original.json');stage=read('stage_manifest.json');repairs=read('repairs.json')
    stage['staging_only']=True
    stage['final_ledger_acceptance_authorized']=False
    stage['approved_originals_with_pending_replacements']=[
        target for target,record in repairs['results'].items() if record['previously_approved']]
    (OUT/'stage_manifest.json').write_text(json.dumps(stage,indent=2)+'\n')
    payload={'id':'20260926','exported_at':review['exported_at'],'decisions':review['decisions'],
             'placements':read('placements.json')['placements'],'staged':stage['records'],'repairs':repairs['results']}
    (OUT/'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = '+json.dumps(payload,separators=(',',':'))+';\n')
    rows=list(repairs['results'].items());dest=OUT/'repair_contacts';dest.mkdir(exist_ok=True)
    for start in range(0,len(rows),20):
        sheet=Image.new('RGB',(1600,1400),(55,65,70));draw=ImageDraw.Draw(sheet)
        for i,(target,a) in enumerate(rows[start:start+20]):
            x=(i%5)*320;y=(i//5)*350
            draw.text((x+3,y+3),a['name']+(' [was accepted]' if a['previously_approved'] else ''),fill='white')
            draw.text((x+3,y+18),','.join(a['categories'])[:48],fill='#e6b581')
            ims=[Image.open(HERE/'native'/(target+'.png')).convert('RGBA'),
                 Image.open(HERE/unquote(a['old_path'])).convert('RGBA'),Image.open(HERE/a['path']).convert('RGBA')]
            ims[0]=ims[0].resize(ims[1].size,Image.Resampling.NEAREST)
            scale=min(1,102/max(im.width for im in ims),308/max(im.height for im in ims))
            for j,im in enumerate(ims):
                im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
                sheet.paste(im,(x+j*106+(102-im.width)//2,y+40),im)
        sheet.save(dest/f'{start//20+1:02}.jpg')
    print('Browser overlay and',len(rows),'repair comparisons written')

if __name__=='__main__':main()
