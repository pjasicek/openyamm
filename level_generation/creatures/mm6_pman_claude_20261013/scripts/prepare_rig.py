"""Preserve generated garment shells and prepare a provisional colored joint-estimation upload."""
import bpy,bmesh,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
bpy.data.objects.remove(bpy.data.objects['P13'],do_unlink=True)  # hidden 12-triangle sleeve fragment
meshes=[o for o in bpy.data.objects if o.type=='MESH']
report=[]
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data)
 boundary={e for e in bm.edges if e.is_boundary};loops=[]
 while boundary:
  e=boundary.pop();comp={e};stack=[e]
  while stack:
   a=stack.pop()
   for v in a.verts:
    for b in v.link_edges:
     if b in boundary:boundary.remove(b);comp.add(b);stack.append(b)
  vs={v for e in comp for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs)
  loops.append({'edges':len(comp),'center':list(c),'diameter':max((v.co-c).length for v in vs)*2})
 report.append({'part':o.name,'boundary_loops':loops})
 bm.free()
 attr=o.data.attributes.get('piece') or o.data.attributes.new('piece','INT','POINT')
 attr.data.foreach_set('value',[int(o.name[1:])]*len(o.data.vertices))
 for face in o.data.polygons:face.use_smooth=True
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body';me=body.data
body.vertex_groups.clear()
orig=me.attributes.new('orig_co','FLOAT_VECTOR','POINT')
for v in me.vertices:orig.data[v.index].vector=v.co
# A tiny provisional palette supports Meshy's estimator; final UVs/textures come after deformation review.
mat=bpy.data.materials.new('ProvisionalPeasant');mat.use_nodes=True
im=bpy.data.images.new('ProvisionalPalette',width=8,height=8)
colors=[(.34,.20,.11,1),(.63,.43,.23,1),(.65,.43,.28,1),(.035,.023,.018,1),(.30,.38,.65,1),(.20,.10,.05,1),(.78,.75,.69,1),(.15,.10,.08,1)]
im.pixels=[v for row in range(8) for c in colors for v in c];im.pack()
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);me.materials.clear();me.materials.append(mat)
uv=me.uv_layers.active or me.uv_layers.new(name='ProvisionalUV')
for face in me.polygons:
 face.material_index=0;part=me.attributes['piece'].data[face.vertices[0]].value
 if part==0:color=4
 elif part==1 or part in (4,5):color=2
 elif part==2:color=0
 elif part in (3,8,9):color=6
 elif part in (6,7,11):color=5
 elif part==10:color=1
 else:color=7
 for li in face.loop_indices:uv.data[li].uv=((color+.5)/8,.5)
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
(P/'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:work/body_for_rig.glb','height_meters':1.7},indent=2))
(P/'work/topology_review.json').write_text(json.dumps(report,indent=2))
expected=sum(x['tris'] for x in json.loads((P/'work/st_v1_parts.json').read_text()))
assert sum(len(f.vertices)-2 for f in me.polygons)==expected-12
print('Prepared',len(me.vertices),'vertices,',expected,'triangles; garment openings retained.')
