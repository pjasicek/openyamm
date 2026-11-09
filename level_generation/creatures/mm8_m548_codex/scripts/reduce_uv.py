"""Reduce the body while protecting the head, then unwrap the retained animated mesh."""
import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
m=bpy.data.objects['CrystalDragon'];rig=bpy.data.objects['CrystalDragonRig'];before=len(m.data.polygons)
bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bpy.context.view_layer.objects.active=m
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for v in m.data.vertices:v.select=v.co.z<.615 and v.co.y<.32
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.decimate(ratio=.34,use_symmetry=False);bpy.ops.object.mode_set(mode='OBJECT')
dec=m.modifiers.new('FinalReduction','DECIMATE');dec.ratio=.75
bpy.ops.object.modifier_apply(modifier=dec.name)
for uv in list(m.data.uv_layers):m.data.uv_layers.remove(uv)
m.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006,area_weight=0,scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=.006,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
assert all(v.groups for v in m.data.vertices)
assert len(m.data.polygons)<before and len(m.data.polygons)>3500
bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
dup=m.copy();dup.data=m.data.copy();dup.modifiers.clear();dup.parent=None;bpy.context.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/crystal_neutral.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
(P/'work/reduction.json').write_text(json.dumps({'original_triangles':before,'triangles':len(m.data.polygons),'head_and_tail_tip':'retained','body_ratio':.34,'uv_padding_fraction':.006},indent=2))
print('REDUCED',before,len(m.data.polygons),flush=True)
