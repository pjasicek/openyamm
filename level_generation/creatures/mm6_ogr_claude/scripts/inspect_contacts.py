from pathlib import Path
import runpy,sys,os,bpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common
runpy.run_path(str(p/'scripts/cloth.py'),run_name='__main__')
rig=bpy.data.objects['Rig']
common.workbench_clay(bpy.context.scene)
for an,f in [('Attack',19),('Attack',21),('Hit',14),('Running',23),('Death',31)]:
 a=bpy.data.actions[an];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 c=rig.matrix_world@rig.pose.bones['B_Head'].head
 common.render_views(str(p/'review'/f'head_{an}_{f}'),c.z+.06,.55,views=('front','left','right'),resolution=(650,650),target=(c.x,c.y))
for name in ['g6_skirt_poke.py']:
 s=p/'scripts'/name;sys.argv=[str(s),'--',str(p/'work/rig_v5t.blend'),'Walking','Running','Attack'];runpy.run_path(str(s),run_name='__main__')
