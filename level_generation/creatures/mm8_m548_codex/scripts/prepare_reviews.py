"""Prepare reproducible native captures; only an isolated map fixture declares foreign sprite families."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import tempfile
import yaml

root=Path.cwd();project=root/'level_generation/creatures/mm8_m548_codex'
out=project/'review/ingame';out.mkdir(exist_ok=True)
for place,positions in [('out',[(-4760,3322,1),(-4695,3029,1),(-4630,2736,1)]),
                        ('in',[(500,-2935,-47),(500,-2575,-47),(500,-3295,-47)])]:
    for mode in ['models','sprites']:
        steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'wait':.25}]
        for monster,position in zip([112,113,114],positions):
            steps += [{'text':f'actor spawn {monster} 1 '+ ' '.join(map(str,position))+' friendly'},
                      {'key':'Return'},{'wait':.25}]
        steps += [{'key':'`'},{'wait':.2},{'capture':'front'},{'wait':1.0},{'capture':'walk'},
                  {'wait':1.0},{'capture':'later'}]
        if mode=='models':
            steps += [{'key':'`'},{'text':'render lod 2'},{'key':'Return'},{'key':'`'},
                      {'wait':.3},{'capture':'lod2'}]
        (out/f'{place}_{mode}.yml').write_text(yaml.safe_dump({'output_dir':str(out/f'{place}_{mode}'),
                                                            'exit':True,'steps':steps},sort_keys=False))
source=root/'assets_dev';target=Path(tempfile.mkdtemp(prefix='visual-fixture-',dir=project/'work'))/'assets'
probe=target.parent/'link-probe'
os.link(source/'engine/icon_packages.txt',probe);probe.unlink()
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
records=[]
for relative in map(Path,['worlds/mm6/maps/6d19.scene.yml','worlds/mm6/maps/oute3.scene.yml']):
    original=(source/relative).read_bytes()
    scene=yaml.safe_load(original);actors=scene['initial_state']['actors'];count=len(actors)
    for monster in [112,113,114]:
        actor=copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors),name='Crystal Dragon preload fixture',monster_info_id=monster,
                     monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,
                     sprite_ids=[0,0,0,0],immobile=True)
        actors.append(actor)
    (target/relative).unlink()
    (target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
    assert (source/relative).read_bytes()==original and len(actors)==count+3
    records.append({'path':str(relative),'original_sha256':hashlib.sha256(original).hexdigest(),
                    'added_monster_ids':[112,113,114]})
# Snapshot the binding manifest because other creature production may update it during review.
manifest=target/'worlds/mm8/models/actors.yml';data=manifest.read_bytes()
manifest.unlink();manifest.write_bytes(data)
record={'assets_root':str(target),'scenes':records,
        'purpose':'Preload foreign native sprite families; production maps unchanged.'}
(out/'fixture.json').write_text(json.dumps(record,indent=2)+'\n')
print(target)
