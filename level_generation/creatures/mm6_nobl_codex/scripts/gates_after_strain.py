import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('build_sword.py');run('export_review.py')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
run('g6_contacts.py',[p/'review/viewer/mm6_nobl_clay.glb',*roles])
run('g6_head_clearance.py',[p/'work/rig_v8.blend',*roles])
for role in roles:run('cloak_stretch.py',['rig_v8.blend',role,'2'])
for role in ['Walking','Running']:
 os.environ['CLIP']=role;run('cloak_poke.py',['rig_v8.blend'])
lib=Path('/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set')
refs={'Standing':('Relax','RelaxIdle'),'Fidget':('Relax','RelaxIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR1'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed-Shield','ShieldDeath1')}
run('trace_export.py',[p/'review/viewer/mm6_nobl_clay.glb',*[f'{role}={lib}/{s}.glb:{clip}' for role,(s,clip) in refs.items()]])
run('g6_sword_mesh.py',[p/'review/viewer/mm6_nobl_clay.glb'])
os.environ['ROLL_SWEEP']='1'
run('blade_edge_gate.py',[p/'review/viewer/mm6_nobl_clay.glb'])

import bpy,common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v8.blend'));r=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene)
for role,f in [('Standing',0),('Walking',10),('Attack',23),('Death',23),('Death',54)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 common.render_views(str(p/f'review/strain_{role}_{f}'),.85,2.15,views=('front','back','left'),resolution=(500,600))
