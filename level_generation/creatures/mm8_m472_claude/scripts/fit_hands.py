from pathlib import Path
import runpy,sys,bpy
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];pv=body.data.attributes['piece'].data
for v in body.data.vertices:
 piece=pv[v.index].value
 if piece in (3,4):
  for g in body.vertex_groups:g.remove([v.index])
  body.vertex_groups['B_L_Hand' if piece==3 else 'B_R_Hand'].add([v.index],1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v1.blend'))
run('finger_weights.py',p/'work/rig_v1.blend',p/'work/rig_fingers.blend')
for side in ('L','R'):run('hand_xray.py',p/'work/rig_fingers.blend',side,p/f'review/hand_fit_{side}')
run('hand_frame_check.py',p/'work/rig_fingers.blend')
