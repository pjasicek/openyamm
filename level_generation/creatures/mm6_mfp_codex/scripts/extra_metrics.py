import bpy,sys,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));from cloth_volume import capped_tree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=os.environ.get('EXTRA_BLEND',str(P/'work/rig_equipped.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene;rb=r.data.bones
co=np.array([v.co[:]for v in b.data.vertices]);pv=np.array([x.value for x in b.data.attributes['piece'].data]);edges=np.array([e.vertices[:]for e in b.data.edges]);restlen=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1);faces=[f.vertices[:]for f in b.data.polygons];gn={g.index:g.name for g in b.vertex_groups}
armmask=np.array([sum(g.weight for g in v.groups if gn[g.group].startswith('B_R_')and any(s in gn[g.group]for s in ['UpperArm','Clavicle','Forearm','Hand','Finger']))>.2 for v in b.data.vertices]);emask=armmask[edges[:,0]]&armmask[edges[:,1]]&(restlen>1e-5)
K=rb['Knife'].matrix_local;local=np.array([tuple(K.inverted()@v.co)for v in k.data.vertices]);mid=local[(local[:,2]>.07)&(local[:,2]<.17)];xy=mid[:,:2];ed=np.linalg.svd(xy-xy.mean(0))[2][0]
if xy.mean(0)@ed>0:ed=-ed
edge=Vector((*ed,0));flat=Vector((-ed[1],ed[0],0));tip=Vector(local[np.argmax(local[:,2])]);A=bpy.data.actions['Attack'];r.animation_data.action=A;r.animation_data.action_slot=A.slots[0];rows=[];worst=0.;witness=None;stretch=[]
# A normal half-space alone falsely classifies points beyond reduced fingers as inside.
_,first,vertex_map=np.unique(np.round(co,5),axis=0,return_index=True,return_inverse=True)
pieces={}
for label in set(pv):
 fl=[tuple(vertex_map[list(f)])for f in faces if pv[f[0]]==label];fl=[f for f in fl if len(set(f))==len(f)];counts={}
 for face in fl:
  for i,j in zip(face,list(face[1:])+[face[0]]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
 pieces[int(label)]=(fl,[e for e,n in counts.items()if n==1])
def inside(tree,point):
 votes=0
 for direction in [Vector((.371,.619,.693)).normalized(),Vector((-.713,.533,.455)).normalized(),Vector((.251,-.918,.307)).normalized()]:
  origin=point.copy();hits=0
  for _ in range(80):
   hit,normal,face,distance=tree.ray_cast(origin,direction,3)
   if hit is None:break
   hits+=1;origin=hit+direction*1e-5
  votes+=hits%2
 return votes>=2
for f in np.linspace(0,A.frame_range[1],math.ceil(A.frame_range[1]*48/30)+1):
 sc.frame_set(int(f),subframe=float(f%1));M=r.pose.bones['Knife'].matrix;tipworld=M@tip;D=(M.to_3x3()@Vector((0,0,1))).normalized();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();rat=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)/np.maximum(restlen,1e-6);p99=float(np.percentile(rat[emask],99));stretch.append((p99,f,rat))
 rows.append({'t':float(f/30),'tip':list(tipworld),'edge':list((M.to_3x3()@edge).normalized()),'flat':list((M.to_3x3()@flat).normalized()),'axis':list(D)})
 tree=BVHTree.FromPolygons(pos.tolist(),faces);solid={}
 for i,v in enumerate(local):
  if v[2]<.025:continue
  point=M@Vector(v);hit,no,face,dist=tree.find_nearest(point,.05)
  if hit is not None and (point-hit).dot(no)<-.7*dist and dist>worst:
   label=int(pv[faces[face][0]])
   if label not in solid:solid[label]=capped_tree(pos[first],*pieces[label])
   if inside(solid[label],point):worst=dist;witness={'t':float(f/30),'vertex':i,'world':list(point),'body_face_piece':label}
for i,row in enumerate(rows):
 if i==0:continue
 v=(np.array(row['tip'])-rows[i-1]['tip'])/(row['t']-rows[i-1]['t']);s=float(np.linalg.norm(v));row.update(speed=s,forward_velocity=float(-v[1]),edge_lead=float(v@row['edge']/max(s,1e-8)),edge_share=float(abs(v@row['edge'])/max(np.hypot(v@row['edge'],v@row['flat']),1e-8)),target_alignment=float(-row['axis'][1]))
p99,f,rat=max(stretch,key=lambda x:x[0]);ids=np.flatnonzero(emask);ids=ids[np.argsort(rat[ids])[-30:]];out={'blade_edge_local':list(edge),'blade_flat_local':list(flat),'tip_local':list(tip),'blade_contact_mm':worst*1000,'blade_contact_witness':witness,'attack_samples':rows,'worst_arm_stretch':{'p99':p99,'frame':f,'edges':[{'vertices':edges[i].tolist(),'rest':co[edges[i]].tolist(),'ratio':float(rat[i])}for i in ids]}}
Path(os.environ.get('EXTRA_REPORT',str(P/'review/extra_metrics.json'))).write_text(json.dumps(out,indent=2));print('EXTRA',json.dumps({k:v for k,v in out.items()if k not in ['attack_samples','worst_arm_stretch']}));print('PEAKS',[(round(x['t'],3),round(x['speed'],2),round(x['target_alignment'],2),round(x['edge_lead'],2),round(x['edge_share'],2))for x in sorted(rows[1:],key=lambda x:-x['speed'])[:12]])
