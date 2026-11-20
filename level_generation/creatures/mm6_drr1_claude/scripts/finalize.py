"""Export the selected reduced rig and a static native-style charred remnant."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];T=P/'textures'
selection=json.loads((P/'review/reduction/selection.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/selection['blend']))
mesh=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];sc=bpy.context.scene
# Restore the seven body-side seam triangles touched by the head-only UV selection flush.
with bpy.data.libraries.load(str(P/'work/uv_v1.blend'),link=False) as (src,dst):dst.objects=['Wyrm']
source=dst.objects[0];sm=source.data
key=lambda v:tuple(round(float(x),7) for x in v)
uvs={tuple(sorted(key(sm.vertices[v].co) for v in f.vertices)):{key(sm.vertices[v].co):sm.uv_layers.active.data[l].uv.copy() for v,l in zip(f.vertices,f.loop_indices)} for f in sm.polygons}
restored=0
for f in mesh.data.polygons:
 if f.material_index!=0:continue
 k=tuple(sorted(key(mesh.data.vertices[v].co) for v in f.vertices))
 if k not in uvs:continue
 for v,l in zip(f.vertices,f.loop_indices):
  old=uvs[k][key(mesh.data.vertices[v].co)]
  if (mesh.data.uv_layers.active.data[l].uv-old).length>1e-6:restored+=1
  mesh.data.uv_layers.active.data[l].uv=old
bpy.data.objects.remove(source,do_unlink=True)
print('RESTORED_BODY_UV_CORNERS',restored)
# Refresh packed images after the local material cleanup.
for mat in mesh.data.materials:
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE':
   path=T/Path(node.image.filepath).name
   if path.is_file():node.image.unpack(method='REMOVE') if node.image.packed_file else None;node.image.filepath=str(path);node.image.reload();node.image.pack()
rig.animation_data.action=bpy.data.actions['Dead'];sc.frame_set(1);bpy.context.view_layer.update()
remesh=bpy.data.meshes.new_from_object(mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()))
remains=bpy.data.objects.new('Wyrm_Remains',remesh);sc.collection.objects.link(remains)
co=np.array([v.co[:] for v in remesh.vertices]);center=(co.min(0)+co.max(0))/2
names={g.index:g.name for g in mesh.vertex_groups}
core=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if names[g.group] in ['Spine1','Spine2','Spine3'])>.7]
body_floor=float(np.percentile(co[core,2],20))
for v in remesh.vertices:
 v.co.x=(v.co.x-center[0])*.62;v.co.y=(v.co.y-center[1])*.4
 v.co.z=max(0,v.co.z-body_floor)*.72+.001

bpy.ops.object.select_all(action='DESELECT');remains.select_set(True);bpy.context.view_layer.objects.active=remains
m=remains.modifiers.new('CharredRemnant','DECIMATE');m.ratio=1050/len(remesh.polygons);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
mat=bpy.data.materials.new('CharredRemains');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.008,.012,.006,1);bs.inputs['Roughness'].default_value=.98;bs.inputs['Specular IOR Level'].default_value=.5;mat['openyamm_specular']=.05
remains.data.materials.clear();remains.data.materials.append(mat)
for f in remains.data.polygons:f.material_index=0
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_wyrm_remains.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_extras=True)
remains.hide_set(True);remains.hide_render=True
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_wyrm.blend'))
# Export static socket transforms from a nonsingular bind pose; clips still carry the visibility scale.
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o in (mesh,rig) or o.name.startswith('Socket_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_wyrm_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('FINAL',len(mesh.data.polygons),'remains',len(remains.data.polygons))
