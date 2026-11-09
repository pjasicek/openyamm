"""Isolate three native fish tiers on the Plane of Water for same-camera palette/LOD checks."""
import copy,hashlib,json,tempfile,shutil,os
from pathlib import Path
import yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2];A=R/'assets_dev'
F=Path(tempfile.mkdtemp(prefix='native-fixture-',dir=P/'work'))/'assets'
# PhysicsFS rejects symbolic links inside a mounted root.
shutil.copytree(A,F,copy_function=os.link,symlinks=True)
(F/'worlds/mm8/maps/elemw.scene.yml').unlink()
source=A/'worlds/mm8/maps/elemw.scene.yml';data=yaml.safe_load(source.read_text())
fish=next(a for a in data['initial_state']['actors'] if a['monster_info_id']==179)
data['spawns']=[];data['initial_state']['actors']=[]
for i,(ident,y) in enumerate([(178,1460),(179,1760),(180,2060)]):
    actor=copy.deepcopy(fish);actor.update(actor_index=i,monster_info_id=ident,immobile=True,position={'x':7600,'y':y,'z':0})
    data['initial_state']['actors'].append(actor)
text=yaml.safe_dump(data,sort_keys=False)
(F/'worlds/mm8/maps/elemw.scene.yml').write_text(text)
Q=P/'review/ingame';(Q/'fixture_scene.yml').write_text(text)
(Q/'fixture.json').write_text(json.dumps({'assets':str(F),'source':str(source.relative_to(R)),
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'actors':data['initial_state']['actors'],
 'scope':'Review-only map overlay. Native geometry/environment, three native fish actors, no encounter spawns.'},indent=2)+'\n')
for mode in ['models','sprites']:
    steps=[{'wait':.2},{'right_down':[20,800]},{'console':'render lod 0'},{'wait':1},{'capture':'school_lod0'}]
    if mode=='models':
        for lod in [1,2,3]:steps.extend([{'console':f'render lod {lod}'},{'wait':.4},{'capture':f'school_lod{lod}'}])
    steps.append({'right_up':[20,800]})
    (Q/f'fixture_{mode}.yml').write_text(yaml.safe_dump({'output_dir':str((Q/f'fixture_{mode}').resolve()),'exit':True,'steps':steps},sort_keys=False))
print(F)
