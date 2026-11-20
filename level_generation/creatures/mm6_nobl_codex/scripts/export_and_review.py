import sys,runpy,bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;common.workbench_clay(sc,True)
for role,sec in [('Standing',0),('Walking',.3),('Running',.35),('Attack',.683),('Hit',.2),('Death',.8),('Dead',0),('Fidget',1)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=sec*sc.render.fps;sc.frame_set(int(f),subframe=f%1)
 common.render_views(str(p/f'review/textured_{role}'),.85,2.15,views=('front','back','left'),resolution=(600,720))
sys.argv=['hands','--',str(p/'export/mm6_nobl_lod0.glb'),str(p/'review/hand'),'Standing:0','Walking:.2','Attack:.683','Hit:.2']
runpy.run_path(str(p/'scripts/glb_hand_closeups.py'),run_name='__main__')
