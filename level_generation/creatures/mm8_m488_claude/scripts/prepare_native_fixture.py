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
records=[]
for map_name in ['oute3','6d19']:
    relative=Path('worlds/mm6/maps')/(map_name+'.scene.yml')
    raw=(source/relative).read_bytes()
    scene=yaml.safe_load(raw)
    actors=scene['initial_state']['actors']
    count=len(actors)
    for monster in [67,68,69]:
        actor=copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors),name='MinotaurPeasant sprite preload fixture',monster_info_id=monster,
            monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,
            sprite_ids=[0,0,0,0],immobile=True)
        actors.append(actor)
    (target/relative).unlink()
    (target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
    assert (source/relative).read_bytes()==raw
    records.append(dict(scene=str(relative),original_actor_count=count,original_sha256=hashlib.sha256(raw).hexdigest()))
out=P/'review/ingame'
out.mkdir(exist_ok=True)
(out/'fixture.json').write_text(json.dumps(dict(assets_root=str(target),scenes=records),indent=2)+'\n')
for place,spawns in [('out',[(-4300,2800,0),(-4400,3200,0),(-4450,3600,0)]),
                     ('in',[(1100,-3210,0),(1050,-2930,0),(1000,-2650,0)])]:
    for mode in ['3d','sprite']:
        steps=[{'wait':1},{'key':'`'},{'wait':.25}]
        for monster,position in zip([67,68,69],spawns):
            steps += [{'text':'actor spawn '+str(monster)+' 1 '+' '.join(map(str,position))+' friendly'},
                      {'key':'Return'},{'wait':.2}]
        steps += [{'key':'`'},{'wait':.35},{'capture':'tiers'},{'wait':1},{'capture':'motion'},
                  {'key':'`'},{'wait':.2},{'text':'actor kill 2500'},{'key':'Return'},
                  {'key':'`'},{'wait':1.5},{'capture':'corpses'}]
        tour=dict(output_dir=str(Path('/tmp/m488-captures')/(place+'_'+mode)),exit=True,steps=steps)
        (out/(place+'_'+mode+'.yml')).write_text(yaml.safe_dump(tour,sort_keys=False))
print(target)
