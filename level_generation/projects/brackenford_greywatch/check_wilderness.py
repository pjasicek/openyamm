"""Quick written-map checks for wilderness placement; no gameplay scenario matrix."""
from pathlib import Path
import hashlib
import json
import math
import sys
import time
import numpy as np
from scipy.spatial import cKDTree

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
from build_outdoor_content import terrain_height
start=time.monotonic()
source=PROJECT/'source';out=PROJECT/'review/wilderness_revision'
path=PROJECT/'runtime/worlds/mm8/maps/lg01.odm'
native=parse_odm_file(path)['payload']
semantic=json.loads((source/'lg01.semantic.json').read_text())
before=json.loads((out/'before/lg01.semantic.json').read_text())
scene=json.loads((source/'lg01.scene.yml').read_text())
assert semantic['buildings']==before['buildings'], 'Accepted town buildings changed'
assert semantic['arrivals']==before['arrivals'], 'Arrival anchors changed'
assert semantic['fixed_actors'][:29]==before['fixed_actors'][:29], 'Town population placement changed'
assert not scene['spawns'], 'Do not duplicate fixed population with random spawns'
assert len(scene['initial_state']['actors'])==len(semantic['fixed_actors'])==102
h=native['height_map'];tiles=native['tile_map']
for actor,marker in zip(scene['initial_state']['actors'],semantic['fixed_actors']):
    position=[actor['position'][k] for k in 'xyz'];x,y,z=position
    assert position==marker['position']
    assert z==terrain_height(x,y,h)
    assert not 126<=tiles[math.floor(64-y/512)*128+math.floor(x/512+64)]<162,marker['id']
    assert abs(x)<24576 and abs(y)<24576
content=json.loads((source/'lg01.content.json').read_text())
assert content['town_wilderness_initial_minimum_xy']>=8192
# Rewards keep their native event and container identity despite the moved den-side chest.
for prop in semantic['content_landmarks']:
    if prop['kind']!='chest_target':continue
    chest=scene['loot_containers'][prop['container_id']]
    assert chest['container_id']==prop['container_id']
    assert [chest['position'][k] for k in 'xyz']==prop['position']
    model=native['bmodels'][prop['bmodel_index']]
    assert all(f['cog_triggered_number']==prop['event_id'] for f in model['faces'])
# Full water cells must have a level rendered surface, including the new isolated pond.
water=[]
for r in range(127):
    for c in range(127):
        if tiles[r*128+c]!=126:continue
        levels=[h[rr*128+cc]*32 for rr,cc in [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]]
        assert len(set(levels))==1,(r,c,levels)
        water.append(levels[0])
assert set(water)=={256,512},set(water)
# Inspect native deck directions and passage dimensions independently of cosmetic rails.
bridge=native['bmodels'][next(m['index'] for m in semantic['bmodels'] if m['id']=='bridge_deck')]
assert bridge['faces'][0]['polygon_type']==5 and bridge['faces'][1]['polygon_type']==3
assert bridge['faces'][1]['texture_name'].lower()=='trimd'
decor=json.loads((source/'lg01.decorations.json').read_text())
assert len(native['entities'])==len(decor['records'])+1
hostiles=semantic['fixed_actors'][29:]
centers=[np.mean([a['position'][:2] for a in hostiles if a['role']==role],axis=0).tolist()
         for role in sorted({a['role'] for a in hostiles})]
assert len(centers)==11
spacing=np.percentile(cKDTree(centers).query(centers,k=2)[0][:,1],[25,50,75]).round(1).tolist()
report=dict(status='pass',native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    unchanged_town_buildings_arrivals_and_residents=True,hostiles=len(hostiles),encounter_areas=len(centers),
    authored_area_center_nearest_neighbor_quartiles=spacing,initial_town_separation=content['town_wilderness_initial_minimum_xy'],
    decoration_counts=decor['counts'],water_levels=sorted(set(water)),native_chests=4,
    checks='Native grounding/dry actor placement; no duplicate spawns; chest event/target IDs; level water; bridge floor/ceiling; accepted town preserved',
    limitations='Initial placement only; not a combat balance, wandering/aggro or performance claim.',
    elapsed_seconds=round(time.monotonic()-start,3))
(out/'wilderness_check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
