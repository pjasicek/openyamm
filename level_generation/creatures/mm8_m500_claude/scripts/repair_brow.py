"""Replace the overlapping left-brow pockets; preserve surrounding surface and frozen maps."""
import bpy,bmesh,json,numpy as np,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
body=bpy.data.objects['Body'];me=body.data;bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
uv=bm.loops.layers.uv['UVMap'];sources=[9893,10386,10395,10396,10401,10405]
charts=[]
for i in sources:
 a,b,c=[np.array(l[uv].uv) for l in bm.faces[i].loops];ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
 charts.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
remove=[]
for f in bm.faces:
 c=f.calc_center_median()
 if c.x<-.055 and -.14<c.y<-.065 and 1.79<c.z<1.835:remove.append(f)
assert len(remove)==41,len(remove)
ids=[f.index for f in remove];affected={e for f in remove for e in f.edges};border=[e for e in affected if len([f for f in e.link_faces if f not in remove])==1]
assert len(border)==16
bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY')
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
filled=bmesh.ops.holes_fill(bm,edges=border,sides=16)['faces'];assert len(filled)==1
new=bmesh.ops.triangulate(bm,faces=filled,quad_method='BEAUTY',ngon_method='BEAUTY')['faces'];assert len(new)==14
# Give the repaired patch one continuous chart in unused head-atlas space.
occupied=np.load(P/'work/uvraster_head.npz')['piece']>=0
summed=np.pad(occupied.astype(int),((1,0),(1,0))).cumsum(0).cumsum(1);H,W=64,96
counts=summed[H:,W:]-summed[:-H,W:]-summed[H:,:-W]+summed[:-H,:-W]
candidates=np.argwhere(counts==0);y,x=next((int(y),int(x)) for y,x in candidates if y>=4 and x>=4)
verts={v for face in new for v in face.verts};points=np.array([[v.co.y,v.co.z] for v in verts]);lo,hi=points.min(0),points.max(0)
for face in new:
 face.material_index=1;face.smooth=True
 for loop in face.loops:
  q=(np.array([loop.vert.co.y,loop.vert.co.z])-lo)/(hi-lo)
  loop[uv].uv=((x+4+q[0]*88)/1024,1-(y+4+(1-q[1])*56)/1024)
pos=np.zeros((H,W,3),np.float32);coverage=np.zeros((H,W),bool)
for face in new:
 coords=np.array([v.co[:] for v in face.verts]);u=np.array([l[uv].uv[:] for l in face.loops]);u=np.column_stack([u[:,0]*1024-x,(1-u[:,1])*1024-y])
 xx,yy=np.meshgrid(np.arange(W)+.5,np.arange(H)+.5);q=np.stack([xx,yy],-1)-u[0];bary=q@np.linalg.inv(np.column_stack([u[1]-u[0],u[2]-u[0]])).T;m=(bary[...,0]>=0)&(bary[...,1]>=0)&(bary.sum(-1)<=1)
 pos[m]=coords[0]+bary[m,0,None]*(coords[1]-coords[0])+bary[m,1,None]*(coords[2]-coords[0]);coverage|=m
np.savez_compressed(P/'work/brow_texture_patch.npz',pos=pos,coverage=coverage,x=x,y=y)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
assert all(e.is_manifold for f in new for e in f.edges)
assert all(f.normal.x<-.1 for f in new),[f.normal[:] for f in new]
report={'removed_faces':ids,'new_faces':len(new),'moved_vertices':0,'uv_method':'Continuous planar chart in unused 96x64 head-atlas region; paint projected from the original surface; all other UVs unchanged.','reason':'Three inward-facing overlapping pockets above the left eye replaced with a manifold patch.'}
bm.to_mesh(me);bm.free();me.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv_brow.blend'));(P/'work/brow_repair.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
sys.path.insert(0,str(P.parents[2]/'level_generation/creatures/mm6_bar1_claude/scripts'));import common
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/brow_repaired'),1.7,.65,views=('front','right'),resolution=(600,600))
