import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(R/'anim_library/humanoid_set/Unarmed.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
report={}
for name in ('UnarmedDeath1','UnarmedGetHitF1'):
 a=next(a for a in bpy.data.actions if a.name.endswith(name))
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 rows=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  rows.append({n:rig.pose.bones[n].matrix.to_quaternion() for n in ('B_Head','B_R_Hand','B_L_Hand','B_L_Foot','B_R_Foot')})
 report[name]={n:max(math.degrees(2*math.acos(min(1,abs(rows[i][n].normalized().dot(rows[i-1][n].normalized()))))) for i in range(1,len(rows))) for n in rows[0]}
print('SOURCE_JERK',report,flush=True)
(P/'work/source_jerk.json').write_text(json.dumps(report,indent=2))
