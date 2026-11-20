"""Check Crownspire's revised placement, native floor materials, collision binding and stage."""
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

import yaml
from layout import PROJECT as P, ROOT, ROOMS

sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file

report=json.loads((P/'d12_build.json').read_text())
semantic=json.loads((P/'source/hes_d12.semantic.json').read_text())
metadata=json.loads((P/'source/hes_d12.geometry.yml').read_text())
native=parse_blv_file(P/'runtime/hes_d12.blv')['payload']
scene=json.loads((P/'runtime/hes_d12.scene.yml').read_text())
actors=scene['initial_state']['actors']
assert len(actors)==123 and len(report['placements'])==121
# The three Hierarch forms share their intended position and never appear together.
placed=actors[:121]
for index,cell in enumerate(sorted(semantic['sectors']),1):
    x0,y0,x1,y1,z0,z1=semantic['room_bounds'][cell.removeprefix('room_')]
    centres=[]
    for face in native['faces']:
        if face['room_number']!=index or face['is_portal']:continue
        vs=[native['vertices'][i] for i in face['vertex_indices']]
        centres.append(tuple(sum(v[k] for v in vs)/len(vs) for k in 'xyz'))
    assert any(x0<=x<=x1 and y0<=y<=y1 and z0<=z<=z1 for x,y,z in centres),cell
distances=[math.hypot(a['position']['x']-b['position']['x'],a['position']['y']-b['position']['y'])
           for i,a in enumerate(placed) for b in placed[i+1:]
           if abs(a['position']['z']-b['position']['z'])<300]
assert min(distances)>=400

# A densest 300-radius circle can be moved until it touches two actors.
points=[tuple(a['position'][k] for k in 'xyz') for a in placed]
centres=list(points)
for i,(x,y,z) in enumerate(points):
    for u,v,w in points[i+1:]:
        d=math.hypot(u-x,v-y)
        if not 0<d<=600 or abs(z-w)>=300:continue
        h=math.sqrt(300**2-(d/2)**2)
        for sign in (-1,1):centres.append(((x+u)/2+sign*h*(v-y)/d,(y+v)/2-sign*h*(u-x)/d,(z+w)/2))
crowding=max(sum(math.hypot(x-u,y-v)<=300.001 and abs(z-w)<300 for u,v,w in points) for x,y,z in centres)
assert crowding<=4,crowding

for entry,a in zip(report['placements'],placed):
    r=ROOMS[entry['room']];x,y,z=entry['position'];radius=a['radius']
    points=semantic['room_footprints'][entry['room']]
    assert min(p[0]for p in points)+radius<x<max(p[0]for p in points)-radius
    assert min(p[1]for p in points)+radius<y<max(p[1]for p in points)-radius
    cell=sorted(semantic['sectors'])[a['sector_id']-1].removeprefix('room_')
    assert cell in semantic['room_cells'][entry['room']],(a['actor_index'],cell)
    for rid,x0,y0,z0,x1,y1,z1 in semantic['obstacles']:
        assert not (rid==entry['room'] and z<z1-1 and x0-radius<x<x1+radius and y0-radius<y<y1+radius)

floors=collections.defaultdict(collections.Counter)
for face in native['faces']:
    vs=[native['vertices'][i] for i in face['vertex_indices']]
    if face['facet_type']==3 and len({v['z'] for v in vs})==1:
        floors[vs[0]['z']][face['texture_name']]+=1
assert floors[-1536]['hcfloor']>0 and floors[-1536]['hpfloor']==0,dict(floors[-1536])
assert floors[0]['hpfloor'] and floors[704]['hpring'] and floors[2304]['hpfloor']
assert not report['checks']['ceiling_problems'] and not report['checks']['stacking_problems']
assert report['checks']['max_lights']<=4 and len(native['lights'])==5
assert len(native['entities'])==74+len(semantic['pickups'])

stage=ROOT/'output/hesper_stage/assets_editor_dev'
rows=[line.split('\t') for line in (stage/'worlds/hesper/data_tables/decoration_data.txt').read_text().splitlines()]
head=next(row for row in rows if len(row)>5 and row[1]=='hes_founder_head')
assert (int(head[4]),int(head[5]))==(52,67),head
entity=next(e for e in metadata['entities'] if e['id'].startswith('hes_founder_head_'))
assert entity['decoration_list_id']+1==int(head[0]) and entity['event_id_secondary']==73

tour=yaml.safe_load((P/'review_tour_01.yml').read_text())
assert tour['output_dir'].endswith('/review/build02') and len(tour['shots'])==13
clearances={}
for shot in tour['shots']:
    x,y,z=shot['position']
    gap=min(math.hypot(x-a['position']['x'],y-a['position']['y'])-a['radius']
            for a in placed if abs(z-a['position']['z'])<300)
    assert gap>=250,(shot['name'],gap)
    clearances[shot['name']]=round(gap,1)
assert report['exits']['shaft']==dict(map='hes_d13.blv',key='shaft_bottom',ready=True,x=400,y=1000,z=0,direction=0)
for rel,expected in json.loads((P/'review/fixes/preserved_sha256.json').read_text()).items():
    if '/hesper_d13/' in rel: continue  # Brightness B explicitly re-authors D13 too.
    assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,rel
hashes={}
for f in (P/'runtime/worlds/hesper').rglob('*'):
    if f.is_file():
        rel=f.relative_to(P/'runtime');assert f.read_bytes()==(stage/rel).read_bytes(),str(rel)
        hashes[str(rel)]=hashlib.sha256(f.read_bytes()).hexdigest()
result={'minimum_actor_spacing':min(distances),'max_actors_in_300_radius':crowding,
        'native_floor_faces':dict(floors),'camera_body_clearance':clearances,'head_collision_radius':52,
        'shaft':report['exits']['shaft'],'preserved_review_sheet':True,'staged_sha256':hashes}
(P/'review/fixes/static_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: pack density/free floor, native floor materials/sectors, trophy collision binding, tour clearance, D13 link and stage')
