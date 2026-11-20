"""Check moving rigid shoulder caps and reject rib-to-arm stretching."""
import bpy,json,sys,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.path.insert(0,str(P/'scripts'));import motion as M
surfaces=[]
for o in [bpy.data.objects['Body'],bpy.data.objects['Head']]:
 rest=np.array([v.co[:] for v in o.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
 mid=rest[edges].mean(1);region=(abs(mid[:,0])>.12)&(mid[:,2]>.60)&(mid[:,2]<.84)&(length>1e-6)
 caps={side:(rest[:,0]*sign>.16)&(rest[:,0]*sign<.245)&(rest[:,2]>.73)&(rest[:,2]<.81)&(rest[:,1]<.035) for side,sign in [('L',1),('R',-1)]}
 for side,mask in caps.items():
  for v in o.data.vertices:
   if mask[v.index]:assert any(o.vertex_groups[g.group].name=='UpperArm_'+side and g.weight>.9999 for g in v.groups),(o.name,side,'frozen shoulder',v.index)
 for f in o.data.polygons:
  names={o.vertex_groups[g.group].name for i in f.vertices for g in o.data.vertices[i].groups if g.weight>1e-6}
  assert not (any(n.startswith(('UpperArm_','Forearm_','Hand_')) for n in names) and names.intersection({'Chest','Waist','Neck','Head'})),(o.name,'arm-to-torso bridge',f.index)
 assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in o.data.vertices)
 surfaces.append(dict(obj=o,rest=rest,edges=edges,length=length,region=region,caps=caps))
def evaluated(s):
 o=s['obj'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=o.to_mesh();a=np.array([v.co[:] for v in me.vertices]);o.to_mesh_clear();return a
def chest_space(a):
 m=np.array(M.rig.pose.bones['Chest'].matrix.inverted());return a@m[:3,:3].T+m[:3,3]
M.pose('Standing',0)
for s in surfaces:s['standing']=chest_space(evaluated(s))
report={};cap_count={side:sum(int(s['caps'][side].sum()) for s in surfaces) for side in ['L','R']};assert min(cap_count.values())>=10
for clip,end in [('Attack',1.25),('Hit',1.125),('Fidget',.625),('Death',.25)]:
 peak=0;worst=0;rigid_error=0;travel={side:0 for side in cap_count};count=round(end*96)+1
 for t in np.linspace(0,end,count):
  M.pose('Hit' if clip=='Death' else clip,float(t));displacement={side:[] for side in cap_count}
  for s in surfaces:
   a=evaluated(s);e=s['edges'];ratio=np.linalg.norm(a[e[:,0]]-a[e[:,1]],axis=1)/np.maximum(s['length'],1e-8)
   value=float(ratio[s['region']].max()) if s['region'].any() else 0
   if value>peak:peak=value;worst=float(t)
   delta=chest_space(a)-s['standing']
   for side,mask in s['caps'].items():
    displacement[side].extend(np.sum(delta[mask]**2,axis=1))
    both=mask[e[:,0]]&mask[e[:,1]]&(s['length']>1e-6)
    if both.any():rigid_error=max(rigid_error,float(np.abs(ratio[both]-1).max()))
  for side in travel:travel[side]=max(travel[side],float(np.sqrt(np.mean(displacement[side]))))
 assert peak<2.5,(clip,peak,worst)
 assert rigid_error<1e-4,(clip,'shoulder cap deformation',rigid_error)
 minimum={'Attack':.05,'Hit':.07,'Fidget':.009,'Death':.015}[clip]
 assert min(travel.values())>minimum,(clip,'shoulders do not move',travel)
 report[clip]={'samples':count,'maximum_shoulder_edge_ratio':peak,'worst_time_s':worst,'cap_maximum_edge_ratio_error':rigid_error,'cap_chest_relative_rms_travel_m':travel}
report.update(chest_arm_shared_faces=0,rig_uv_sha256=hashlib.sha256((P/'work/rig_uv.blend').read_bytes()).hexdigest(),cap_vertices=cap_count)
(P/'work/shoulder_motion_v3/deformation_audit.json').write_text(json.dumps(report,indent=2));print('SHOULDER_MOTION_AUDIT_PASS',report,flush=True)
