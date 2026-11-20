"""Inspect written native tiles through actual donor bitmaps and independent corner colours."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--version',default='terrain_v2')
parser.add_argument('--source',action='store_true',help='Inspect authored tile arrays before compiling; no native claim.')
args=parser.parse_args()
OUT=PROJECT/'review'/args.version
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    path=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    if args.source:
        path=PROJECT/'implementation/source/mm5_sw.terrain.yml'
        source=json.loads(path.read_text())
        native={'tile_map':list(bytes.fromhex(source['tile_map_hex']))}
    else:
        native=parse_odm_file(path)['payload']
    tiles=np.array(native['tile_map']).reshape(128,128)
    rows=list(csv.DictReader((PROJECT/'implementation/terrain_rows.tsv').open(),delimiter='\t'))
    names={90+i:row['texture_name'] for i,row in enumerate(rows)}
    paths={p.stem.lower():p for world in ['mm7','mm8']
           for p in (ROOT/'assets_dev/worlds'/world/'textures').iterdir() if p.is_file()}
    paths['mm5void']=PROJECT/'implementation/runtime/worlds/mm5/textures/mm5void.png'
    paths.update({p.stem.lower():p for p in (PROJECT/'implementation/runtime/worlds/mm5/textures').iterdir()
                  if p.is_file()})
    images={name:Image.open(paths[name]).convert('RGB') for name in {names[int(raw)] for raw in tiles.flat}}
    colors={}
    for name,im in images.items():
        if name=='dirttyl' or name.startswith('drsr'):
            result=['dirt']*4
        elif name in ('wtrtyl','mm5acid'):
            result=['acid' if name=='mm5acid' else 'water']*4
        elif name=='7sand':
            result=['sand']*4
        elif name.startswith('mm5sd'):
            a=np.array(im,float);result=[]
            for x,y in [(0,0),(120,0),(0,120),(120,120)]:
                red,green,blue=a[y:y+8,x:x+8].mean((0,1))
                result.append('dirt' if red-green>20 and green<80 else 'sand')
        elif name.startswith(('gr','wtrdr','rc','vol','mm5ac')):
            a=np.array(im.resize((128,128)),float);result=[]
            for x,y in [(0,0),(120,0),(0,120),(120,120)]:
                red,green,blue=a[y:y+8,x:x+8].mean((0,1))
                if name.startswith('gr'):
                    kind='grass' if green>red else 'dirt'
                elif name.startswith(('wtrdr','mm5ac')):
                    liquid='acid' if name.startswith('mm5ac') else 'water'
                    kind=liquid if red>180 and blue>180 else 'dirt'
                elif name.startswith('vol'):
                    kind='scorch' if red-green<8 else 'dirt'
                else:
                    kind='rock' if red>85 else 'dirt'
                result.append(kind)
        else:
            result=None
        colors[name]=result
    errors=[];excluded=[]
    for r in range(127):
        for c in range(127):
            a_name=names[int(tiles[r,c])];a=colors[a_name]
            for dr,dc,aa,bb,side in [(0,1,[1,3],[0,2],'east'),(1,0,[2,3],[0,1],'south')]:
                if r+dr>=127 or c+dc>=127:
                    continue
                b_name=names[int(tiles[r+dr,c+dc])];b=colors[b_name]
                record={'cell':[r,c],'edge':side,'textures':[a_name,b_name]}
                if a is None or b is None:
                    excluded.append(record)
                elif [a[i] for i in aa]!=[b[i] for i in bb]:
                    errors.append(record)
    # Preview the written material assignment. The shore overlay is composited
    # over one water frame, rather than displaying its magenta transparency key.
    rendered={}
    for name,im in images.items():
        if name.startswith('wtrdr') or (name.startswith('mm5ac') and name!='mm5acid'):
            a=np.array(im);mask=(a[:,:,0]>200)&(a[:,:,1]<80)&(a[:,:,2]>200)
            base='mm5acid' if name.startswith('mm5ac') else 'wtrtyl'
            a[mask]=np.array(images[base].resize(im.size))[mask]
            im=Image.fromarray(a)
        rendered[name]=im.resize((64,64))
    spec=json.loads((PROJECT/'implementation/architecture.json').read_text())
    for label,box in [('town',(46,81,44,72)),('travel',(16,112,16,112)),('full',(0,127,0,127)),
                      ('acid',(10,31,50,78)),('scorch',(0,6,64,76))]:
        r0,r1,c0,c1=box
        size=64 if label in ('town','acid','scorch') else 16
        canvas=Image.new('RGB',((c1-c0)*size,(r1-r0)*size))
        for r in range(r0,r1):
            for c in range(c0,c1):
                canvas.paste(rendered[names[int(tiles[r,c])]].resize((size,size)),((c-c0)*size,(r-r0)*size))
        if label=='town':
            draw=ImageDraw.Draw(canvas)
            def screen(x,y):
                return ((x/512+64-c0)*size,(64-y/512-r0)*size)
            for b in spec['buildings']:
                ox,oy=b['frontOrigin'];tx,ty=b['frontTangent'];nx,ny=b['frontOutward'];w,d=b['localFootprint']
                points=[screen(ox+tx*x-nx*y,oy+ty*x-ny*y) for x,y in [(-w/2,0),(w/2,0),(w/2,d),(-w/2,d)]]
                draw.polygon(points,fill='#aaa396',outline='white',width=2)
                draw.text(screen(*b['center']),b['id'],fill='black')
                for venue in b['venues']:
                    x,y=venue['door']
                    draw.line([screen(x,y),screen(x+nx*256,y+ny*256)],fill='cyan',width=3)
        canvas.save(OUT/(label+'.png'))
    report={'sourceSha256' if args.source else 'nativeSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'inputKind':'authored terrain metadata' if args.source else 'written native ODM',
            'method':'Classify actual bitmap corner colours independently from the generator variant dictionary.',
            'bitmapCorners':colors,'supportedEdgeMismatches':errors,'excludedEdges':excluded,
            'limits':'Void edges use separately reviewed geometry. This is a tile-art check, not regional visual acceptance.'}
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'supportedEdgeMismatches':len(errors),'excludedEdges':len(excluded)}))
    assert not errors,errors[:10]


if __name__=='__main__':
    main()
