import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for i in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'work'/f'lod_review_{i}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
 for mat in bpy.data.materials:
  if mat.node_tree:
   bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 for n,t,h in [('Standing',0,1.65),('Attack',.71875,3.4)]:
  ac=bpy.data.actions[n];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];f=t*scene.render.fps;scene.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/lod_{i}_{n}'),.72,h,views=('three_quarter',),resolution=(400,600))
