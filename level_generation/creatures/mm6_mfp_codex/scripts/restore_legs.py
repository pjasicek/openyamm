import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
# Every action owns its translations; a newly replaced Attack must not inherit Death's cloth cage.
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);skirt={n:pb.location.copy()for n,pb in r.pose.bones.items()if n.startswith('Skirt_')}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for pb in r.pose.bones:
  if pb.name=='B_Pelvis':continue
  if pb.name.startswith('Skirt_'):
   if a.name=='Attack':pb.location=skirt[pb.name];pb.keyframe_insert('location',frame=0)
  else:pb.location=Vector();pb.keyframe_insert('location',frame=0)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Reinstate native generated upper-leg geometry: an animated hem can reveal areas hidden in standing.
with bpy.data.libraries.load(str(P/'work/rig_v1.blend'),link=False)as(src,dst):dst.objects=['Body']
patch=dst.objects[0];bpy.context.collection.objects.link(patch);patch.name='LegGeometry';patch.parent=None
for mod in list(patch.modifiers):patch.modifiers.remove(mod)
bm=bmesh.new();bm.from_mesh(patch.data);pc=bm.verts.layers.int['piece'];keep=[f for f in bm.faces if all(v[pc]==0 and .40<v.co.z<.875 for v in f.verts)];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in keep],context='FACES');bm.to_mesh(patch.data);bm.free();print('RESTORED_LEG_FACES',len(patch.data.polygons))
for o in bpy.data.objects:o.select_set(o in [b,patch])
bpy.context.view_layer.objects.active=b;bpy.ops.object.join();bm=bmesh.new();bm.from_mesh(b.data);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(b.data);bm.free()
# Preserve the already selected head UV; only the revised body is uploaded for a new UV/texture pass.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
ob=b.copy();ob.data=b.data.copy();bpy.context.collection.objects.link(ob);ob.parent=None
for mod in list(ob.modifiers):ob.modifiers.remove(mod)
ob.vertex_groups.clear();ob.data.materials.clear();mat=bpy.data.materials.new('Neutral revised body');mat.use_nodes=True;ob.data.materials.append(mat)
for f in ob.data.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'texturing/mfp_body_upload_v2.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False)
