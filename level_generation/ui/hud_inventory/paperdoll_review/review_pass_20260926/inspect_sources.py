import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT=Path(__file__).resolve().parent
HERE=OUT.parent
sys.path.insert(0,str(HERE))
from prepare_raw_candidates import reference_geometry, crop_rect, sheet_kind
import queue as queue_module


def read(path): return json.loads(Path(path).read_text())

def foreground(image):
    a=np.asarray(image.convert('RGBA')).astype(np.int16)
    mask=a[:,:,3]>96
    if sheet_kind(image)=='magenta':
        mask &= (np.minimum(a[:,:,0],a[:,:,2])-a[:,:,1]<80) | (np.minimum(a[:,:,0],a[:,:,2])<150)
    return mask


def main():
    data=json.loads((OUT/'catalog.original.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets={a['id']:a for a in data['assets'].values()}
    stage=read(OUT/'stage_manifest.json');repairs=read(OUT/'repair_queue.json')
    targets=set(stage['records'])|set(repairs)
    queue=queue_module.Queue();attempts={a['id']:a for a in queue.state['attempts']}
    results={};sheets={}
    retained={r['target_id']:r for r in read(HERE.parent/'review/second_pass/replacement_audit.json')['targets']}
    for target in sorted(targets):
        asset=assets[target];record=stage['records'].get(target,repairs.get(target))
        selected=next((o for o in asset['preparedAlternatives'] if o['sha256']==record['reviewed_sha256']),{})
        aid=selected.get('attempt') or queue.state['cells'].get(target,{}).get('attempt')
        if not aid:
            aids=[aid for cell in retained.get(target,{}).get('cells',[]) for aid in cell.get('retained_attempts',[])]
            aid=next((aid for aid in aids if aid in attempts),None)
        info={'target':target,'name':asset['name'],'size':asset['size'],'native':asset['native'],
              'reviewed_path':record['reviewed_path'],'attempt':aid,'known_extraction_rect':bool(selected.get('rawRect'))}
        attempt=attempts.get(aid)
        if aid and aid.startswith('dense:'):
            _,bundle,sheet=aid.split(':');folder=HERE.parent/'chat_bundles/dense64_20260916'/bundle
            manifest=read(folder/'manifest.json');sh=next(s for s in manifest['sheets'] if s['id']==sheet)
            layout=read(folder/sh['layout']);receipt=read(folder/'outputs/progress.json')['sheets'][sheet]
            raw=str(folder/receipt['raw_path']);reference_size=layout['reference_size']
            rectangles={c['id']:c['reference_rect'] for c in layout['cells']}
        elif attempt:
            payload=read(attempt['payload']);raw=attempt['raw']
            try: reference_size,rectangles,_=reference_geometry(payload,queue)
            except (KeyError,FileNotFoundError): reference_size,rectangles=None,{}
        else: raw=selected.get('raw');raw=str((HERE/unquote(raw)).resolve()) if raw else None;reference_size,rectangles=None,{}
        if raw and Path(raw).exists():
            if raw not in sheets:
                with Image.open(raw) as im:
                    im=im.convert('RGBA');mask=foreground(im);labels,n=ndimage.label(mask)
                    boxes=[]
                    for lab,sl in enumerate(ndimage.find_objects(labels),1):
                        if sl is None:continue
                        area=int((labels[sl]==lab).sum())
                        if area<100:continue
                        yy,xx=sl;boxes.append({'box':[xx.start,yy.start,xx.stop,yy.stop],'area':area,'label':lab})
                    sheets[raw]={'size':list(im.size),'kind':sheet_kind(im),'components':boxes,
                                 'reference_size':reference_size,'rectangles':rectangles}
            sh=sheets[raw];info['raw']=raw
            info['raw_rect']=selected.get('rawRect') or (crop_rect(rectangles[target],reference_size,sh['size']) if target in rectangles else None)
        with Image.open(HERE/unquote(asset['native'])) as native, Image.open(HERE/unquote(record['reviewed_path'])) as candidate:
            na=np.array(native.convert('RGBA'))[:,:,3]>64;ca=np.array(candidate.convert('RGBA'))[:,:,3]>64
            info['native_bounds']=native.convert('RGBA').getbbox();info['candidate_bounds']=candidate.convert('RGBA').getbbox()
            info['edges']={k:[int(x.sum()),int(y.sum())] for k,x,y in [('left',na[:,0],ca[:,0]),('right',na[:,-1],ca[:,-1]),('top',na[0],ca[0]),('bottom',na[-1],ca[-1])]}
        results[target]=info
    (OUT/'source_audit.json').write_text(json.dumps({'assets':results,'sheets':sheets},indent=2)+'\n')
    # Every reviewed asset is visible in these diagnostic sheets, not just flagged ones.
    (OUT/'audit_contacts').mkdir(exist_ok=True)
    for start in range(0,len(results),30):
        sheet=Image.new('RGB',(1500,1350),(40,46,46));draw=ImageDraw.Draw(sheet)
        for index,(target,info) in enumerate(list(results.items())[start:start+30]):
            x,y=index%6*250,index//6*270
            decision=stage['records'].get(target,{}).get('decision',{}).get('decision','auto')
            draw.text((x+3,y+3),info['name']+' '+decision,fill='white')
            cats=repairs.get(target,{}).get('categories',[]);draw.text((x+3,y+17),','.join(cats)[:38],fill=(255,190,130))
            for col,url in enumerate([info['native'],info['reviewed_path']]):
                with Image.open(HERE/unquote(url)) as im:
                    im=im.convert('RGBA');im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST) if col==0 else im;im.thumbnail((118,224));sheet.paste(im,(x+col*124+3,y+40),im)
        sheet.save(OUT/'audit_contacts'/f'{start//30+1:02}.jpg',quality=90)
    print('assets',len(results),'raw sheets',len(sheets))

if __name__=='__main__':main()
