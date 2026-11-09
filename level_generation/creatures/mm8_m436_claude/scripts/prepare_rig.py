"""Join reviewed parts, preserve provenance, and export the provisional rig upload."""
import bpy, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/anatomy_v3_parts.blend'))
import bmesh
from mathutils import Vector
scale=1.7/max(v.co.z for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices)
for o in bpy.data.objects:
 if o.type=='MESH':
  for v in o.data.vertices:v.co*=scale
for name in ['P00','P04']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 pending={e for e in bm.edges if e.is_boundary};caps=[]
 while pending:
  stack=[pending.pop()];es=set(stack)
  while stack:
   e=stack.pop()
   for v in e.verts:
    for e2 in v.link_edges:
     if e2 in pending:pending.remove(e2);es.add(e2);stack.append(e2)
  vs=set(v for e in es for v in e.verts);center=sum((v.co for v in vs),start=Vector())/len(vs)
  diameter=max((v.co-w.co).length for v in vs for w in vs)
  print('SKIN_BOUNDARY',name,len(es),tuple(center),diameter)
  assert name=='P04' or diameter<.06 or (abs(center.x)>.4 and .8<center.z<1.1 and len(es)<=6 and diameter<.08), 'Unreviewed large skin opening'
  caps.extend(bmesh.ops.holes_fill(bm,edges=list(es))['faces'])
 if caps:bmesh.ops.triangulate(bm,faces=caps)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('P')]
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    attr = o.data.attributes.new('piece', 'INT', 'POINT')
    attr.data.foreach_set('value', [int(o.name[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['P00']
bpy.ops.object.join()
body = bpy.context.object
body.name = body.data.name = 'Body'
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set(
    'vector', [c for v in body.data.vertices for c in v.co])
mat = bpy.data.materials.new('Provisional clay for rigging')
mat.use_nodes = True
im = bpy.data.images.new('Provisional_clay', width=1, height=1, alpha=True)
im.pixels = [0.55, 0.55, 0.55, 1.0]
im.pack()
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = im
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:
    body.data.uv_layers.new(name='ProvisionalUV')
for p in body.data.polygons:
    p.material_index = 0
    p.use_smooth = True
body.data.validate(verbose=True, clean_customdata=False)
assert not body.data.validate(), 'Mesh must be valid before rig upload'
assert len(body.data.vertices)>5000
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/step1.blend'))
(P / 'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P / 'export/m436_clean_v1.glb'), export_format='GLB',
    use_selection=True, export_animations=False, export_yup=True, export_extras=True)
(P / 'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:export/m436_clean_v1.glb','height_meters':1.7},indent=2)+'\n')
print('RIG_UPLOAD',len(body.data.vertices),sum(len(p.vertices)-2 for p in body.data.polygons))
