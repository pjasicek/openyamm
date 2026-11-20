"""Quick native exit continuity and terrain-screening checks; no travel scenario matrix."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OUT=P/'review/transition_revision'
sys.path.insert(0,str(ROOT/'util'));from map_export import parse_odm_file
from build_outdoor_content import terrain_height
parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');args=parser.parse_args()
plan=json.loads((P/'outdoor_plan.json').read_text());s=json.loads((P/'source/lg01.semantic.json').read_text())
before=json.loads((OUT/'before/lg01.semantic.json').read_text());t=json.loads((P/'source/lg01.terrain.yml').read_text())
h=list(bytes.fromhex(t['height_map_hex']));tiles=list(bytes.fromhex(t['tile_map_hex']))
old=list(bytes.fromhex(json.loads((OUT/'before/lg01.terrain.yml').read_text())['height_map_hex']))
assert s['buildings']==before['buildings'] and s['arrivals']==before['arrivals'] and s['fixed_actors']==before['fixed_actors']
assert json.loads((P/'source/lg01.decorations.json').read_text())['entities']==json.loads((OUT/'before/lg01.decorations.json').read_text())['entities']
for r in range(128):
    for c in range(128):
        if abs((c-64)*512)<=24576 and abs((64-r)*512)<=24576:assert h[r*128+c]==old[r*128+c]
nativepath=P/'runtime/worlds/mm8/maps/lg01.odm'
if not args.source:
    native=parse_odm_file(nativepath)['payload'];assert native['height_map']==h and native['tile_map']==tiles
    previous=parse_odm_file(OUT/'before/lg01.odm')['payload'];assert native['bmodels']==previous['bmodels']
    assert native['entities']==previous['entities']
records=[]
for route in plan['regional_exit_scenery']:
    path=next(p['cells'] for p in s['roads'] if p['id']==route['id']+'_scenic_continuation')
    assert all(198<=tiles[r*128+c]<234 for r,c in path)
    assert all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:]))
    r,c=path[-1];assert (r==0 and tiles[r*128+c]==199) if route['id']=='north' else (c==0 and tiles[r*128+c]==200)
    points=[((c-64)*512+256,(64-r)*512-256) for r,c in path]
    zz=[terrain_height(x,y,h) for x,y in points]
    grade=max(abs(a-b)/512 for a,b in zip(zz,zz[1:]));assert grade<=.5,grade
    # Ground-level sightline toward the final road cell: not a claim about flying or every camera angle.
    origin=(-24575,points[0][1]) if route['id']=='west' else (points[0][0],24575)
    target=points[-1];start_z=terrain_height(*origin,h)+176;end_z=terrain_height(*target,h)+16
    obstructed=[]
    for f in np.linspace(.01,.99,99):
        x=origin[0]+f*(target[0]-origin[0]);y=origin[1]+f*(target[1]-origin[1])
        if terrain_height(x,y,h)>start_z+f*(end_z-start_z):obstructed.append([round(x),round(y)])
    assert obstructed,'The walking-eye ray exposes the far road ending'
    records.append(dict(exit=route['id'],destination=route['destination'],trigger=route['trigger'],road_cells=len(path),
        edge_cell=path[-1],edge_tile=tiles[r*128+c],max_centerline_grade=grade,
        origin=list(origin),foot_z=terrain_height(*origin,h),target=list(target),eye_height=176,
        first_terrain_occlusion=obstructed[0],screened_far_road=True))
report=dict(status='pass',mode='source' if args.source else 'native',native_sha256=None if args.source else hashlib.sha256(nativepath.read_bytes()).hexdigest(),
    exits=records,inside_travel_bounds_heights_unchanged=True,buildings_arrivals_actors_decorations_unchanged=True,
    limitations='Continuity, native identities and sampled terrain sightline only; not full traversal, all camera angles or flight occlusion.')
(OUT/('source_check.json' if args.source else 'transition_check.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
