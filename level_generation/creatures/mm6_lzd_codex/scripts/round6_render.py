import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
runpy.run_path(str(P/'scripts/round6_diagnostics.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_lzd_a.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');r.name='Rig'
a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
common.workbench_clay(scene,textured=True)
for i,t in enumerate([0,.2,.4,.6,.8]):
 f=t*30;scene.frame_set(int(f),subframe=f%1);common.render_views(str(P/f'review/master_frames/Walking_{i}'),.87,2.45,views=('front','left','three_quarter'),resolution=(440,500))
for frame in [0,5,10,13,14,15,19,24,29,34,38]:
 f=frame/48*30;scene.frame_set(int(f),subframe=f%1);common.render_views(str(P/f'review/round6/walk_{frame:02}'),.87,2.45,views=('left',),resolution=(480,560))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round6/export_reimport.blend'))
