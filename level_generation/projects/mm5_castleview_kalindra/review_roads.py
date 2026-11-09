"""Check actual native road bitmaps against the route graph, including painted diagonal joins."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest == build['nativeSha256']
    tiles = parse_odm_file(native)['payload']['tile_map']
    plan = json.loads((PROJECT/'implementation/roads.json').read_text())
    road_cells = {tuple(c) for c in plan['cells']}
    edges = {frozenset([tuple(a),tuple(b)]) for path in plan['paths']
             for a,b in zip(path['cells'],path['cells'][1:]) if a!=b}
    rows = list(csv.DictReader((PROJECT/'implementation/terrain_rows.tsv').open(),delimiter='\t'))
    names = {90+i:r['texture_name'] for i,r in enumerate(rows)}
    files = {p.stem.lower():p for p in (ROOT/'assets_dev/worlds/mm8/textures').iterdir() if p.is_file()}
    artwork = {}
    for name in {names[tiles[r*128+c]] for r,c in road_cells}:
        pixels = np.array(Image.open(files[name]).convert('RGB'),dtype=float)
        # The painted stones are neutral grey; their dirt ground is strongly red/brown.
        stone = ((abs(pixels[:,:,0]-pixels[:,:,1])<22)
                 & (pixels[:,:,2]>pixels[:,:,0]*.68) & (pixels[:,:,2]>35))
        profiles = [e.mean(axis=0 if i%2==0 else 1) for i,e in enumerate(
            [stone[:3,:],stone[:,-3:],stone[-3:,:],stone[:,:3]])]
        present = [bool(e.mean()>.1) for e in profiles]
        artwork[name] = {'portsNESW':sum(1<<i for i,on in enumerate(present) if on),
                         'stoneEdgeFractions':[float(e.mean()) for e in profiles],
                         'profiles':profiles,'sha256':hashlib.sha256(files[name].read_bytes()).hexdigest()}
    checked = []
    directions = [(-1,0),(0,1),(1,0),(0,-1)]
    for r,c in sorted(road_cells):
        name = names[tiles[r*128+c]]
        expected = sum(1<<i for i,(dr,dc) in enumerate(directions)
                       if frozenset([(r,c),(r+dr,c+dc)]) in edges)
        if c==126:
            expected |= 2
        assert artwork[name]['portsNESW']==expected,(r,c,name,expected,artwork[name]['portsNESW'])
        for i in [1,2]:
            dr,dc = directions[i]
            other = (r+dr,c+dc)
            if frozenset([(r,c),other]) not in edges:
                continue
            next_name = names[tiles[other[0]*128+other[1]]]
            a,b = artwork[name]['profiles'][i],artwork[next_name]['profiles'][(i+2)%4]
            overlap = float(np.minimum(a,b).sum()/min(a.sum(),b.sum()))
            assert overlap>.45,(r,c,name,next_name,overlap)
            checked.append({'cell':[r,c],'edge':i,'textures':[name,next_name],'stoneProfileOverlap':overlap})
    result = {'nativeSha256':digest,'roadCells':len(road_cells),'graphEdges':len(edges),'paintedJoins':checked,
              'artwork':{n:{k:v for k,v in a.items() if k!='profiles'} for n,a in artwork.items()},
              'limits':'Painted stone ports and shared-edge coverage are measured independently from tile selection. '
                       'Native player-height appearance and final frontage composition require visual review.'}
    (PROJECT/'review/native/roads.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'roadCells':len(road_cells),'paintedJoins':len(checked)})


if __name__=='__main__':
    review()
