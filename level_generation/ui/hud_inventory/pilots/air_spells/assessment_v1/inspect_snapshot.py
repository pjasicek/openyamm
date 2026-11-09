"""Diagnostic extraction of the first Air spell sheet; no automatic fitting or acceptance."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
HUD=HERE.parents[1]
sys.path.insert(0,str(HUD))
from finalize_classification import ROOT, read, digest
from freeze_targets import rendered
import registration

def main():
    out=HERE/'assessment_v1'
    out.mkdir(exist_ok=True)
    attempt=HUD/'checkpoint/attempts/c6f45ee23332498eb4b9a81120bb1906'
    raw=Image.open(attempt/'raw.png').convert('RGBA')
    job=next(j for j in read('jobs.json')['jobs'] if j['id']=='spell_icon_pair-f7d2c87d07da')
    targets={t['id']:t for t in read('expected_targets.json')['targets']}
    payload=json.loads((attempt/'payload.json').read_text())
    crops=[(19,53,400,450),(446,53,826,450),(19,510,404,886),(446,510,826,886),
           (19,946,403,1350),(446,946,826,1350),(19,1410,402,1812),(446,1410,826,1812)]
    page=Image.open(HUD/'exports/engine/icons_x2/sba000.png').convert('RGBA')
    nativepage=Image.open(ROOT/'assets_dev/engine/icons/sba000.bmp').convert('RGBA').resize(page.size,Image.Resampling.NEAREST)
    pages=[page.copy(),page.copy(),nativepage.copy(),nativepage.copy()]
    results=[]
    for index,(member,box) in enumerate(zip(job['members'],crops)):
        image=raw.crop(box)
        pixels=np.array(image)
        # Diagnostic matte only; contaminated contours are not approved by this coarse extraction.
        key=(pixels[:,:,0]>200)&(pixels[:,:,1]<70)&(pixels[:,:,2]>200)
        pixels[key]=0
        image=Image.fromarray(pixels).convert('RGBa').resize(tuple(member['export_region'][2:]),Image.Resampling.LANCZOS).convert('RGBA')
        artifact=out/(targets[member['target']]['runtime_name']+'.png')
        image.save(artifact)
        evidence=registration.evidence(member,targets[member['target']],artifact,out/'registration')
        x,y,w,h=payload['page_crops'][index//2]['final_draw_xywh']
        pages[index%2].alpha_composite(image,(x,y))
        native=rendered(Image.open(ROOT/member['source_path']),'hud').resize((w,h),Image.Resampling.NEAREST)
        pages[2+index%2].alpha_composite(native,(x,y))
        results.append(dict(cell=member['id'],raw_crop_xyxy=box,review=evidence))
    for name,picture in zip(['restored-colored','restored-sepia','native-colored','native-sepia'],pages):
        picture.save(out/(name+'.png'))
    (out/'processing.json').write_text(json.dumps(dict(attempt='c6f45ee23332498eb4b9a81120bb1906',
        raw_sha256=digest(attempt/'raw.png'),method='observed whole-panel crops; diagnostic premultiplied resize; coarse magenta key',
        status='diagnostic_only_not_accepted',cells=results),indent=2)+'\n')
    (out/'inspect_snapshot.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({r['cell']:r['review']['failures'] for r in results},indent=2))
if __name__=='__main__':
    main()
