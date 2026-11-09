"""Clean only the observed defects; preserve original Meshy download."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
for name in ['P11']:
 bpy.data.objects.remove(parts.pop(name),do_unlink=True)
# The native hood is a black void: recess/smooth the hallucinated face inside its existing hood.
head=parts['P04']
for v in head.data.vertices:
 if v.co.z>1.40:
  v.co.y=max(v.co.y,-0.012)
  v.co.x*=0.85
bm=bmesh.new();bm.from_mesh(head.data)
for _ in range(12):bmesh.ops.smooth_vert(bm,verts=list(bm.verts),factor=0.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(head.data);bm.free()
# Keep a round-topped hood rather than the isolated sharp vertex the generator added.
hood=parts['P06']
for v in hood.data.vertices:
 if v.co.z>1.66:v.co.z=1.66+(v.co.z-1.66)*0.6
report=[]
for name,o in parts.items():
 me=o.data;piece={'P13':9,'P14':2}.get(name,int(name[1:]));me.attributes.new('piece','INT','POINT').data.foreach_set('value',[piece]*len(me.vertices))
 for face in me.polygons:face.use_smooth=True
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bnd=[e for e in bm.edges if e.is_boundary]
 report.append({'piece':piece,'vertices':len(me.vertices),'triangles':sum(len(f.vertices)-2 for f in me.polygons),'boundary_edges':len(bnd),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)})
 bm.free()
for o in bpy.data.objects:o.select_set(o.name in parts)
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
# Stitch coincident shell seams and fill only tiny accidental holes, never cuffs or garment openings.
bm=bmesh.new();bm.from_mesh(body.data);pl=bm.verts.layers.int['piece']
for piece in set(v[pl] for v in bm.verts):
 bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if v[pl]==piece],dist=0.00001)
boundaries=set(e for e in bm.edges if e.is_boundary);repairs=[]
while boundaries:
 first=boundaries.pop();edges={first};todo=list(first.verts);verts=set()
 while todo:
  v=todo.pop()
  if v in verts:continue
  verts.add(v)
  for e in v.link_edges:
   if e in boundaries:boundaries.remove(e);edges.add(e);todo.extend(e.verts)
 points=np.array([tuple(v.co) for v in verts]);extent=float(np.linalg.norm(points.max(0)-points.min(0)))
 if len(edges)<=12 and extent<0.045:
  result=bmesh.ops.holes_fill(bm,edges=list(edges),sides=12);repairs.append({'edges':len(edges),'extent_m':extent,'faces_added':len(result['faces'])})
# The generated sleeve's folded normals should remain consistently outward.
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
print('SMALL_HOLE_REPAIRS',repairs)
co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
assert np.isfinite(co).all() and len(co)>5000
# Flat provisional per-part colours satisfy Meshy's textured upload, not final production UVs/materials.
me=body.data;pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
image=bpy.data.images.new('Provisional_Only',width=8,height=1,alpha=False)
colours=[(.10,.12,.22,1),(.65,.65,.63,1),(.65,.60,.46,1),(.006,.007,.009,1),(.035,.028,.020,1),(.1,.12,.22,1),(.1,.12,.22,1),(.1,.12,.22,1)]
image.pixels=[c for rgba in colours for c in rgba];image.pack()
mat=bpy.data.materials.new('Monk_Provisional');mat.use_nodes=True;nt=mat.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=0.9;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
me.materials.clear();me.materials.append(mat);uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
for f in me.polygons:
 part=pv[f.vertices[0]];slot=1 if part in [2,3] else 2 if part in [9,10,12] else 3 if part==4 else 4 if part in [7,8] else 0
 for li in f.loop_indices:uv.data[li].uv=((slot+.5)/8,.5)
 f.material_index=0
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
(p/'work/cleanup.json').write_text(json.dumps({'removed_parts':[11],'small_hole_repairs':repairs,'face_correction':'recessed featureless hood liner; no visible face','hood_correction':'rounded extreme apex','parts':report},indent=2)+'\n')
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/clean'),.85,1.95,views=('front','left','back','three_quarter'),resolution=(700,900))
