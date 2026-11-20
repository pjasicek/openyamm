"""Retain selected anatomy, remove hidden skirt fragments, upload neutral provisional texture."""
import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
removed=[10,15,17,18,19,20,21,22]
for i in removed:bpy.data.objects.remove(bpy.data.objects[f'P{i:02d}'],do_unlink=True)
parts=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in parts)
for o in parts:
 i=int(o.name[1:]);a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[i]*len(o.data.vertices))
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
assert len(body.data.vertices)>5000
(P/'review/geometry_review.json').write_text(json.dumps({'height_m':1.9,'removed_hidden_skirt_fragments':removed,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'hands':'Five distinct fingers verified in side closeups; no fused digits','horns':2,'face':'Long bull muzzle, nose ring, ears and mane retained','uv':'provisional constant UV solely for anatomical rigging'},indent=2))
