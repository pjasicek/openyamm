import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('gates_motion.py')
run('g4_weights.py',[p/'work/rig_v8.blend','final_attack','Attack:20','Attack:21'])
import bpy,common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v8.blend'));r=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene)
for role,f in [('Walking',10),('Attack',34),('Attack',20),('Hit',12),('Death',16)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 common.render_views(str(p/f'review/contact_{role}_{f}'),.85,2.15,views=('front','back','left'),resolution=(500,600))
