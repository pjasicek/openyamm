import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'))
for mat,tag in zip(bpy.data.objects['Jackalman'].data.materials,['body','head','staff']):
 bs=mat.node_tree.nodes.get('Principled BSDF');normal=bs.inputs['Normal'].links[0].from_node;tex=normal.inputs['Color'].links[0].from_node;tex.image=bpy.data.images.load(str(P/'textures/rebaked'/f'{tag}_normal.png'));tex.image.colorspace_settings.name='Non-Color';sep=bs.inputs['Roughness'].links[0].from_node
 for link in list(bs.inputs['Metallic'].links):mat.node_tree.links.remove(link)
 bs.inputs['Metallic'].default_value=0;mat.node_tree.links.new(sep.outputs['Red'],bs.inputs['Specular IOR Level'])
for im in bpy.data.images:
 if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_authoring.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');sc=bpy.context.scene
def pose(name,end=False):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=a.frame_range[1] if end else a.frame_range[0];sc.frame_set(int(f),subframe=float(f-int(f)));return {p.name:p.matrix.copy()for p in rig.pose.bones}
def difference(a,b):
 return {'max_joint_distance_m':max((a[n].translation-b[n].translation).length for n in a),'max_rotation_deg':max(min(math.degrees(a[n].to_quaternion().rotation_difference(b[n].to_quaternion()).angle),360-math.degrees(a[n].to_quaternion().rotation_difference(b[n].to_quaternion()).angle))for n in a)}
report={n:difference(pose(n),pose(n,True))for n in ['Standing','Walking']};report['Death_to_Dead']=difference(pose('Death',True),pose('Dead'));assert report['Death_to_Dead']['max_joint_distance_m']<1e-5 and report['Death_to_Dead']['max_rotation_deg']<.1
(P/'review/clip_boundaries.json').write_text(json.dumps(report,indent=2));print('BOUNDARIES',report,flush=True)
for i in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'work/lod_preview_{i}.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
 for mat in bpy.data.materials:
  if mat.node_tree:
   bs=mat.node_tree.nodes.get('Principled BSDF')
   if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 common.render_views(str(P/f'review/lod{i}'),1,2.5,views=['three_quarter'],resolution=(400,550))
