"""Audit effective MM8 terrain after full-scene and ordered scene-overlay settings.

Keep the raw ODM inventory as historical build provenance. This supplement records
the settings the runtime applies before descriptor resolution, including Shadowspire.
"""
import collections
import csv
import json
import yaml
from common import *
from inventory import descriptor_index, parse_odm_file

original = json.loads((P/'inventory.json').read_text())
table_path = ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt'
table = list(csv.DictReader(table_path.open(),delimiter='\t'))
roots = [ROOT/'assets_dev/engine/maps'] + sorted((ROOT/'assets_dev/worlds').glob('*/maps'))
maps,grids,used = [],{},collections.defaultdict(dict)
for record in original['maps']:
    source=ROOT/record['source']; data=parse_odm_file(source)['payload'];name=record['id']
    master,lookup=data['master_tile'],data['tile_set_lookup_indices']
    base=source.with_suffix('.scene.yml')
    candidates=[]
    for root in roots:
        candidates.extend(root.glob(name+'_*.scene.yml'))
        candidates.extend(root.glob(name+'.scene.*.yml'))
    candidates=sorted(set(candidates),key=lambda p:p.name.lower())
    assert len({p.name.lower() for p in candidates})==len(candidates),'Ambiguous mounted overlays'
    paths=[base]+candidates if base.exists() else []
    changes=[]
    for path in paths:
        scene=yaml.load(path.read_text(),Loader=yaml.CSafeLoader)
        assert scene['source']['geometry_file'].lower()==source.name.lower(),path
        terrain=scene.get('terrain',{})
        unknown=set(terrain)-{'attribute_overrides','footstep_sound_overrides'}
        assert not unknown,(path,unknown,'Needs explicit terrain override audit')
        environment=scene.get('environment',{})
        before=(master,list(lookup))
        master=environment.get('master_tile',master)
        lookup=environment.get('tile_set_lookup_indices',lookup)
        if before!=(master,list(lookup)):
            changes.append(dict(path=str(path.relative_to(ROOT)),before=before,after=(master,lookup)))
    grid=[]
    for y in range(127):
        grid.append([table[descriptor_index(raw,master,lookup)]['texture_name'].lower()
                     for raw in data['tile_map'][y*128:y*128+127]])
    counts=collections.Counter(n for row in grid for n in row)
    assert '' not in counts and 'pending' not in counts
    for n,count in counts.items():used[n][name]=count
    grids[name]=grid
    maps.append(dict(id=name,master_tile=master,lookup=lookup,tiles=dict(counts),changes=changes,
                     sources={str(p.relative_to(ROOT)):sha(p) for p in [source]+paths}))
old={r['name'] for r in original['tiles'] if r['maps']}
frames={r['name'] for r in original['tiles'] if r['kind']=='animation'}
assert len(frames)==42
report=dict(scope='14 mounted MM8 outdoor maps including full scenes and ordered world/engine scene overlays',
            source_inventory_sha256=sha(P/'inventory.json'),table_sha256=sha(table_path),
            maps=maps,used_static_count=len(used),animation_frames=len(frames),
            runtime_names=sorted(set(used)|frames),target_runtime_files=len(set(used)|frames),
            added_names=sorted(set(used)-old),removed_names=sorted(old-set(used)),
            uses=dict(used))
(P/'effective_inventory.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'effective_grids.json').write_text(json.dumps(grids)+'\n')
print('Effective inventory:',len(used),'static;',len(set(used)|frames),'runtime; added',report['added_names'])
print('Changed settings:',[(r['id'],r['changes']) for r in maps if r['changes']])
