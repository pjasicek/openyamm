"""Seat coarse hand surfaces around the fixed off-hand shaft without adding triangles."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
cfg=json.loads((P/'gates.json').read_text());glb=S.Glb(P/'export/mm6_natm.glb');prop=S.load_props(cfg,P,glb,S.Report(cfg))[0];report=[];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
for level in [0,1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));C.activate('Attack',42/48);r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;me.calc_loop_triangles();before=np.array([v.co[:]for v in me.vertices]);names=[g.name for g in body.vertex_groups];ww=np.zeros((len(before),6));blend=np.zeros((len(before),4,4))
 for vertex in me.vertices:
  for gg in vertex.groups:
   n=names[gg.group]
   if n in r.data.bones:blend[vertex.index]+=gg.weight*np.array(r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted())
   if n=='B_L_Hand':ww[vertex.index,0]+=gg.weight
   for finger in range(5):
    if n.startswith(f'B_L_Finger{finger}'):ww[vertex.index,finger+1]+=gg.weight
 hand=ww.sum(1)>.2;tri=np.array([list(t.vertices)for t in me.loop_triangles if hand[list(t.vertices)].all()]);labels=[np.einsum('sk,tk->ts',bary,ww[tri,j]).ravel()>.3 for j in range(6)];to_prop=S.C@np.linalg.inv(np.array(r.pose.bones['Spear'].matrix));prop_to_world=np.linalg.inv(to_prop)[:3,:3];surface=prop['grip_surfaces']['L'][level];solid=prop['solid_surfaces'][level];weld={}
 for i,co in enumerate(before):weld.setdefault(tuple(np.round(co,6)),[]).append(i)
 rows=[]
 for iteration in range(80):
  co=np.array([v.co[:]for v in me.vertices]);posed=np.einsum('nij,nj->ni',blend[:,:3,:3],co)+blend[:,:3,3];points=np.einsum('sk,tkj->tsj',bary,posed[tri]).reshape(-1,3);local=S.transform(to_prop,points);signed,_=solid.signed(local);gaps=[surface.gap(local[mask])for mask in labels];depth=max(0,-signed.min());rows.append({'iteration':iteration,'gaps_mm':(np.array(gaps)*1000).tolist(),'depth_mm':depth*1000})
  if max(gaps)<.0022 and depth<.0022:break
  corrections=np.zeros_like(co);counts=np.zeros(len(co))
  def apply_sample(index,target):
   fi,bi=divmod(index,len(bary));delta=prop_to_world@(np.array(target)-local[index]);delta*=min(1,.003/max(np.linalg.norm(delta),1e-12));weights=bary[bi];weights=weights/max(weights@weights,1e-9)
   for vi,w in zip(tri[fi],weights):
    if w:corrections[vi]+=delta*w;counts[vi]+=1
  for index in np.flatnonzero(signed<-.0015):
   hit=solid.tree.find_nearest(Vector(local[index]));apply_sample(index,np.array(hit[0])+np.array(hit[1])*.001)
  for gap,mask in zip(gaps,labels):
   if gap<=.002:continue
   ids=np.flatnonzero(mask);hits=[surface.tree.find_nearest(Vector(local[i]))for i in ids];j=min(range(len(ids)),key=lambda j:hits[j][3]);hit=hits[j];apply_sample(int(ids[j]),np.array(hit[0])+np.array(hit[1])*.0015)
  for ids in weld.values():
   selected=[i for i in ids if counts[i]>0]
   if not selected:continue
   delta=np.mean([np.linalg.solve(blend[i,:3,:3],corrections[i]/counts[i])for i in selected],axis=0)
   for i in ids:me.vertices[i].co=Vector(co[i]+delta)
  me.update()
  if iteration%10==0:print('COARSE_GRIP_FIT',level,iteration,rows[-1],flush=True)
 after=np.array([v.co[:]for v in me.vertices]);move=np.linalg.norm(after-before,axis=1);assert move.max()<.025,(level,move.max());C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));report.append({'level':level,'moved_vertices':int((move>1e-7).sum()),'maximum_bind_move_mm':float(move.max()*1000),'fit_history':rows});print('COARSE_GRIP_RESULT',level,report[-1]['maximum_bind_move_mm'],rows[-1],flush=True)
(P/'review/round3_coarse_grip_fit.json').write_text(json.dumps(report,indent=2))
