import bpy,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];s=bpy.context.scene
def use(a):
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def points():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
# Dense edge/floor audit, including in-between export samples and rigid ordinary hands.
me=body.data;rest=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);L=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);piece=np.array([v.value for v in me.attributes['piece'].data]);reports={}
for name in [a.name for a in bpy.data.actions]:
 use(bpy.data.actions[name]);end=int(bpy.data.actions[name].frame_range[1]);maxratio=np.ones(len(edges));floor=1e6;endpoint=[]
 for f in np.arange(0,end+.01,.5):
  s.frame_set(int(f),subframe=f%1);co=points();assert np.isfinite(co).all();floor=min(floor,float(co[:,2].min()));ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(L,1e-6);maxratio=np.maximum(maxratio,ratio)
  if f in (0,end):endpoint.append(co)
 assert floor>-.005,(name,floor)
 info={'samples':end*2+1,'floor_m':floor,'parts':{}}
 for part in (0,1,2,3,7,20):
  mask=(piece[edges[:,0]]==part)&(piece[edges[:,1]]==part)&(L>.0001);r=maxratio[mask];info['parts'][part]={'p99':float(np.percentile(r,99)),'max':float(r.max())}
  if part in (2,3):assert r.max()<1.001,(name,part,r.max())
 info['loop_delta_m']=float(np.linalg.norm(endpoint[-1]-endpoint[0],axis=1).max());reports[name]=info
(p/'work/final_deformation_gate.json').write_text(json.dumps(reports,indent=2));print('DEFORMATION',json.dumps(reports),flush=True)
