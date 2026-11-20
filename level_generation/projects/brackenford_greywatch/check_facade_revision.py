"""Quick native/semantic check for the outdoor facade revision; no gameplay scenarios."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import time

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file

parser=argparse.ArgumentParser()
parser.add_argument('--review-directory',default='facade_revision')
args=parser.parse_args()
start=time.monotonic()
path=PROJECT/'runtime/worlds/mm8/maps/lg01.odm'
native=parse_odm_file(path)['payload']
semantic=json.loads((PROJECT/'source/lg01.semantic.json').read_text())
before=json.loads((PROJECT/'review/facade_revision/before/lg01.semantic.json').read_text())
town=json.loads((PROJECT/'source/town_registry.json').read_text())
assert {(e['id'],e['name']) for e in before['events']} <= {
    (e['id'],e['name']) for e in semantic['events']}
doors=[]
for house in semantic['buildings']:
    model=next(m for m in semantic['bmodels'] if m['id']==house['id']+'_door')
    part=native['bmodels'][model['index']];face=part['faces'][0]
    points=[part['vertices'][i] for i in face['vertex_indices']]
    dimensions=[max(p[k] for p in points)-min(p[k] for p in points) for k in 'xyz']
    assert abs(math.hypot(*dimensions[:2])-128)<=1 and dimensions[2]==256
    assert face['texture_name'].lower()==house['door_texture'].lower()
    assert face['cog_triggered_number']==house['event_id']
    entry=next(e for e in town['houses'] if e['building']==house['id'])
    assert entry['event_id']==house['event_id'] and entry['door_position']==house['door_position']
    assert entry['house_id']==12000+semantic['buildings'].index(house)
    doors.append(dict(building=house['id'],event=house['event_id'],house=entry['house_id'],
                      dimensions=[128,256],texture=face['texture_name']))
    body=native['bmodels'][next(m['index'] for m in semantic['bmodels'] if m['id']==house['id'])]
    assert not {'bdoorb','cr_w128b'} & {f['texture_name'].lower() for f in body['faces']}
terrain=json.loads((PROJECT/'source/lg01.terrain.yml').read_text())
assert bytes(native['height_map'])==bytes.fromhex(terrain['height_map_hex'])
assert bytes(native['tile_map'])==bytes.fromhex(terrain['tile_map_hex'])
keys={p.stem.lower() for folder in ['assets_dev/worlds/mm8/textures','assets_dev/engine/textures']
      for p in (ROOT/folder).glob('*.bmp')}
assert all(f['texture_name'].lower() in keys for m in native['bmodels'] for f in m['faces'])
well=next(p for p in semantic['content_landmarks'] if p['id']=='town_well')
wx,wy=well['position'][:2]
roads={((c-64)*512+256,(64-r)*512-256) for road in semantic['roads'] for r,c in road['cells']}
assert not any(abs(wx-x)<512 and abs(wy-y)<512 for x,y in roads)
assert [a['id'] for a in semantic['arrivals']]==[a['id'] for a in before['arrivals']]
decorations=json.loads((PROJECT/'source/lg01.decorations.json').read_text())
assert len(native['entities'])==1+len(decorations['entities'])
for house in semantic['buildings']:
    x,y=house['xy'];w,d=house['local_footprint']
    t=math.radians(house['rotation_degrees']);co,si=math.cos(t),math.sin(t)
    def inside(px,py,margin):
        dx,dy=px-x,py-y
        return abs(co*dx+si*dy)<w/2+margin and abs(-si*dx+co*dy)<d/2+margin
    # Dirt margins are not the road-center walking corridor; rotated houses use their local footprint.
    assert not any(inside(rx,ry,96) for rx,ry in roads), house['id']
    for actor in semantic['fixed_actors'][:29]:
        assert not inside(*actor['position'][:2],80), (house['id'],actor['id'])
# Check new authored prop footprints and native stat-barrel identities when present.
barrels=[d for d in decorations['records'] if d.get('role')=='permanent stat barrel']
if 'stat_barrels' in json.loads((PROJECT/'outdoor_plan.json').read_text()):
    anchors=json.loads((PROJECT/'outdoor_plan.json').read_text())['stat_barrels']
    assert len(barrels)==len(anchors)==4
    for barrel,anchor in zip(barrels,anchors):
        assert barrel['name']=='dec03' and barrel['position'][:2]==anchor['xy']
        entity=native['entities'][barrel['index']]
        assert entity['name']=='dec03' and entity['event_id_primary']==0
        # Runtime resolves descriptor by name; native reference IDs are not merged TXT row numbers.
        assert entity['decoration_list_id']==barrel['id']
for prop in semantic['content_landmarks']:
    if prop['kind'] not in ['well','fountain']:continue
    extent=400 if prop['kind']=='fountain' else 128
    assert not any(abs(prop['position'][0]-x)<extent+384 and abs(prop['position'][1]-y)<extent+384
                   for x,y in roads),prop['id']
    if prop['event_id'] in [303,304]:
        model=native['bmodels'][prop['bmodel_index']]
        assert all(f['cog_triggered_number']==prop['event_id'] for f in model['faces'])
result=dict(status='pass',scope='Native data/IDs/clearance only; no behavioral scenario suite',
    doors=doors,bmodels=len(native['bmodels']),faces=sum(len(m['faces']) for m in native['bmodels']),
    native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    indoor_sha256=hashlib.sha256((path.parent/'lg02.blv').read_bytes()).hexdigest(),
    native_terrain_exact=True,texture_keys_resolve=True,stable_event_identities=True,stat_barrels=len(barrels),
    well_position=well['position'],well_road_clearance_units=128,decoration_count=len(decorations['entities']),
    elapsed_seconds=round(time.monotonic()-start,3))
(PROJECT/'review'/args.review_directory/'quick_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='doors'}))
