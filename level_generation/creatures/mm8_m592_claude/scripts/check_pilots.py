"""Half-frame deformation/contact/ground gates on the actual Guardian surface."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);E=np.array([tuple(e.vertices) for e in me.edges]);L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);valid=L>1e-5;faces=[tuple(f.vertices) for f in me.polygons];piece=np.array([x.value for x in me.attributes['piece'].data]);gn=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(gn)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
def mask(sd,parts,threshold):return W[:,[i for i,n in enumerate(gn) if n.startswith('B_'+sd+'_') and any(p in n for p in parts)]].sum(1)>threshold
arms={sd:mask(sd,['Clavicle','UpperArm','Forearm','Hand','Finger'],.1) for sd in 'LR'};hands={sd:mask(sd,['Hand','Finger'],.5) for sd in 'LR'};farms={sd:mask(sd,['Forearm','Hand','Finger'],.75) for sd in 'LR'}
armedges=valid&(arms['L'][E].all(1)|arms['R'][E].all(1));handedges=valid&(hands['L'][E].all(1)|hands['R'][E].all(1));foot={sd:np.flatnonzero((co[:,2]<.12)&(abs(co[:,0])<.5)&(co[:,0]*(1 if sd=='L' else -1)>0)) for sd in 'LR'}
F=json.loads((P/'work/claws_fit.json').read_text());hard=[]
for fs in F.values():
 for f in fs:
  ids=set(f['hard_vertices']);hard.extend(i for i,e in enumerate(E) if all(int(j) in ids for j in e))
report={'method':'Half-frame evaluated surface, rigid talon edges, open-mouth skin local signed proximity; contacts require visual confirmation near boundaries.','clips':{}}
for name in ('Standing','Walking','Running','Attack'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];r={'arm_edge_p99':0,'hand_edge_max':0,'hard_claw_error':0,'wrist_swing_max':0,'wrist_twist_max':0,'contacts':{},'minimum_sole':1e3,'max_lowest_sole':-1e3,'max_rotation_step':{},'worst_frames':{}};last={}
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  bpy.context.scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();C=np.array([tuple(body.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(C[E[:,0]]-C[E[:,1]],axis=1)/np.maximum(L,1e-9)
  metrics={'arm_edge_p99':float(np.percentile(ratio[armedges],99)),'hand_edge_max':float(ratio[handedges].max()),'hard_claw_error':float(np.max(abs(ratio[hard]-1)))}
  for k,v in metrics.items():
   if v>r[k]:r[k]=v;r['worst_frames'][k]=float(f)
  soles=[float(C[foot[sd],2].min()) for sd in 'LR'];r['minimum_sole']=min(r['minimum_sole'],min(soles));r['max_lowest_sole']=max(r['max_lowest_sole'],min(soles))
  for sd in 'LR':
   sw,tw=armik.wrist_cost(rig,sd,armik.W(rig,'B_'+sd+'_Hand').to_3x3().normalized())
   for k,v in [('wrist_swing_max',sw),('wrist_twist_max',abs(tw))]:
    if v>r[k]:r[k]=v;r['worst_frames'][k]={'frame':float(f),'side':sd}
   fl=[face for face in faces if all(piece[j]==0 and not arms[sd][j] for j in face)];tree=BVHTree.FromPolygons(C.tolist(),fl)
   for idx in np.flatnonzero(farms[sd]):
    pt=Vector(C[idx]);loc,n,face,d=tree.find_nearest(pt,.06)
    if loc is not None and d>.003 and (pt-loc).dot(n)<-.8*d and d>r['contacts'].get(sd,{}).get('depth',0):r['contacts'][sd]={'depth':float(d),'frame':float(f),'vertex':int(idx),'point':list(pt)}
  for n in ('B_Head','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_Hand','B_R_Foot','B_L_Foot'):
   q=armik.W(rig,n).to_quaternion()
   if n in last:
    angle=last[n].rotation_difference(q).angle;deg=math.degrees(min(angle,2*math.pi-angle))
    if deg>r['max_rotation_step'].get(n,0):r['max_rotation_step'][n]=deg;r['worst_frames'][n]=float(f)
   last[n]=q
 report['clips'][name]=r;print('MOTION_GATE',name,r,flush=True)
(P/'review/pilot_gates.json').write_text(json.dumps(report,indent=2)+'\n');assert max(r['hard_claw_error'] for r in report['clips'].values())<.01
