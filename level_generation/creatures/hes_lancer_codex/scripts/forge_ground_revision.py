"""Ground the heavier hull and maul while preserving the authored release in world space."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_concept_fit.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
parts=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Body' or o.name.startswith(('Arm_','Apron_')))];maul=bpy.data.objects['Thunder_Maul'];local=[r.data.bones['Thunder_Maul'].matrix_local.inverted()@v.co for v in maul.data.vertices]
def low(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();z=min((ob.matrix_world@v.co).z for v in me.vertices);e.to_mesh_clear();return z
report={}
for clip in ('Forge_Death','Forge_Dead'):
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[];maximum=0.
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));weapon=armik.W(r,'Thunder_Maul').copy();offset=max(0,.004-min(low(o) for o in parts));maximum=max(maximum,offset);root=armik.W(r,'B_Pelvis');root.translation.z+=offset;armik.set_world(r,'B_Pelvis',root)
  weapon.translation.z+=max(0,.004-min((weapon@v).z for v in local));armik.set_world(r,'Thunder_Maul',weapon)
  keys.append((float(f),{n:r.pose.bones[n].matrix_basis.copy() for n in ('B_Pelvis','Thunder_Maul')}))
 previous={}
 for f,pose in keys:
  for n,m in pose.items():
   b=r.pose.bones[n];q=m.to_quaternion()
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f)
 report[clip]={'max_root_lift_m':maximum};print('GROUND_HULL',clip,maximum,flush=True)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_concept_grounded.blend'));(P/'review/forge_concept_grounding.json').write_text(json.dumps(report,indent=2)+'\n');sys.stdout.flush();os._exit(0)
