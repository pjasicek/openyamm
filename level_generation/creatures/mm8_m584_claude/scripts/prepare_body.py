"""Remove failed feather panels, clean beak artefacts, and stage the wingless body for joint estimation."""
from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
wing={3,4,5,9,10,12,13,18,40,42,43,44};slivers={36,37,38,39,41,45,46}
for o in list(bpy.data.objects):
 if o.type=='MESH' and int(o.name[1:]) in wing|slivers:bpy.data.objects.remove(o,do_unlink=True)
colors=[(.58,.45,.32,1),(.24,.16,.09,1),(.035,.038,.042,1),(.12,.27,.08,1),(.45,.48,.49,1),(.63,.40,.12,1)]
img=bpy.data.images.new('provisional',width=len(colors),height=1,alpha=True);img.pixels[:]=[v for c in colors for v in c];img.pack()
mat=bpy.data.materials.new('Provisional');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img
bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
records=[]
for o in [o for o in bpy.data.objects if o.type=='MESH']:
 idx=int(o.name[1:]);bm=bmesh.new();bm.from_mesh(o.data)
 if idx in (20,21):
  bad=[v for v in bm.verts if v.co.y<-.17];bmesh.ops.delete(bm,geom=bad,context='VERTS')
 if idx in (0,1):
  edges=[e for e in bm.edges if e.is_boundary]
  result=bmesh.ops.holes_fill(bm,edges=edges,sides=0);bmesh.ops.triangulate(bm,faces=result['faces'])
 if idx==2:
  # Shorten the erroneously extended crow beak to the selected short native beak.
  for v in bm.verts:
   if v.co.y<-.145 and v.co.z>1.59:v.co.y=-.145+(v.co.y+.145)*.57
  # Tiny tears around the closed mouth are return artefacts; the open lower feather rim stays.
  edges=[e for e in bm.edges if e.is_boundary and all(v.co.z>1.59 for v in e.verts)]
  result=bmesh.ops.holes_fill(bm,edges=edges,sides=16);bmesh.ops.triangulate(bm,faces=result['faces'])
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for v in o.data.vertices:v.co.x+=.012;v.co.y-=.035
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[idx]*len(o.data.vertices))
 o.data.materials.clear();o.data.materials.append(mat)
 if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
 for face in o.data.polygons:
  c=face.center
  col=0 if idx in (0,1) else 1
  if idx==1 and c.z<.60:col=1
  if idx in (2,20,21):col=2
  if idx in (8,11):col=3
  if idx in (16,17,19,22,23,24,25,26,27,28,29,30,31,32,33,34,35):col=4
  if idx==2 and c.y<-.18 and c.z>1.59:col=5
  for li in face.loop_indices:o.data.uv_layers.active.data[li].uv=((col+.5)/len(colors),.5)
  face.material_index=0;face.use_smooth=True
 records.append({'piece':idx,'vertices':len(o.data.vertices),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons)})
for o in bpy.data.objects:o.select_set(o.type=='MESH')
body=bpy.data.objects['P00'];bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
(P/'work/cleanup.json').write_text(json.dumps({'discarded_wing_panels':sorted(wing),'discarded_beak_slivers':sorted(slivers),'shortened_beak':.57,'sealed_hidden_skin_ends':True,'parts':records},indent=2)+'\n')
common.workbench_clay(bpy.context.scene,True)
common.render_views(str(P/'review/clean_body'),.9,2.15,views=('front','left','back'),resolution=(650,850))
print('BODY',sum(r['triangles'] for r in records),'triangles')
