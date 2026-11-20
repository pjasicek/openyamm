"""Locate complete raw-sheet subjects; retain measurements for all staged approvals."""
import json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from inspect_sources import OUT,HERE,foreground,read


def ordered_cells(rects):
    # Dense sheets center differently sized sprites in a row; y origins are not row ids.
    rows=[]
    for key,rect in sorted(rects.items(),key=lambda entry:entry[1][1]):
        y,end=rect[1],rect[1]+rect[3]
        row=next((r for r in rows if y<r['bottom'] and end>r['top']),None)
        if row is None:
            rows.append({'top':y,'bottom':end,'cells':[(key,rect)]})
        else:
            row['top']=max(row['top'],y);row['bottom']=min(row['bottom'],end);row['cells'].append((key,rect))
    return [sorted(row['cells'],key=lambda c:c[1][0]) for row in rows]


def main():
    source=read(OUT/'source_audit.json');maps={};counts=Counter()
    data=json.loads((OUT/'catalog.original.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    hashes={a['id']:a['sourceHash'] for a in data['assets'].values()}
    for path,sheet in source['sheets'].items():
        rows=ordered_cells(sheet['rectangles']);n=sum(map(len,rows));components=sheet['components']
        large=sorted(components,key=lambda c:-c['area'])
        # Only discard components if their area is clearly incidental compared with every retained subject.
        if n and len(large)>=n and (len(large)==n or large[n-1]['area']>large[n]['area']*8):
            todo=sorted(large[:n],key=lambda c:c['box'][1]);mapping={};index=0
            for row in rows:
                pieces=sorted(todo[index:index+len(row)],key=lambda c:c['box'][0]);index+=len(row)
                for (key,rect),piece in zip(row,pieces):mapping[key]=piece
            maps[path]=mapping;counts['sheets_complete_component_map']+=1
        else:counts['sheets_requiring_local_inspection']+=1
    audit={}
    for target,asset in source['assets'].items():
        raw=asset.get('raw');mapping=maps.get(raw,{})
        piece=mapping.get(target)
        if not piece:
            alias=next((key for key in mapping if hashes.get(key)==hashes.get(target)),None)
            piece=mapping.get(alias)
            if piece:maps[raw][target]=piece
        if not piece or not asset.get('raw_rect'):
            audit[target]={'status':'no_complete_component_mapping','edges':asset['edges']};continue
        x0,y0,x1,y1=piece['box'];a,b,c,d=asset['raw_rect'];area=(x1-x0)*(y1-y0)
        lost=1-max(0,min(x1,c)-max(x0,a))*max(0,min(y1,d)-max(y0,b))/max(area,1)
        overlaps=[]
        for other,p in mapping.items():
            if other==target or p['label']==piece['label']:continue
            xx,yy,XX,YY=p['box'];overlap=max(0,min(XX,c)-max(xx,a))*max(0,min(YY,d)-max(yy,b))
            if overlap>area*.025:overlaps.append(other)
        border=x0==0 or y0==0 or x1>=source['sheets'][raw]['size'][0] or y1>=source['sheets'][raw]['size'][1]
        audit[target]={'status':'crop_repair' if lost>.015 or overlaps else 'crop_matches_subject',
            'raw':raw,'component':piece,'old_crop':asset['raw_rect'],'lost_bbox_fraction':round(lost,5),
            'neighbor_overlap':overlaps,'raw_canvas_clipped':border,'edges':asset['edges']}
    (OUT/'crop_audit.json').write_text(json.dumps({'summary':dict(counts),'sheets':maps,'targets':audit},indent=2)+'\n')
    print(dict(counts));print(dict(Counter(x['status'] for x in audit.values())))
    stage=read(OUT/'stage_manifest.json')
    print('approved crop suspects',sum(v['status']=='crop_repair' and stage['records'].get(k,{}).get('decision',{}).get('decision')=='approve' for k,v in audit.items()))

if __name__=='__main__':main()
