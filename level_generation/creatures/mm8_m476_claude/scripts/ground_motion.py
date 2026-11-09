import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_level.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups]
foot=np.array([sum(e.weight for e in v.groups if 'Foot' in names[e.group] or 'Toe' in names[e.group])>.5 for v in body.data.vertices])
report={}
for a in list(bpy.data.actions):
 rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 vals=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear()
  low=co[:,2].min() if a.name=='Death' else co[foot,2].min()
  vals.append(float(low))
 # Preserve airborne parts of the run, shifting the contact minima to floor.
 offsets=np.array(vals)
 if a.name=='Running': offsets=offsets-np.clip(offsets-np.quantile(offsets,.25),0,.04)
 report[a.name]={'before_cm':[round(min(vals)*100,2),round(max(vals)*100,2)]}
 for f,z in enumerate(offsets):
  sc.frame_set(f);b=rig.pose.bones['B_Pelvis'];M=b.matrix.copy();M.translation.z-=float(z);b.matrix=M;b.keyframe_insert('location',frame=f)
 print('FLOOR',a.name,report[a.name])
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
(p/'work/floor_fit.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_grounded.blend'))
