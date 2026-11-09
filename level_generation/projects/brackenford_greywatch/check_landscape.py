"""Fast landscape readback: full bridge footprint, ground variants and native decoration identities."""
from pathlib import Path
import argparse,json,sys,math,hashlib
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OUT=P/'review/landscape_revision'
sys.path.insert(0,str(ROOT/'util'));from map_export import parse_odm_file
from build_outdoor_content import terrain_height
parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');args=parser.parse_args()
s=json.loads((P/'source/lg01.semantic.json').read_text());before=json.loads((OUT/'before/lg01.semantic.json').read_text())
t=json.loads((P/'source/lg01.terrain.yml').read_text());h=list(bytes.fromhex(t['height_map_hex']));tiles=list(bytes.fromhex(t['tile_map_hex']))
assert s['buildings']==before['buildings'] and s['arrivals']==before['arrivals']
assert s['fixed_actors']==before['fixed_actors'], 'Population positions changed'
z=s['terrain']['bridge_deck_z'];xs=np.arange(3072,7681,64)
max_ground=max(terrain_height(x,y,h) for x in xs for y in np.arange(-256,769,64))
assert z-max_ground>=64,('buried bridge',z,max_ground)
# Walking corridor must meet the bridge gently, on both banks, not a vertical wall beyond the deck.
profiles=[]
for a,b in [((0,256),(3072,256)),((7680,256),(10240,256)),((10240,256),(12544,3840))]:
    distance=math.dist(a,b);n=math.ceil(distance/64)
    points=[(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
    zz=[max(terrain_height(x,y,h),z) if 2560<=x<=8192 else terrain_height(x,y,h) for x,y in points]
    grade=max(abs(zz[i+1]-zz[i])/(distance/n) for i in range(n))
    assert grade<=.5,('bridge approach grade',a,b,grade)
    profiles.append(dict(from_xy=a,to_xy=b,max_grade=round(grade,3)))
counts=Counter(tiles);assert counts[2]>0 and counts[4]>0 and counts[92]>0
nativepath=P/'runtime/worlds/mm8/maps/lg01.odm';native=None
if not args.source:
    native=parse_odm_file(nativepath)['payload'];assert native['height_map']==h and native['tile_map']==tiles
    bridge=native['bmodels'][next(m['index'] for m in s['bmodels'] if m['id']=='bridge_deck')]
    assert bridge['faces'][0]['polygon_type']==5 and bridge['faces'][1]['polygon_type']==3
    assert {v['z'] for v in bridge['vertices']}=={z-64,z}
    # Stone landings must meet the timber edge without coplanar overlapping tops.
    for m in s['bmodels']:
        if not m['id'].startswith('bridge_pier_'):continue
        component=native['bmodels'][m['index']]
        for face in component['faces']:
            vertices=[component['vertices'][i] for i in face['vertex_indices'][:face['vertex_count']]]
            if vertices and all(v['z']==z for v in vertices):
                assert max(v['x'] for v in vertices)<=3072 or min(v['x'] for v in vertices)>=7680, 'Overlapping bridge tops'
d=json.loads((P/'source/lg01.decorations.json').read_text());anchors={a['id']:a for a in d['native_landmarks']}
landmarks=[]
for a in d['records']:
    if a['semantic_id'] not in anchors:continue
    anchor=anchors[a['semantic_id']];assert a['name']==anchor['name'] and a['event']==0
    x,y,zz=a['position'];assert zz==terrain_height(x,y,h)
    if native:
        entity=native['entities'][a['index']]
        assert entity['name']==a['name'] and entity['decoration_list_id']==a['id']
        assert entity['event_id_secondary']==0 and entity['event_id_primary']==0
    landmarks.append(dict(id=a['semantic_id'],name=a['name'],entity_index=a['index'],position=a['position'],
        binding='native interactive-decoration family; shared Global.lua',light_radius=a['light_radius']))
assert len(landmarks)==6
old_h=list(bytes.fromhex(json.loads((OUT/'before/lg01.terrain.yml').read_text())['height_map_hex']))
fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
for ax,hh,deck,label in [(axes[0],old_h,640,'Before'),(axes[1],h,z,'After')]:
    xx=np.arange(2048,9217,64)
    for y,color in [(-256,'#228844'),(256,'#665599'),(768,'#bb6633')]:
        ax.plot(xx,[terrain_height(x,y,hh) for x in xx],label=f'terrain Y={y}',color=color)
    ax.plot([3072,7680],[deck,deck],lw=4,color='black',label='deck surface')
    ax.set(title=label,ylabel='native elevation',ylim=(0,2000));ax.grid(alpha=.25);ax.legend(loc='upper left')
axes[1].set_xlabel('native X along crossing');fig.tight_layout();fig.savefig(OUT/'bridge_profiles.png',dpi=140);plt.close(fig)
report=dict(status='pass',mode='source' if args.source else 'native',native_sha256=hashlib.sha256(nativepath.read_bytes()).hexdigest() if native else None,
    bridge_deck_z=z,maximum_terrain_under_deck=max_ground,minimum_ground_clearance=z-max_ground,approach_profiles=profiles,
    ground_detail_tiles={str(i):counts[i] for i in [2,4,92]},native_scenery_counts=d['counts'],native_landmarks=landmarks,
    accepted_buildings_arrivals_population_unchanged=True,limitations='Static binding and geometric review, not new script behavior or balance tests.')
(OUT/('source_check.json' if args.source else 'landscape_check.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
