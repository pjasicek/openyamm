import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_draped.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
P0=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(P0),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
edges=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(P0[edges[:,0]]-P0[edges[:,1]],axis=1)
for role,f in [('Death',10),('Death',45),('Hit',3),('Walking',19)]:
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear()
    for side in 'LR':
        w=W[:,[i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(t in n for t in ['UpperArm','Forearm'])]].sum(1)
        keep=np.all((w[edges]>.3)&(pv[edges]==0),axis=1);ratios=np.linalg.norm(P[edges[:,0]]-P[edges[:,1]],axis=1)/np.maximum(length,1e-6)
        chosen=np.argsort(np.where(keep,ratios,0))[-5:]
        for ei in chosen:
            print('EDGE',role,f,side,float(ratios[ei]),[(int(i),P0[i].round(4).tolist(),[(names[j],round(float(W[i,j]),3)) for j in np.where(W[i]>.01)[0]]) for i in edges[ei]],flush=True)
    for side,target in [('R',[-.0656456,-.0258304,1.17879]),('R',[-.078699,.003763,1.1605])]:
        i=int(np.linalg.norm(P-np.array(target),axis=1).argmin());print('CONTACT_VERTEX',role,f,i,P0[i].tolist(),P[i].tolist(),[(names[j],round(float(W[i,j]),3)) for j in np.where(W[i]>.01)[0]],flush=True)
