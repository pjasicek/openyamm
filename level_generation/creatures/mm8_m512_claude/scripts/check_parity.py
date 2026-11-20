"""Compare authored vertices with the actual runtime GLB at keys and fractional frames, despite UV seam splits."""
import bpy
import json
import sys
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'export/mm8_wolf.blend'))
rig=bpy.data.objects['Wolf_Rig'];body=bpy.data.objects['Wolf'];sc=bpy.context.scene
rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.context.view_layer.update()
tree=KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(body.matrix_world@v.co,v.index)
tree.balance();glb=Glb(PROJECT/'export/mm8_wolf.glb');mesh=load_meshes(glb)[0]
mapping=[];errors=[];weight_errors=[]
source_weights=np.zeros((len(body.data.vertices),len(mesh.bone_names)))
for v in body.data.vertices:
    for g in v.groups:
        name=body.vertex_groups[g.group].name
        if name in mesh.bone_names:source_weights[v.index,mesh.bone_names.index(name)]=g.weight
source_weights/=source_weights.sum(1)[:,None]
for vi,point in enumerate(mesh.rest):
    candidates=tree.find_range(point,1e-5)
    target=np.zeros(len(mesh.bone_names))
    for j,w in zip(mesh.joints[vi],mesh.weights[vi]):target[j]+=w
    assert candidates,'Export bind surface differs from master'
    _,index,distance=min(candidates,key=lambda c:np.linalg.norm(source_weights[c[1]]-target))
    mapping.append(index);errors.append(distance);weight_errors.append(np.linalg.norm(source_weights[index]-target))
assert max(weight_errors)<1e-4,'Export changed skin weights' 
mapping=np.array(mapping)
report={'source':glb.sha256,'rest_error_m':max(errors),'clips':{},'failures':[]}
for name,clip,start,end in glb.clips():
    rig.animation_data.action=bpy.data.actions[name];rows=[]
    times=np.unique(np.r_[np.linspace(start,end,7),np.arange(start,end,1/24)+1/96])
    times=times[times<=end]
    for time,pose in zip(times,glb.pose(clip,times)):
        frame=time*24+1;sc.frame_set(int(frame),subframe=frame%1)
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        co=np.array([body.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
        distances=np.linalg.norm(co[mapping]-mesh.posed(pose),axis=1);worst=int(np.argmax(distances));error=float(distances[worst])
        rows.append({'time':float(time),'error_m':error,'key':bool(abs(time*24-round(time*24))<1e-5),'export_vertex':worst,'source_vertex':int(mapping[worst]),'bind_position':mesh.rest[worst].tolist()})
    key_error=max(r['error_m'] for r in rows if r['key']);fractional=max(r['error_m'] for r in rows)
    report['clips'][name]={'key_error_m':key_error,'subframe_error_m':fractional,'samples':len(rows),'worst':max(rows,key=lambda r:r['error_m']),'worst_key':max((r for r in rows if r['key']),key=lambda r:r['error_m'])}
    if key_error>=2e-5 or fractional>=.004:report['failures'].append([name,key_error,fractional])
(PROJECT/'work/export_parity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)

assert not report['failures'],report['failures']
