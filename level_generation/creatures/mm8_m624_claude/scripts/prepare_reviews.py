"""Prepare reproducible native captures; only an isolated map fixture declares foreign sprite families."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import tempfile
import yaml

root=Path.cwd();project=root/'level_generation/creatures/mm8_m624_claude'
out=project/'review/ingame';out.mkdir(exist_ok=True)
positions_by_map={'oute3': [(-4380,3550,1),(-4380,3150,1),(-4380,2750,1)],
                  '6d19':[(990,-2540,-47),(990,-2910,-47),(990,-3280,-47)]}
for place in ['out','in']:
    for mode in ['models','sprites']:
        steps=[{'expect':'gameplay'},{'wait':1},{'capture':'front'},{'wait':1},{'capture':'later'}]
        if mode=='models':
            steps += [{'console':'render lod 2'},
                      {'wait':.2},{'capture':'lod2'}]
        (out/f'{place}_{mode}.yml').write_text(yaml.safe_dump({'output_dir':'/tmp/m624-final-'+place+'_'+mode,
                                                            'exit':True,'steps':steps},sort_keys=False))
source=root/'assets_dev';target=Path(tempfile.mkdtemp(prefix='visual-fixture-',dir=project/'work'))/'assets'
probe=target.parent/'link-probe'
os.link(source/'engine/icon_packages.txt',probe);probe.unlink()
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
records=[]
for relative in map(Path,['worlds/mm6/maps/6d19.scene.yml','worlds/mm6/maps/oute3.scene.yml']):
    original=(source/relative).read_bytes()
    scene=yaml.safe_load(original);actors=scene['initial_state']['actors'];count=len(actors)
    for tier,monster in enumerate([169,170,171]):
        actor=copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors),name='Naga preload fixture',monster_info_id=monster,
                     monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,
                     sprite_ids=[0,0,0,0],immobile=True)
        actor.update(position=dict(zip(['x','y','z'],positions_by_map[relative.name.split('.')[0]][tier])),
                     initial_yaw_units=0,move_speed=0,radius=90,height=160,sector_id=0,current_action_animation=0)
        actors.append(actor)
    (target/relative).unlink()
    (target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
    assert (source/relative).read_bytes()==original and len(actors)==count+3
    records.append({'path':str(relative),'original_sha256':hashlib.sha256(original).hexdigest(),
                    'added_monster_ids':[169,170,171]})
items=target/'engine/world_items/items.yml';item_data=items.read_bytes()
items.unlink();items.write_bytes(item_data)
# Snapshot the binding manifest because other creature production may update it during review.
manifest=target/'worlds/mm8/models/actors.yml';data=manifest.read_bytes()
manifest.unlink();manifest.write_bytes(data)
record={'assets_root':str(target),'scenes':records,
        'purpose':'Immobile placed tier comparison at fixed coordinates; production maps unchanged.'}
(out/'fixture.json').write_text(json.dumps(record,indent=2)+'\n')
print(target)
