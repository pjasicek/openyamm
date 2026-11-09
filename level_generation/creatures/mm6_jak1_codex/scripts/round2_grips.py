import bpy,sys,runpy,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
L=ROOT/'anim_library/humanoid_set'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'))
for a in list(bpy.data.actions):
 if a.name.startswith('StaffCast'):bpy.data.actions.remove(a)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_sources.blend'))
run('retarget.py',['work/round2_sources.blend','work/round2_sources.blend',*[f'{L}/2Hand Staff.glb:{n}:{a}' for n,a in [('StaffCastLAttack1','Cast1'),('StaffCastLAttack2','Cast2'),('StaffCastLAttack3','Cast3'),('StaffCastSummon1','Summon')]]])
os.environ['GRIP_SIDE']='L';os.environ['GRIP_SOURCE']='grip_source_left.json';os.environ['GRIP_OUTPUT']='grip_pose_left.json';os.environ['R_HANDLE']='.013'
run('grip_from_source.py',[L/'2Hand Staff.glb','StaffAttack2:0'])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_grip.blend'))
with bpy.data.libraries.load(str(P/'work/round2_sources.blend')) as (src,dst):dst.actions=['Staff2']
for a in dst.actions:a.use_fake_user=True
from hand_weights import repair_hand_weights
repair_hand_weights(bpy.data.objects['Body'],bpy.data.objects['Rig'])
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_grip_input.blend'))
run('grip_solve.py',['work/round2_grip_input.blend','Staff2',0])
