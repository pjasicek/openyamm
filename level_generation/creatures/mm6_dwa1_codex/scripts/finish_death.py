import bpy,shutil,numpy as np,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bk=P/'work/before_death_finish.blend'
if not bk.exists():shutil.copy2(P/'work/textured_master.blend',bk)
bpy.ops.wm.open_mainfile(filepath=str(bk));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;ns=[f'B_{s}_{n}'for s in'LR'for n in ['Thigh','Calf','Foot']];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);ref={n:rig.pose.bones[n].rotation_quaternion.copy()for n in ns};a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];poses=[];end=int(a.frame_range[1])
for f in range(end+1):
 scene.frame_set(f);poses.append({n:ref[n].slerp(rig.pose.bones[n].rotation_quaternion,.4)for n in ns})
for f,pose in enumerate(poses):
 for n,q in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
# Refit the changed corpse motion from actual mesh minima, preserving the fall and upper-body action.
floors=[]
for f in np.arange(0,end+.0001,.25):
 scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();floors.append(min((body.matrix_world@v.co).z for v in m.vertices));ev.to_mesh_clear()
required=np.maximum(0,-np.array(floors))+.001;lifts=[float(required[max(0,f*4-2):min(len(required),f*4+3)].max())for f in range(end+1)];loc=[]
for f in range(end+1):
 scene.frame_set(f);pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=lifts[f];pb.matrix=M;loc.append(pb.location.copy())
for f,l in enumerate(loc):rig.pose.bones['B_Pelvis'].location=l;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));(P/'review/death_fit.json').write_text(json.dumps({'leg_motion_share':.4,'root_lift_min_max_m':[min(lifts),max(lifts)]},indent=2));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
