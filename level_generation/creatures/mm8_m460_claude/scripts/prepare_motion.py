from pathlib import Path
import bpy,sys,runpy,os
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,args):
    s=p/'scripts'/n;sys.argv=[str(s),'--']+list(map(str,args));runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
body=bpy.data.objects['Body']
for v,a in zip(body.data.vertices,body.data.attributes['piece'].data):
    if a.value not in (3,4):continue
    for g in body.vertex_groups:g.remove([v.index])
    body.vertex_groups['B_L_Hand' if a.value==3 else 'B_R_Hand'].add([v.index],1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_hands.blend'))
run('finger_weights.py',[p/'work/rig_hands.blend',p/'work/rig_fingers.blend'])
lib=root/'anim_library/humanoid_set'
run('retarget.py',[p/'work/rig_fingers.blend',p/'work/motion_sources.blend',
    f'{lib}/Relax.glb:RelaxIdle:Standing',f'{lib}/Relax.glb:RelaxWalkForward:Walking',
    f'{lib}/Unarmed.glb:UnarmedCastDualAttack2:Attack',f'{lib}/Unarmed.glb:UnarmedCastDualAttack2:Cast',
    f'{lib}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{lib}/Relax.glb:RelaxLaydownLayDown:Death'])
os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',[p/'work/motion_sources.blend','Standing','0'])
