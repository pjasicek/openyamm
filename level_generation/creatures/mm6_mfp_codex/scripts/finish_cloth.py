import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/cloth_fit.py'),run_name='__main__')
# Re-bake helpers after arm edits without distributing weights a second time.
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in list(bpy.data.actions):bake_twist(a)
body=bpy.data.objects['Body'];root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones[root.name].matrix_local.to_3x3().inverted();floor={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];nf=int(a.frame_range[1]);corr=[0.]*(nf+1);loc=[]
 for f in range(nf+1):sc.frame_set(f);loc.append(root.location.copy())
 for t in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(t),subframe=float(t%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();dz=max(0,.0003-min(v.co.z for v in me.vertices));ev.to_mesh_clear()
  for j in {int(t),min(nf,math.ceil(t))}:corr[j]=max(corr[j],dz)
 for f,l in enumerate(loc):root.location=l+inv@Vector((0,0,corr[f]));root.keyframe_insert('location',frame=f)
 floor[a.name]=max(corr)
(P/'review/floor_corrections.json').write_text(json.dumps(floor,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__')
