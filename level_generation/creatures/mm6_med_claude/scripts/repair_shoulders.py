"""Tuck the inward shoulder-cap tips into the torso and carry their roots with the chest."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv_pre_shoulder.blend'));body=bpy.data.objects['Body'];me=body.data;parts=np.array([x.value for x in me.attributes['part'].data]);changed=[];sp=body.vertex_groups['B_Spine2']
for v in me.vertices:
 if parts[v.index] not in [6,9]:continue
 x,y,z=v.co;w=float(np.clip((.174-abs(x))/.042,0,1)*np.clip((z-1.53)/.06,0,1)*np.clip((1.75-z)/.025,0,1))
 if w<.001:continue
 changed.append({'vertex':v.index,'weight':w,'before':list(v.co)})
 v.co.x-=np.sign(x)*.025*w
 old={body.vertex_groups[g.group].name:g.weight for g in v.groups};new={n:a*(1-w) for n,a in old.items()};new['B_Spine2']=new.get('B_Spine2',0)+w;new=dict(sorted(new.items(),key=lambda x:-x[1])[:4]);total=sum(new.values())
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for n,a in new.items():
  if a>1e-6:body.vertex_groups[n].add([v.index],a/total,'REPLACE')
me.update();assert 5<len(changed)<250,len(changed);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'));(P/'work/shoulder_root_fix.json').write_text(json.dumps(changed,indent=2));print('SHOULDER ROOTS',len(changed))
