"""User-requested independent wings, body and head texture domains; preserve the accepted head UVs."""
import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in bpy.data.actions:a.use_fake_user=True
assert len(bpy.data.actions)==9,[a.name for a in bpy.data.actions]
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=body.data;m=bpy.data.materials.new('HarpyWings');m.use_nodes=True;me.materials.append(m);pa=[v.value for v in me.attributes['part'].data]
for f in me.polygons:
 if pa[f.vertices[0]] in [1,10]:f.material_index=2
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/three_sets.blend'))
for label in ['torso','wings']:
 obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();bpy.context.collection.objects.link(obj);bm=bmesh.new();bm.from_mesh(obj.data)
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f.material_index==2)!=(label=='wings')],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;obj.data.materials.append(m)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(P/'texturing'/f'hrp_{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
 print('UPLOAD',label,len(obj.data.polygons));bpy.data.objects.remove(obj,do_unlink=True)
