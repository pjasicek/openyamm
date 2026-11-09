from pathlib import Path
import bpy,json,sys,math
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_fitted.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];path=json.loads((p/'work/boulder_path.json').read_text());r={'source':'working_05 fitted Attack frame 12','frame':12,'centre':path[12]['centre'],'hands':{}}
bpy.context.scene.frame_set(12)
for s in 'LR':
 r['hands'][s]={'matrix':[list(row) for row in rig.pose.bones[f'B_{s}_Hand'].matrix],'fingers':{pb.name:list(pb.rotation_quaternion) for pb in rig.pose.bones if pb.name.startswith(f'B_{s}_Finger')}}
bpy.context.scene.frame_set(24)
for s in 'LR':
 from mathutils import Matrix
 q=rig.pose.bones[f'B_{s}_Hand'].matrix.to_quaternion()@Matrix(r['hands'][s]['matrix']).to_quaternion().inverted();print('GRIP_ROTATION',s,[round(math.degrees(v),2) for v in q.to_euler()],flush=True)
(p/'work/selected_grip.json').write_text(json.dumps(r,indent=2))
