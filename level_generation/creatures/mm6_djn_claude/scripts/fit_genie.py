import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
for v in me.vertices:
 v.co.x+=.035;v.co.y-=.055
 if me.attributes['part'].data[v.index].value in [0,1,4,6,8,12] and v.co.y>.1:v.co.y=.1+(v.co.y-.1)*.64
co=np.array([v.co[:] for v in me.vertices]);part=np.array([a.value for a in me.attributes['part'].data])
# Ring centroids are measured on skin, excluding the rigid gold shells.
skin=bmesh.new();skin.from_mesh(me);skin.verts.ensure_lookup_table()
bmesh.ops.delete(skin,geom=[v for v in skin.verts if part[v.index] not in [2,3]],context='VERTS')
def ring(p,n):
 bm=skin.copy();res=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=Vector(p),plane_no=Vector(n));e=[x for x in res['geom_cut'] if isinstance(x,bmesh.types.BMEdge)];adj={}
 for x in e:
  a,b=x.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 seen=set();cs=[]
 for v in adj:
  if v in seen:continue
  todo=[v];pts=[];seen.add(v)
  while todo:
   a=todo.pop();pts.append(tuple(a.co))
   for b in adj[a]:
    if b not in seen:seen.add(b);todo.append(b)
  if len(pts)>4:cs.append(np.array(pts).mean(0))
 bm.free();return min(cs,key=lambda c:np.linalg.norm(c-p)).tolist() if cs else list(p)
J={'Pelvis':[0,0,1.11],'Spine':[0,.035,1.23],'Spine1':[0,.055,1.4],'Spine2':[0,.065,1.56],'Neck':[0,.04,1.70],'Head':[0,.005,1.80]};rows={}
for sd,s in [('L',1),('R',-1)]:
 shoulder=[s*.285,.055,1.59];elbow=[s*.49,.048,1.305];wrist=[s*.674,.01,1.036];axis=np.array(wrist)-elbow
 J[sd+'_Clavicle']=[s*.07,.05,1.605];J[sd+'_UpperArm']=shoulder
 J[sd+'_Forearm']=ring(elbow,axis);J[sd+'_Hand']=ring(wrist,axis)
 rows[sd]={'shoulder_seed':shoulder,'elbow_ring':J[sd+'_Forearm'],'wrist_ring':J[sd+'_Hand']}
# Skin ring at left wrist is occluded by the bracer but the separate hand has a clean top opening.
for sd in ['L','R']:print(sd,rows[sd])
(P/'work/joints_final.json').write_text(json.dumps({'joints':J,'ring_measurements':rows},indent=2))
np.savez(P/'work/fitted_geometry.npz',co=co,parts=part,edges=np.array([e.vertices[:] for e in me.edges]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
