"""Isolated native-comparison fixture: preload foreign sprite families without editing production maps."""
import copy
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
import yaml
P=Path(__file__).resolve().parents[1]
ROOT=P.parents[2]
source=ROOT/'assets_dev'
target=Path(tempfile.mkdtemp(prefix='native-fixture-',dir=P/'work'))/'assets'
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
capture_root=Path(tempfile.mkdtemp(prefix='openyamm-unicorn-captures-'))
records=[]
for map_name in ['oute3','6d19']:
    relative=Path('worlds/mm6/maps')/(map_name+'.scene.yml')
    raw=(source/relative).read_bytes()
    scene=yaml.safe_load(raw)
    actors=scene['initial_state']['actors']
    count=len(actors)
    for monster in [109,110,111]:
        actor=copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors),name='Unicorn sprite preload fixture',monster_info_id=monster,
            monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,
            sprite_ids=[0,0,0,0],immobile=True)
        actors.append(actor)
    (target/relative).unlink()
    (target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
    assert (source/relative).read_bytes()==raw
    records.append(dict(scene=str(relative),original_actor_count=count,original_sha256=hashlib.sha256(raw).hexdigest()))
# Limit this explicit review fixture to the family under test; production bindings stay untouched.
manifest=Path('worlds/mm8/models/actors.yml')
raw=(source/manifest).read_bytes()
entries=[a for a in yaml.safe_load(raw)['actors'] if a['descriptor'] in ['Unicorn A','Unicorn B','Unicorn C']]
assert len(entries)==3
(target/manifest).unlink()
(target/manifest).write_text(yaml.safe_dump({'actors':entries},sort_keys=False))
assert (source/manifest).read_bytes()==raw
out=P/'review/ingame'
out.mkdir(exist_ok=True)
(out/'fixture.json').write_text(json.dumps(dict(assets_root=str(target),capture_root=str(capture_root),scenes=records),indent=2)+'\n')
for place,spawns in [('out',[(-4357,2989,1),(-4357,3169,1),(-4357,3349,1)]),
                     ('in',[(950,-3075,-47),(950,-2915,-47),(950,-2755,-47)])]:
    for mode in ['3d','sprite']:
        steps=[{'wait':1},{'key':'`'},{'wait':.25}]
        for monster,position in zip([109,110,111],spawns):
            steps += [{'text':'actor spawn '+str(monster)+' 1 '+' '.join(map(str,position))+' friendly'},
                      {'key':'Return'},{'wait':.2}]
        steps += [{'key':'`'},{'wait':.35},{'capture':'tiers'},{'wait':1},{'capture':'motion'},
                  {'key':'`'},{'wait':.2},{'text':'actor kill 800'},{'key':'Return'},
                  {'key':'`'},{'wait':.3},{'capture':'death'},{'wait':.55},{'capture':'corpses'},{'wait':1.0},{'capture':'remains'}]
        tour=dict(output_dir=str(capture_root/(place+'_'+mode)),exit=True,steps=steps)
        (out/(place+'_'+mode+'.yml')).write_text(yaml.safe_dump(tour,sort_keys=False))
print(target)

steps=[{'wait':1},{'key':'`'},{'wait':.25},
       {'text':'actor spawn 111 1 -4257 3169 1'},{'key':'Return'},
       {'text':'actor damage last 1'},{'key':'Return'},{'key':'`'}]
for i in range(18):steps += [{'wait':.25},{'capture':f'combat_{i:02d}'}]
steps += [{'key':'`'},{'text':'actor damage last 1'},{'key':'Return'},{'key':'`'},
          {'wait':.15},{'capture':'hit'},{'wait':.6},{'key':'`'},
          {'text':'actor kill 800'},{'key':'Return'},{'key':'`'},
          {'wait':.3},{'capture':'death'},{'wait':.55},{'capture':'corpse'}]
(out/'combat.yml').write_text(yaml.safe_dump(dict(output_dir=str(capture_root/'combat'),exit=True,steps=steps),sort_keys=False))
