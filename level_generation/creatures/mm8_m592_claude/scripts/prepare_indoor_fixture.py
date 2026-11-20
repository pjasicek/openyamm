from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import tempfile
import yaml
root=Path('/home/pjasicek/github/OpenYAMM')
project=root/'level_generation/creatures/mm8_m592_claude'
source=root/'assets_dev'
target=Path(tempfile.mkdtemp(prefix='indoor-fixture-',dir=project/'work'))/'assets'
# PhysicsFS rejects symbolic links inside mounted roots. Hard links keep this fixture small.
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
relative=Path('worlds/mm6/maps/6d19.scene.yml')
scene=yaml.safe_load((source/relative).read_text())
actors=scene['initial_state']['actors']
original_count=len(actors)
for monster_id in (145,146,147,196,197,198):
    actor=copy.deepcopy(actors[0])
    actor.update(actor_index=len(actors),name='Plane Guardian sprite preload fixture',monster_info_id=monster_id,
                 monster_id=monster_id,unique_name_index=0,group=999,ally=999,hostility_type=0,
                 sprite_ids=[0,0,0,0],immobile=True)
    actors.append(actor)
# Break only the fixture's link before changing it; production assets must remain untouched.
(target/relative).unlink()
(target/relative).write_text(yaml.safe_dump(scene,sort_keys=False))
assert len(actors)==original_count+6
assert len(yaml.safe_load((source/relative).read_text())['initial_state']['actors'])==original_count
record={'assets_root':str(target),'scene':str(relative),'original_sha256':hashlib.sha256((source/relative).read_bytes()).hexdigest(),
        'fixture_sha256':hashlib.sha256((target/relative).read_bytes()).hexdigest(),
        'purpose':'Declare six distant Plane Guardians so the indoor map loads native sprite families before debug summons. Production map is untouched.',
        'added_monster_ids':[145,146,147,196,197,198]}
(project/'review/ingame/indoor_fixture.json').write_text(json.dumps(record,indent=2)+'\n')
print(target)
