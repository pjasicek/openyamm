"""Dense deformation and anatomical wrist/sole screen on the evaluated pilot."""
from pathlib import Path
import bpy,sys,json,math
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rest=np.array([tuple(v.co) for v in me.vertices]);edges=np.array([tuple(e.vertices) for e in me.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
weights=np.zeros((len(rest),len(body.vertex_groups)));names=[g.name for g in body.vertex_groups]
for v in me.vertices:
    for g in v.groups:weights[v.index,g.group]=g.weight
masks={}
for side in 'LR':
    for tag,parts in [('arm',('UpperArm','Forearm','Hand')),('hand',('Hand','Finger'))]:
        w=weights[:,[i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(part in n for part in parts)]].sum(1)
        masks[side+'_'+tag]=(w[edges[:,0]]>.3)&(w[edges[:,1]]>.3)
soles={s:np.where((rest[:,2]<.055)&(rest[:,0]*(1 if s=='L' else -1)>0))[0] for s in 'LR'}
report={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    row={'stretch':{},'wrist_deg':{},'sole_min':1e9,'sole_max_lowest':-1e9}
    for f in np.arange(act.frame_range[0],act.frame_range[1]+.01,.5):
        bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        co=np.array([tuple(v.co) for v in mesh.vertices]);ev.to_mesh_clear()
        ratios=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-6)
        for name,mask in masks.items():
            value=float(np.percentile(ratios[mask],99)) if name.endswith('arm') else float(ratios[mask].max())
            if value>row['stretch'].get(name,[0])[0]:row['stretch'][name]=[value,float(f)]
        foot=min(float(co[ids,2].min()) for ids in soles.values());row['sole_min']=min(row['sole_min'],foot);row['sole_max_lowest']=max(row['sole_max_lowest'],foot)
        for s in 'LR':
            h=rig.pose.bones[f'B_{s}_Hand'];fa=rig.pose.bones[f'B_{s}_Forearm'];middle=rig.pose.bones[f'B_{s}_Finger2']
            fdir=(h.matrix@h.bone.matrix_local.inverted()@rig.data.bones[f'B_{s}_Finger2'].head_local)-h.head
            bend=math.degrees((h.head-fa.head).angle(fdir))
            if bend>row['wrist_deg'].get(s,[0])[0]:row['wrist_deg'][s]=[bend,float(f)]
    report[act.name]=row;print('PROBE',act.name,json.dumps(row),flush=True)
(p/'review/motion_probe.json').write_text(json.dumps(report,indent=2))
