import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_lzd_a.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');r.name='Rig';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/export_reimport.blend'))
runpy.run_path(str(P/'scripts/round5_render_master.py'),run_name='__main__')
sys.argv=['hands','--',str(P/'review/viewer/mm6_lzd_a.glb'),str(P/'review/hands/export'),'Standing:0','Attack:0.466666667','Cast:0.489583333','Death:0.135'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
for tier in 'abc':
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/f'review/viewer/mm6_lzd_{tier}.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene,True);common.render_views(str(P/f'review/tier_{tier}'),.9,2.12,views=('front','left','three_quarter'),resolution=(600,700))

