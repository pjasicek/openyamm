"""Repair confirmed Smart Topology faults before the rig upload; preserve source geometry."""
import bpy,bmesh,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts=[o for o in bpy.data.objects if o.type=='MESH'];fix=[]
# Meshy inferred two braids from the oblique view; the native has one centred braid.
bpy.data.objects.remove(bpy.data.objects['P02'],do_unlink=True)
braid=bpy.data.objects['P03']
for v in braid.data.vertices:v.co.x-=.055
fix.append('Removed duplicate P02 braid and centred P03 on native back midline.')
# A lone interior cheek triangle is not visible surface.
bpy.data.objects.remove(bpy.data.objects['P116'],do_unlink=True)
for part in [4,5]:
 ob=bpy.data.objects[f'P{part:02d}'];bm=bmesh.new();bm.from_mesh(ob.data)
 boundary=[e for e in bm.edges if e.is_boundary];seen=set()
 for e in boundary:
  if e in seen:continue
  stack=[e];edges=[]
  while stack:
   x=stack.pop()
   if x in seen:continue
   seen.add(x);edges.append(x)
   for v in x.verts:stack.extend(y for y in v.link_edges if y.is_boundary and y not in seen)
  vertices=set(v for x in edges for v in x.verts);c=sum((v.co for v in vertices),Vector())/len(vertices)
  print('ARM_BOUNDARY',part,len(edges),list(c))
  if c.z<1.16:
   bmesh.ops.holes_fill(bm,edges=edges,sides=0);fix.append(f'Filled accidental arm hole P{part}: {len(edges)} edges at {list(c)}')
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(ob.data);bm.free()
parts=[o for o in bpy.data.objects if o.type=='MESH']
for ob in parts:
 n=int(ob.name[1:]);a=ob.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[n]*len(ob.data.vertices));ob.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for ob in list(bpy.data.objects):
 if ob is not body:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/clean_body'),.825,1.8,views=('front','left','back'),resolution=(600,900))
(P/'review/geometry_corrections.json').write_text(json.dumps(fix,indent=2));assert len(body.data.vertices)>5000
