import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for i in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'work/lod_preview_{i}.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
 for mat in bpy.data.materials:
  if mat.node_tree:
   bs=mat.node_tree.nodes.get('Principled BSDF')
   if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 common.render_views(str(P/f'review/lod{i}'),1,2.5,views=['three_quarter'],resolution=(400,550))
