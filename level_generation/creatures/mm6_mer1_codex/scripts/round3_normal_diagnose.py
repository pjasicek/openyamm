"""Render the actual portable tier-A GLB, all clips and both hands, with standard glTF materials."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_mer1_a.glb'));s=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in list(bpy.data.objects):
 if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='BLENDER_EEVEE';s.world=bpy.data.worlds.new('Review world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;s.render.film_transparent=True
if hasattr(s,'eevee')and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=16
for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
 data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;o=bpy.data.objects.new('Review softbox',data);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
for mat in bpy.data.materials:
 if mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=0
# Rest/body turnarounds and true shoulder close-ups from the final portable export.
for role,t in [('Standing',0),('Attack',.4),('Death',1.3)]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*(s.render.fps/s.render.fps_base);s.frame_set(int(f),subframe=f%1)
 center=sum((rig.matrix_world@rig.pose.bones[f'B_{sd}_UpperArm'].head for sd in 'LR'),Vector())*.5
 common.render_views(str(P/'review/round3'/f'no_normal_{role}'),center.z,.9,views=('front',),target=(center.x,center.y),resolution=(800,800))
