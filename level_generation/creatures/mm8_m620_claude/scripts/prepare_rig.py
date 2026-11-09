"""Preserve native ragged garment shells and label parts before the joint-estimation upload."""
from pathlib import Path
import bpy, json, sys
import numpy as np

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts=[o for o in bpy.data.objects if o.type=='MESH']
classes={0:0,1:1,2:2,3:3,4:3,5:3,6:3,9:5,10:5,12:6,13:6,14:6,17:6}
report=[]
for o in parts:
 i=int(o.name[1:]);co=np.array([v.co[:] for v in o.data.vertices])
 # Detached hair strands and cloth tears keep their semantic owner.
 cls=classes.get(i,4 if co[:,2].min()>1.45 else (1 if co[:,2].mean()<.84 else 2))
 for name,value in [('piece',i),('region',cls)]:
  a=o.data.attributes.new(name,'INT','POINT');a.data.foreach_set('value',[value]*len(co))
 report.append({'piece':i,'region':cls,'verts':len(co),'triangles':len(o.data.polygons)})
 for f in o.data.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body';me=body.data
orig=me.attributes.new('orig_co','FLOAT_VECTOR','POINT')
for v in me.vertices:orig.data[v.index].vector=v.co
mat=bpy.data.materials.new('ProvisionalBedraggled');mat.use_nodes=True
im=bpy.data.images.new('ProvisionalPalette',width=8,height=8)
colors=[(.62,.41,.27,1),(.23,.21,.19,1),(.10,.24,.09,1),(.26,.17,.09,1),(.055,.025,.01,1),(.38,.29,.17,1),(.30,.20,.11,1),(.2,.2,.2,1)]
im.pixels=[v for row in range(8) for c in colors for v in c];im.pack()
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.clear();me.materials.append(mat)
uv=me.uv_layers.active or me.uv_layers.new(name='ProvisionalUV')
for f in me.polygons:
 f.material_index=0;r=me.attributes['region'].data[f.vertices[0]].value
 for li in f.loop_indices:uv.data[li].uv=((r+.5)/8,.5)
body.vertex_groups.clear()
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
(P/'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:work/body_for_rig.glb','height_meters':1.7},indent=2)+'\n')
(P/'work/semantic_parts.json').write_text(json.dumps(report,indent=2)+'\n')
assert set(r['region'] for r in report)==set(range(7))
print('Prepared',len(me.vertices),'vertices and',len(me.polygons),'triangles.')
