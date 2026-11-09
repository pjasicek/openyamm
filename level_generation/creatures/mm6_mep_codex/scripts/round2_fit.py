import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];report=[]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'review/round2/before/work/final_lod{level}.blend'))
 b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 old=bpy.data.actions.get('Cast')
 if old:bpy.data.actions.remove(old)
 cast=bpy.data.actions['Attack'].copy();cast.name='Cast';cast.use_fake_user=True
 piece=np.array([v.value for v in me.attributes['piece'].data]);coords=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles()
 faces=[list(t.vertices) for t in me.loop_triangles if all(piece[i]==0 for i in t.vertices) and all(abs(coords[i,0])<.235 for i in t.vertices) and coords[list(t.vertices),2].mean()<1.32]
 tree=BVHTree.FromPolygons(coords.tolist(),faces,all_triangles=True);maxshift=0.;coatpoint=None;sashpoint=None
 for i in np.flatnonzero(piece==7):
  v=me.vertices[int(i)];oldco=v.co.copy();radial=Vector((v.co.x,v.co.y-.008,0)).normalized()
  # Ray from outside finds the coat's outer wall, keeping the sash relief outside it.
  origin=v.co+radial*.35;hit,normal,face,dist=tree.ray_cast(origin,-radial,.7)
  if hit is None:hit,normal,face,dist=tree.find_nearest(v.co)
  clearance=(v.co-hit).dot(radial)
  if clearance<.008:v.co+=radial*(.008-clearance)
  if level>0:v.co+=radial*(.006 if level==1 else .009)
  loc,normal,face,dist=tree.find_nearest(v.co);ids=faces[face]
  bc=barycentric_transform(loc,*[me.vertices[j].co for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  weights=np.zeros(len(b.vertex_groups))
  for j,share in zip(ids,bc):
   for g in me.vertices[j].groups:weights[g.group]+=g.weight*max(0,share)
  weights[np.argsort(weights)[:-8]]=0;weights/=weights.sum()
  for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
  for j in np.flatnonzero(weights>1e-7):b.vertex_groups[int(j)].add([v.index],float(weights[j]),'REPLACE')
  maxshift=max(maxshift,(v.co-oldco).length)
  if sashpoint is None:sashpoint=list(v.co);coatpoint=list(loc)
 report.append({'lod':level,'sash_vertices':int((piece==7).sum()),'maximum_displacement_mm':maxshift*1000,'sash_seed':sashpoint,'coat_seed':coatpoint,'sash_bounds':[coords[piece==7].min(0).tolist(),coords[piece==7].max(0).tolist()]})
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round2_sash_lod{level}.blend'))
(P/'review/round2/sash_fit.json').write_text(json.dumps(report,indent=2));print('SASH_FIT',report)
