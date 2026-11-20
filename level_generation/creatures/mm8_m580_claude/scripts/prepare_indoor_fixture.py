from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import tempfile
import yaml
root=Path('/home/pjasicek/github/OpenYAMM')
project=root/'level_generation/creatures/mm8_m580_claude'
source=root/'assets_dev'
target=Path(tempfile.mkdtemp(prefix='indoor-fixture-',dir=project/'work'))/'assets'
# PhysicsFS rejects symbolic links inside mounted roots. Hard links keep this fixture small.
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
records=[]
for world,map_name in [('mm6','6d19'),('mm6','oute3'),('mm8','out01')]:
    relative=Path(f'worlds/{world}/maps/{map_name}.scene.yml')
    before=(source/relative).read_bytes()
    scene=yaml.safe_load(before)
    actors=scene['initial_state']['actors'];original_count=len(actors)
    for monster_id in (136,137,138):
        actor=copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors),name='Dragon Turtle sprite preload fixture',monster_info_id=monster_id,
                     monster_id=monster_id,unique_name_index=0,group=999,ally=999,hostility_type=0,
                     sprite_ids=[0,0,0,0],immobile=True)
        actors.append(actor)
    (target/relative).unlink()
    (target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
    assert len(actors)==original_count+3 and (source/relative).read_bytes()==before
    records.append({'scene':str(relative),'original_sha256':hashlib.sha256(before).hexdigest(),
                    'fixture_sha256':hashlib.sha256((target/relative).read_bytes()).hexdigest(),
                    'original_actor_count':original_count})
record={'assets_root':str(target),'scenes':records,'added_monster_ids':[136,137,138],
        'purpose':'Preload native MM8 sprite families in isolated MM6 visual checks; production maps unchanged.'}
(project/'review/ingame/indoor_fixture.json').write_text(json.dumps(record,indent=2)+'\n')
print(target)
