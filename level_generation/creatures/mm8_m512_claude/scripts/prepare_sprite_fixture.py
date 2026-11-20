"""Read-only asset hard links plus wolf frame definitions for cross-world indoor debug spawns."""
from pathlib import Path
import os
import shutil
import yaml
P=Path(__file__).resolve().parents[1];source=P.parents[2]/'assets_dev';target=P/'work/sprite_fixture/assets_dev'
# PhysicsFS rejects internal symlinks. Hard-link unchanged files, then detach the one review-only table.
if not target.exists():shutil.copytree(source,target,copy_function=os.link)
common=yaml.safe_load((source/'engine/rendering/sprite_frame_data_common.yml').read_text())
for family in ['m513','m514','m515']:
 extra=yaml.safe_load((source/f'engine/rendering/sprite_frames/monsters/{family}.yml').read_text())
 common['sprites'].extend(extra['sprites'])
assert len({x['sprite_id'] for x in common['sprites']})==len(common['sprites'])
(target/'engine/rendering/sprite_frame_data_common.yml').unlink()
(target/'engine/rendering/sprite_frame_data_common.yml').write_text(yaml.safe_dump(common,sort_keys=False))
bindings=target/'worlds/mm8/models/actors.yml'
manifest=yaml.safe_load((source/'worlds/mm8/models/actors.yml').read_text())
manifest['actors']=[a for a in manifest['actors'] if a['descriptor'].startswith('Dire Wolf ')]
assert len(manifest['actors'])==3
bindings.unlink();bindings.write_text(yaml.safe_dump(manifest,sort_keys=False))
(P/'work/sprite_fixture/settings.ini').write_text('[assets]\nroot='+str(target)+'\n')
print(target)
