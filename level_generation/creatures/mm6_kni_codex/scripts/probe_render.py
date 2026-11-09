import bpy,sys,json,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/clay.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
for name,f in [('Standing',0),('Walking',12),('Running',12),('Attack',10),('Attack',23),('Hit',6),('Death',32),('Fidget',30)]:
 ac=bpy.data.actions[name];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];scene.frame_set(f)
 common.render_views(str(P/'review'/f'probe_{name}_{f}'),1.0,2.6,views=('front','left','three_quarter'),resolution=(400,560))
