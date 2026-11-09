import bpy,bmesh,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_reduced.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();assert all(len(f.vertices)==3 for f in b.data.polygons)
if 'head' not in b.data.attributes:b.data.attributes.new('head','INT','FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/texture_master.blend'))
ob=b.copy();ob.data=b.data.copy();bpy.context.scene.collection.objects.link(ob);ob.parent=None
for m in list(ob.modifiers):ob.modifiers.remove(m)
ob.vertex_groups.clear();ob.data.materials.clear();mat=bpy.data.materials.new('Neutral');mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9;ob.data.materials.append(mat)
for at in list(ob.data.attributes):
 if at.name in ['piece','finger','head','orig_co']:ob.data.attributes.remove(at)
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(p/'texturing/mnk1_body_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
print('TEXTURE_UPLOAD',len(ob.data.vertices),len(ob.data.polygons))
