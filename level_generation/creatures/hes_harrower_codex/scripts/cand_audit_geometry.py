"""Full curved-blade/skin/cloth gate, including both halves and interpolated frames; no viewer capture."""
from pathlib import Path
import json,sys,math
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];step=float(a[2]) if len(a)>2 else .5
bpy.ops.wm.open_mainfile(filepath=str(Path(a[0]).resolve()))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups}
dom=[names[max(v.groups,key=lambda x:x.weight).group] if v.groups else '' for v in body.data.vertices]
BF=[tuple(f.vertices) for f in body.data.polygons]
head=[f for f in BF if all(dom[i] in ('B_Head','B_Neck','Bone_025','headfront') for i in f)]
grip=[any('Hand' in dom[i] or 'Finger' in dom[i] for i in f) for f in BF]
blades=[bpy.data.objects[p+'Blade_'+s] for p in ('Family_','Vreth_') for s in 'LR']
cloth=[o for o in bpy.data.objects if o.name.startswith(('Cloth_','Mantle_'))]
cloth_rest={o.name:np.array([list(v.co) for v in o.data.vertices]) for o in cloth}
DIRS=[Vector(v).normalized() for v in ((.0123,.0217,1),(.71,-.33,-.62),(-.55,.81,.2),(.12,-.97,.21),(-.83,-.18,-.52))]
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',c);ev.to_mesh_clear()
 return c.reshape(-1,3)@np.array(ob.matrix_world.to_3x3()).T+np.array(ob.matrix_world.translation)
def parity(tree,p):
 votes=0
 for d in DIRS:
  q=Vector(p);count=0;travel=0.
  while travel<4.:
   hit,n,fi,dist=tree.ray_cast(q,d,4.-travel)
   if hit is None:break
   count+=1;travel+=dist+1e-5;q=hit+d*1e-5
  votes+=count%2
 return votes>=3
def update(out,key,value,frame,detail=None):
 if key not in out or value>out[key]['value']:out[key]={'value':round(float(value),6),'frame':float(frame),'detail':detail}
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
report={'sample_step_frames':step,'clips':{}}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];r={};motion={s:[] for s in 'LR'}
 hand_faces={sd:[face for face in BF if all(d.startswith('B_'+sd+'_') and ('Hand' in d or 'Finger' in d) for d in [dom[i] for i in face])] for sd in 'LR'}
 other_faces={sd:[face for face in BF if all(not (dom[i].startswith('B_'+sd+'_') and any(t in dom[i] for t in ('UpperArm','Forearm','Hand','Finger'))) for i in face)] for sd in 'LR'}
 for f in np.arange(act.frame_range[0],act.frame_range[1]+1e-5,step):
  sc.frame_set(int(f),subframe=float(f-int(f)));C=coords(body);tree=BVHTree.FromPolygons(C.tolist(),BF);ht=BVHTree.FromPolygons(C.tolist(),head)
  low=int(np.argmin(C[:,2]));update(r,'body_below_floor_m',-C[low,2],f,dom[low])
  foot=[C[[i for i,d in enumerate(dom) if d in (f'B_{s}_Foot',f'B_{s}_Toe0')],2].min() for s in 'LR']
  update(r,'lowest_sole_max_m',min(foot),f);update(r,'lowest_sole_depth_m',-min(foot),f)
  for sd in 'LR':
   hands=BVHTree.FromPolygons(C.tolist(),hand_faces[sd]);other=BVHTree.FromPolygons(C.tolist(),other_faces[sd]);update(r,sd+'_hand_other_body_crossings',len(hands.overlap(other)),f)
  CT=[];CF=[];offset=0
  for ob in cloth:
   V=coords(ob);rest=cloth_rest[ob.name];edges=np.array([list(e.vertices) for e in ob.data.edges]);ratios=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)/np.maximum(np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1),1e-6)
   update(r,ob.name+'_stretch_p99',np.percentile(ratios,99),f);update(r,ob.name+'_below_floor_m',-V[:,2].min(),f)
   for i,p in enumerate(V):
    if rest[i,2]>rest[:,2].max()-.08:continue
    loc,n,fi,d=tree.find_nearest(Vector(p),.06)
    if loc is not None and d>.003 and (Vector(p)-loc).dot(n)<-.7*d and parity(tree,p):update(r,ob.name+'_inside_body_m',d,f,dom[BF[fi][0]])
   CT.extend(V.tolist());CF.extend([tuple(offset+i for i in p.vertices) for p in ob.data.polygons]);offset+=len(V)
  ctree=BVHTree.FromPolygons(CT,CF)
  for ob in blades:
   V=coords(ob);F=[tuple(p.vertices) for p in ob.data.polygons];btree=BVHTree.FromPolygons(V.tolist(),F)
   intersections=[(bi,fi) for bi,fi in btree.overlap(tree) if not grip[fi]]
   update(r,ob.name+'_body_crossings',len(intersections),f,[dom[BF[x[1]][0]] for x in intersections[:6]])
   update(r,ob.name+'_head_crossings',len(btree.overlap(ht)),f)
   update(r,ob.name+'_cloth_crossings',len(btree.overlap(ctree)),f)
   update(r,ob.name+'_below_floor_m',-V[:,2].min(),f)
   for i,p in enumerate(V):
    loc,n,fi,d=tree.find_nearest(Vector(p),.12)
    if loc is not None and not grip[fi] and d>.001 and (Vector(p)-loc).dot(n)<-.7*d and parity(tree,p):update(r,ob.name+'_inside_body_m',d,f,dom[BF[fi][0]])
   # Test full geometry against the other blade of the same assembly.
   if ob.name.endswith('_L'):
    other=bpy.data.objects[ob.name[:-1]+'R'];V2=coords(other);t2=BVHTree.FromPolygons(V2.tolist(),[tuple(p.vertices) for p in other.data.polygons]);update(r,ob.name+'_other_crossings',len(btree.overlap(t2)),f)
  for sd in 'LR':
   from mathutils import Matrix
   z=Vector(G[sd]['handle_axis_hand_local']);x=Vector(G[sd]['blade_out_hand_local']);y=z.cross(x);tu,tl=[.22,0,.36],[.22,0,-.29]
   if 'glaive' in G[sd]:x,y=Vector(G[sd]['glaive']['edge_hand_local']),Vector(G[sd]['glaive']['y_hand_local']);tu,tl=G[sd]['glaive']['tips_glaive_local']['harrower']
   B=Matrix((x,y,z)).transposed().to_4x4();B.translation=Vector(G[sd]['handle_centre_hand_local'])
   M=np.array(rig.matrix_world@rig.pose.bones['B_'+sd+'_Hand'].matrix@B)
   motion[sd].append({'time':f/30,'upper':(M@np.array([*tu,1]))[:3].tolist(),'lower':(M@np.array([*tl,1]))[:3].tolist(),'edge':M[:3,0].tolist(),'flat':M[:3,1].tolist()})
 r['edge_motion']=motion;report['clips'][act.name]=r
 print('GEOMETRY',act.name,json.dumps({k:v for k,v in r.items() if k!='edge_motion'}),flush=True)
(P/'review'/('geometry_'+a[1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
