"""G3 arm joints for the goblin from the SKIN shell only (piece 0; bracers and pauldrons are separate shells that
fooled the generic ring fit), seeded by Meshy's auto-rig shoulder and hand joints.

Per side: the arm tip = the skin vertex farthest from the shoulder along the Meshy shoulder -> hand direction; a
centreline of ring centres is cut perpendicular to the LOCAL arm direction (two passes: first along the straight
seed axis, then perpendicular to the smoothed first-pass centreline). WRIST = narrowest ring between 55 % and 85 %
of the shoulder -> tip length; ELBOW = closest approach of two line fits (upper-arm rings 15-42 %, forearm rings
60-92 % of shoulder -> wrist). Ankles from the narrowest skin/foot ring above the foot.
Writes work/joints.json (Meshy joints with ring wrist/elbow/ankle replaced) and work/centrelines.json.
Args: -- <blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}


def shell(pieces):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] not in pieces], context='VERTS')
    return bm


J={k:np.array(v) for k,v in json.load(open(os.path.join(HERE,'work/joints_final.json')))['joints'].items()}
# Final wrist section: the original glove's open proximal edge, identical after our mirrored repair.
original=bpy.data.libraries.load(os.path.join(HERE,'work','st_v1_parts.blend'),link=False)
with original as (available,loaded):loaded.objects=['P04']
glove=loaded.objects[0]; gb=bmesh.new();gb.from_mesh(glove.data)
wv={v for e in gb.edges if e.is_boundary and min(v.co.z for v in e.verts)>.91 for v in e.verts}
wrist=np.array([tuple(v.co) for v in wv]).mean(0)
gb.free();bpy.data.objects.remove(glove,do_unlink=True)
for side,sg in [('R',-1),('L',1)]:
 J[f'{side}_Hand']=np.array([sg*abs(wrist[0]),wrist[1],wrist[2]])
# A greave covers the missing front of the boot shell: fit the outer cross-section of both together.
FOOT=shell({2,6,7})
def hull(points):
 pts=sorted(set(map(tuple,points)))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lower=[];upper=[]
 for pt in pts:
  while len(lower)>=2 and cross(lower[-2],lower[-1],pt)<=0:lower.pop()
  lower.append(pt)
 for pt in reversed(pts):
  while len(upper)>=2 and cross(upper[-2],upper[-1],pt)<=0:upper.pop()
  upper.append(pt)
 return np.array(lower[:-1]+upper[:-1])
ankles={}
for side,sg in [('R',-1),('L',1)]:
 best=None
 for z in [float((M['L_Foot'][2]+M['R_Foot'][2])/2)]:
  bm=FOOT.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=(0,0,1))
  points=np.array([tuple(v.co)[:2] for v in res['geom_cut'] if isinstance(v,bmesh.types.BMVert) and v.co.x*sg>.06])
  bm.free()
  if len(points)<8:continue
  h=hull(points);per=np.linalg.norm(np.roll(h,1,axis=0)-h,axis=1).sum()
  if best is None or per<best[0]:best=(per,np.r_[(h.min(0)+h.max(0))/2,z])
 assert best is not None,side
 ankles[side]=best[1];print('ANKLE_ENVELOPE',side,best)
FOOT.free()
mean_ankle=(ankles['L']+ankles['R']*np.array([-1,1,1]))/2
for side,sg in [('R',-1),('L',1)]:J[f'{side}_Foot']=mean_ankle*np.array([sg,1,1])

path=os.path.join(HERE,'work/joints_final.json')
data=json.load(open(path));data['joints']={k:v.tolist() for k,v in J.items()}
json.dump(data,open(path,'w'),indent=2)
