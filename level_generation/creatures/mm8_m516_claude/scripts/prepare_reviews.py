"""Isolated native comparison fixture and input tours; production maps are unchanged."""
from pathlib import Path
import copy,hashlib,json,os,shutil,tempfile,yaml
ROOT=Path.cwd();P=Path(__file__).resolve().parents[1];out=P/'review/ingame';out.mkdir(exist_ok=True)
captures=Path(tempfile.mkdtemp(prefix='openyamm-thunder-lizard-native-'));records=[]
for place,positions in [('out',[(-4760,3322,1),(-4695,3029,1),(-4630,2736,1)]),('in',[(900,-2935,-47),(900,-2735,-47),(900,-3135,-47)])]:
 for mode in ['models','sprites']:
  steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'wait':.25}]
  for monster,position in zip([88,89,90],positions):steps += [{'text':f'actor spawn {monster} 1 '+' '.join(map(str,position))+' friendly'},{'key':'Return'},{'wait':.25}]
  steps += [{'key':'`'},{'wait':.2},{'capture':'front'},{'wait':1},{'capture':'walk'},{'wait':1},{'capture':'later'}]
  if mode=='models':steps += [{'key':'`'},{'text':'render lod 2'},{'key':'Return'},{'key':'`'},{'wait':.3},{'capture':'lod2'}]
  (out/f'{place}_{mode}.yml').write_text(yaml.safe_dump({'output_dir':str(captures/f'{place}_{mode}'),'exit':True,'steps':steps},sort_keys=False))
source=ROOT/'assets_dev';target=Path(tempfile.mkdtemp(prefix='visual-fixture-',dir=P/'work'))/'assets'
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
for relative in map(Path,['worlds/mm6/maps/6d19.scene.yml','worlds/mm6/maps/oute3.scene.yml']):
 original=(source/relative).read_bytes();scene=yaml.safe_load(original);actors=scene['initial_state']['actors']
 for monster in [88,89,90]:
  actor=copy.deepcopy(actors[0]);actor.update(actor_index=len(actors),name='Thunder Lizard preload fixture',monster_info_id=monster,monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,sprite_ids=[0,0,0,0],immobile=True);actors.append(actor)
 (target/relative).unlink();(target/relative).write_text(yaml.safe_dump(scene,sort_keys=False));assert (source/relative).read_bytes()==original
 records.append({'path':str(relative),'original_sha256':hashlib.sha256(original).hexdigest(),'added_monster_ids':[88,89,90]})
manifest=target/'worlds/mm8/models/actors.yml';data=manifest.read_bytes();manifest.unlink();manifest.write_bytes(data)
(out/'fixture.json').write_text(json.dumps({'assets_root':str(target),'captures_root':str(captures),'scenes':records},indent=2)+'\n')
# Live combat exercises the fitted lunge, flinch and native corpse transition.
steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'text':'actor spawn 90 1 1250 -2935 -47'},{'key':'Return'},{'key':'`'},{'wait':.6},{'capture':'approach'}]
for i in range(10):steps += [{'wait':.3},{'capture':f'combat-{i:02}'}]
steps += [{'key':'`'},{'text':'actor damage last 1'},{'key':'Return'},{'key':'`'},{'wait':.1},{'capture':'hit'},{'wait':1},{'key':'`'},{'text':'actor damage last 999999'},{'key':'Return'},{'key':'`'},{'wait':.1},{'capture':'death-start'},{'wait':.25},{'capture':'death-mid'},{'wait':.4},{'capture':'corpse'},{'wait':1.5},{'capture':'loot-transition'}]
(out/'combat.yml').write_text(yaml.safe_dump({'output_dir':str(captures/'combat'),'exit':True,'steps':steps},sort_keys=False))
print(json.dumps({'assets_root':str(target),'captures_root':str(captures)}))
