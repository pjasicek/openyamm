"""Fit the engine's eight weights to the original deformed surface across every action."""
from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1];blend=p/'work/rig_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rows={v.index:sorted([(e.group,e.weight) for e in v.groups if e.weight>0],key=lambda x:-x[1]) for v in body.data.vertices}
ids=[i for i,row in rows.items() if len(row)>8];names=[g.name for g in body.vertex_groups];groups=sorted({g for i in ids for g,w in rows[i]});rest={g:rig.data.bones[names[g]].matrix_local.inverted() for g in groups}
poses=[];surface=[];samples=[]
for name in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
    a=bpy.data.actions[name];rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    for f in np.arange(0,a.frame_range[1]+.001,.5):
        sc.frame_set(int(f),subframe=float(f-int(f)));poses.append({g:np.array(rig.pose.bones[names[g]].matrix@rest[g]) for g in groups});samples.append((name,float(f)))
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();surface.append(np.array([me.vertices[i].co[:] for i in ids]));ev.to_mesh_clear()
surface=np.array(surface);records=[]
def fit(A,b,indices):
    active=list(indices);weights=np.zeros(len(indices))
    while active:
        matrix=A[:,active];gram=matrix.T@matrix;rhs=matrix.T@b
        system=np.block([[gram+np.eye(len(active))*1e-9,np.ones((len(active),1))],[np.ones((1,len(active))),np.zeros((1,1))]])
        w=np.linalg.lstsq(system,np.r_[rhs,1.],rcond=None)[0][:-1]
        if w.min()>=-1e-7:
            for index,value in zip(active,w):weights[list(indices).index(index)]=max(0,value)
            weights/=weights.sum();break
        active.pop(int(np.argmin(w)))
    assert abs(weights.sum()-1)<1e-6
    error=np.linalg.norm((A[:,indices]@weights-b).reshape(-1,3),axis=1)
    return weights,float(error.max())
for j,i in enumerate(ids):
    candidate=[g for g,w in rows[i]];v=np.r_[body.data.vertices[i].co[:],1.]
    A=np.array([[pose[g]@v for g in candidate] for pose in poses])[:,:,:3].transpose(0,2,1).reshape(-1,len(candidate));target=surface[:,j].reshape(-1)
    chosen=list(range(8));weights,error=fit(A,target,chosen)
    # Rare garment vertices retain redundant spine/shoulder influences; choose the least-error eight.
    for _ in range(3):
        best=(error,chosen,weights)
        if error<.0008:break
        for old in range(8):
            for new in set(range(len(candidate)))-set(chosen):
                trial=chosen.copy();trial[old]=new;w,e=fit(A,target,trial)
                if e<best[0]:best=(e,trial,w)
        if best[0]>=error-1e-8:break
        error,chosen,weights=best
    assert error<.002,(i,error)
    for g in body.vertex_groups:g.remove([i])
    for k,w in zip(chosen,weights):
        if w>1e-8:body.vertex_groups[candidate[k]].add([i],float(w),'REPLACE')
    records.append({'vertex':i,'original_influences':len(candidate),'error_m':error})
assert max(sum(e.weight>0 for e in v.groups) for v in body.data.vertices)<=8
worst=0
for row,(name,f) in enumerate(samples):
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f))
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();after=np.array([me.vertices[i].co[:] for i in ids]);ev.to_mesh_clear()
    if ids:worst=max(worst,float(np.linalg.norm(after-surface[row],axis=1).max()))
assert worst<.002,worst
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'surface_error_budget_m':.002,'budget_reason':'At the measured native scale this is under one quarter of a source pixel; hands retain their original weights.', 'affected_vertices':len(ids),'sample_count':len(samples),'max_pose_error_m':worst,'vertices':records}
(p/'work/runtime_weights.json').write_text(json.dumps(report,indent=2)+'\n');print('RUNTIME_WEIGHTS',len(ids),worst,flush=True)
