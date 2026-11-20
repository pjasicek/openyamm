import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as gates
sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'work/round2_surface2';out.mkdir(exist_ok=True);report={}
pg=gates.Glb(P/'export/mm6_natf_shield.glb');pms=gates.load_meshes(pg)
for level in [3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];blade=bpy.data.objects['ForearmBlade'];me=body.data;me.calc_loop_triangles();a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);S=rig.pose.bones['LeafShield'].matrix.copy();SI=S.inverted();gn={g.index:g.name for g in body.vertex_groups};weights=[{gn[g.group]:g.weight for g in v.groups}for v in me.vertices];mats=[]
 for v in me.vertices:
  M=Matrix(((0,0,0,0),)*4)
  for g in v.groups:
   n=gn[g.group]
   if n in rig.data.bones:M+=g.weight*(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted())
  mats.append(np.array(SI@M))
 mats=np.array(mats);inv=np.linalg.inv(mats);original=np.array([tuple(v.co)for v in me.vertices]);pts=np.einsum('nij,nj->ni',mats[:,:3,:3],original)+mats[:,:3,3];mask=np.array([sum(w for n,w in row.items()if n.startswith('B_L_Hand')or n.startswith('B_L_Finger'))>.3 for row in weights]);tri=np.array([tuple(t.vertices)for t in me.loop_triangles if mask[list(t.vertices)].all()]);assert len(tri)>0
 pm=pms[level];solid=gates.Surface(pm,np.ones(len(pm.rest),bool)).build(pm.rest);gripmask=(abs(pm.rest[:,0])<.09)&(abs(pm.rest[:,1]+.26)<.021)&(abs(pm.rest[:,2]-.045)<.022);grip=gates.Surface(pm,gripmask).build(pm.rest)
 bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]);history=[]
 for iteration in range(24):
  samples=np.einsum('sk,tkj->tsj',bary,pts[tri]).reshape(-1,3);zup=samples@np.array(gates.C[:3,:3]).T;dist,_=solid.signed(zup);bad=np.flatnonzero(dist<-.0018);history.append(float(-dist.min()*1000))
  if not len(bad):break
  delta=np.zeros_like(pts);number=np.zeros(len(pts))
  for k in bad:
   hit,normal,_,distance=solid.tree.find_nearest(Vector(zup[k]));hit=np.array(hit);d=hit-zup[k];d=d/max(np.linalg.norm(d),1e-10)*(distance+.002);local=np.array(gates.C[:3,:3]).T@d
   for vi in tri[k//len(bary)]:delta[vi]+=local;number[vi]+=1
  use=number>0;pts[use]+=delta[use]/number[use,None]
  # Keep each digit seated at its closest existing surface patch.
  if iteration%3==2:
   for root in ['B_L_Hand']+[f'B_L_Finger{k}'for k in range(5)]:
    ids=np.array([i for i,row in enumerate(weights)if sum(w for n,w in row.items()if n==root or (root!='B_L_Hand'and n.startswith(root)))>.3]);hits=[grip.tree.find_nearest(Vector(np.array(gates.C[:3,:3])@pts[i]))for i in ids];j=min(range(len(ids)),key=lambda k:hits[k][3]);hit,norm,_,d=hits[j]
    if d>.0025:
     i=ids[j];q=pts[i].copy();hit=np.array(gates.C[:3,:3]).T@np.array(hit);v=hit-q;move=v/max(np.linalg.norm(v),1e-10)*(d-.0015);w=np.exp(-np.linalg.norm(pts[ids]-q,axis=1)**2/.012**2);pts[ids]+=w[:,None]*move
 new=np.einsum('nij,nj->ni',inv[:,:3,:3],pts)+inv[:,:3,3]
 for v,q in zip(me.vertices,new):v.co=q
 me.update();report[str(level)]={'hand_shift_max_mm':float(np.linalg.norm(new-original,axis=1).max()*1000),'projection_history_mm':history}
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();dest=out/f'lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
 for part in ['Body']:sel[part][str(level)]['blend']=str(dest.relative_to(P))
(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2));(P/'review/round2/far_hand_fitting.json').write_text(json.dumps(report,indent=2))
