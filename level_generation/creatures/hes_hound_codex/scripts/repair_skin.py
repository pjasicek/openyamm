"""Remove duplicate repair faces, preserve the returned UVs, and inspect jaw ownership."""
import bpy
import bmesh
import json
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'claude_shared/gates'))
sys.path.insert(0,str(PROJECT/'scripts'))
from run_gates import Glb,load_meshes
import common as C
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_uv.blend'))
body=bpy.data.objects['Hound']
rig=bpy.data.objects['Hound_Rig']
g=Glb(PROJECT/'meshy/body_texture_v1/model_urls_glb.glb')
m=load_meshes(g)[0]
prim=g.doc['meshes'][m.index]['primitives'][0]
returned_uv=g.accessor(prim['attributes']['TEXCOORD_0'])[m.faces].copy()
returned_uv[:,:,1]=1-returned_uv[:,:,1]
a=np.array([v.co[:] for v in body.data.vertices])
b=m.rest
scale=np.ptp(a,axis=0).max()/np.ptp(b,axis=0).max()
b=(b-(b.min(0)+b.max(0))/2)*scale+(a.min(0)+a.max(0))/2
tri=b[m.faces]
tree=KDTree(len(tri))
for i,c in enumerate(tri.mean(1)): tree.insert(Vector(c),i)
tree.balance()
bm=bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
uv=bm.loops.layers.uv.active
remove=[]
kept=set()
errors=[]
for f in bm.faces:
    co=np.array([v.co[:] for v in f.verts])
    _,i,d=tree.find(Vector(co.mean(0)))
    if len(co)!=3 or f.calc_area()<1e-12:
        remove.append(f)
        continue
    order=np.linalg.norm(co[:,None,:]-tri[i][None,:,:],axis=-1).argmin(1)
    u=np.array([l[uv].uv[:] for l in f.loops])
    err=np.max(abs(u-returned_uv[i][order]))
    if err>1e-5:
        assert d<1e-5,'Unexpected geometry difference'
        remove.append(f)
        continue
    assert i not in kept, 'More than one retained face maps to a returned face'
    kept.add(i)
    errors.append(float(np.linalg.norm(co-tri[i][order],axis=-1).max()))
assert len(kept)==len(tri) and len(remove)==6,(len(kept),len(tri),len(remove))
bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.to_mesh(body.data)
bm.free()
assert not body.data.validate(verbose=True),'Unexpected remaining mesh repair'
report={'removed_duplicate_or_degenerate_faces':6,'retained_triangles':len(tri),
        'max_geometry_error_m':max(errors),'max_uv_error':0,'maps_only_transfer':True}
(PROJECT/'work/texture_correspondence.json').write_text(json.dumps(report,indent=2)+'\n')
group=body.vertex_groups['Jaw'].index
jaw=[v for v in body.data.vertices if sum(w.weight for w in v.groups if w.group==group)>.3]
print('JAW vertices',len(jaw),flush=True)
for y0,y1 in [(-1.23,-1.17),(-1.17,-1.10),(-1.10,-1.04),(-1.04,-.98)]:
    pts=np.array([v.co[:] for v in body.data.vertices if y0<v.co.y<y1])
    j=np.array([v.co[:] for v in jaw if y0<v.co.y<y1])
    print('SLICE',y0,y1,len(pts),'z',np.percentile(pts[:,2],[0,10,25,50,75,90,100]),
          'jaw',len(j),j.min(0).tolist() if len(j) else None,j.max(0).tolist() if len(j) else None,flush=True)
body.data.calc_loop_triangles()
adj=[[] for _ in body.data.vertices]
for edge in body.data.edges:
    a,b=edge.vertices
    adj[a].append(b);adj[b].append(a)
seen=set();components=[]
for start in range(len(adj)):
    if start in seen: continue
    part=[start];seen.add(start)
    for a in part:
        for b in adj[a]:
            if b not in seen:seen.add(b);part.append(b)
    components.append(part)
components.sort(key=len,reverse=True)
classes=np.zeros(len(body.data.vertices),dtype=np.int32)
for part in components[1:]:
    co=np.array([body.data.vertices[i].co[:] for i in part]);center=co.mean(0)
    if center[1]<-1.03 and center[2]<.83: classes[part]=1
    elif center[2]<.10: classes[part]=2
    elif center[1]<-.90 and center[2]>.82: classes[part]=3
print('ANATOMICAL_CLASSES',dict(zip(*np.unique(classes,return_counts=True))),flush=True)
u=body.data.uv_layers.active.data
np.savez(PROJECT/'work/uv3d.npz',
 uv=np.array([[tuple(u[l].uv) for l in t.loops] for t in body.data.loop_triangles],dtype=np.float32),
 xyz=np.array([[tuple(body.data.vertices[v].co) for v in t.vertices] for t in body.data.loop_triangles],dtype=np.float32),
 part=np.array([classes[t.vertices[0]] for t in body.data.loop_triangles],dtype=np.int32))
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/rig_uv_clean.blend'))
C.render_ortho((3,-1.05,.82),(0,-1.05,.82),.65,str(PROJECT/'review/jaw_rest.png'),res=(1000,800),show=['Hound'])
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
