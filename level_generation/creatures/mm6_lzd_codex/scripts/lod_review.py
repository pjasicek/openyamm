"""Build shared geometry LODs and final local review images in one bounded Blender process."""
import sys,runpy,bpy,json
sys.dont_write_bytecode=True
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'));import build_actor_lods
runpy.run_path(str(P/'scripts/render_master.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/ranged_gate.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True)
build_actor_lods.generate(P/'export/mm6_lzd_lod0.glb',P/'export/mm6_lzd_lods.glb','Lizard')
sys.argv=['g4','--',str(P/'work/export_reimport.blend'),'final','Standing:0','Walking:12','Running:12','Attack:19','Attack:22','Attack:24','Cast:15','Cast:20','Cast:24','Hit:8','Death:10','Death:15','Dead:0','Fidget:8'];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
sys.argv=['hands','--',str(P/'export/mm6_lzd_lod0.glb'),str(P/'review/hands/export'),'Standing:0','Attack:0.7','Cast:0.667708','Death:0.27'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
sys.path.insert(0,str(P/'scripts'));import common
for tier in ['a','b','c']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'review/viewer/mm6_lzd_{tier}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/f'review/tier_{tier}'),.9,2.12,views=('front','left','three_quarter'),resolution=(600,700))
