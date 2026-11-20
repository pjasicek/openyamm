"""Inspect topology and prepare a provisional matte texture for joint estimation."""
import bpy,bmesh,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v2.blend'))
body=bpy.data.objects['Body']; me=body.data
bm=bmesh.new();bm.from_mesh(me)
report={'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'uv_layers':[x.name for x in me.uv_layers]}
bad={f for e in bm.edges if len(e.link_faces)>2 for f in e.link_faces}
report['removed_overlapping_faces']=len(bad)
bmesh.ops.delete(bm,geom=list(bad),context='FACES_ONLY')
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
boundary={e for e in bm.edges if e.is_boundary}; loops=[]
while boundary:
 start=boundary.pop(); comp={start}; stack=[start]
 while stack:
  edge=stack.pop()
  for v in edge.verts:
   for other in v.link_edges:
    if other in boundary:
     boundary.remove(other);comp.add(other);stack.append(other)
 vs={v for e in comp for v in e.verts}; centre=sum((v.co for v in vs),__import__('mathutils').Vector())/len(vs)
 diameter=max((v.co-centre).length for v in vs)*2
 loops.append({'edges':len(comp),'centre':list(centre),'diameter':diameter})
 # Inspected openings are broken fist surfaces, soles and small skull/back holes; this solid stone creature has no open garment edges.
 bmesh.ops.holes_fill(bm,edges=list(comp),sides=0)
remaining={e for e in bm.edges if e.is_boundary}; patches=[]
while remaining:
 first=next(iter(remaining)); start=first.verts[0]; current=start; edge=first; ordered=[]
 while True:
  ordered.append(current);remaining.remove(edge);current=edge.other_vert(current)
  if current==start: break
  candidates=[e for e in current.link_edges if e in remaining]
  assert len(candidates)==1,('Non-simple boundary',tuple(current.co),len(candidates))
  edge=candidates[0]
 assert len(ordered)>=3
 face=bm.faces.new(ordered); patches.append(len(ordered))
# A centre fan avoids reusing interior finger edges as cap diagonals.
for f in [f for f in bm.faces if len(f.verts)>3]:
 verts=list(f.verts); centre=bm.verts.new(f.calc_center_median());bm.faces.remove(f)
 for i,v in enumerate(verts): bm.faces.new((v,verts[(i+1)%len(verts)],centre))
report['explicit_surface_patches']=patches
report['boundary_loops']=loops
report['remaining_boundary_edges']=sum(e.is_boundary for e in bm.edges)
report['remaining_nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges)
assert report['remaining_nonmanifold_edges']==0,report
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
assert report['zero_area_faces']<20,report
for poly in me.polygons: poly.use_smooth=True
# Meshy requires a texture for rig estimation. Final appearance comes after rig/geometry review.
mat=bpy.data.materials.new('ProvisionalMatteStone');mat.use_nodes=True
image=bpy.data.images.new('ProvisionalStone',width=8,height=8)
image.generated_color=(.38,.27,.15,1);image.pack()
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.9
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
me.materials.clear();me.materials.append(mat)
if not me.uv_layers:
 me.uv_layers.new(name='ProvisionalUV')
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
(P/'work/topology_v2.json').write_text(json.dumps(report,indent=2))
(P/'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:work/body_for_rig.glb','height_meters':2.4},indent=2))
print('RIG_INPUT',report)

sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
scene=bpy.context.scene;common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.55,.56,.57,1)
common.render_views(str(P/'review/geometry_repaired'),1.2,2.7,views=('front','left','back','three_quarter'),resolution=(700,1000))
for side,x,z in [('L',.43,1.38),('R',-.40,1.27)]:
 common.render_views(str(P/f'review/fist_repaired_{side}'),z,.7,views=('front','left','back','right'),resolution=(600,600),target=(x,-.4))
