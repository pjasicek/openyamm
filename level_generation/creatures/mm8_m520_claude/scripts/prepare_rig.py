"""Export the selected Cyclops assembly with a provisional neutral rig-service texture."""
from pathlib import Path
import bpy,bmesh,numpy as np,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_fitted.blend'));body=bpy.data.objects['Body']
for o in bpy.data.objects:o.select_set(o is body)
bpy.context.view_layer.objects.active=body
assert body.data.attributes.get('head') and body.data.attributes.get('piece')
co=np.array([tuple(v.co) for v in body.data.vertices]);assert abs(float(np.ptp(co[:,2]))-2.4)<.02
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
body.data.materials.clear()
for f in body.data.polygons:f.material_index=0;f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('CyclopsProvisional');mat.use_nodes=True
tex=bpy.data.images.new('CyclopsProvisional',width=16,height=16);tex.generated_color=(.38,.31,.24,1);tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
report={'vertices':len(body.data.vertices),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'height_m':float(np.ptp(co[:,2])),'head_triangles':sum(len(f.vertices)-2 for f in body.data.polygons if body.data.attributes['head'].data[f.index].value)}
(p/'work/rig_upload.json').write_text(json.dumps(report,indent=2));print('RIG_UPLOAD',report)
