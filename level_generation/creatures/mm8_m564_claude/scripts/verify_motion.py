"""Check intermediate poses, normalized skin, grounded soles and planted-hoof drift under forward travel."""
from pathlib import Path
import json
import bpy
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh=bpy.data.objects['Gorgon'];rig=bpy.data.objects['Gorgon_Rig'];sc=bpy.context.scene
rest=np.array([tuple(v.co) for v in mesh.data.vertices])
edges=np.array([tuple(e.vertices) for e in mesh.data.edges])
length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1)
keep=length>.002
soles={}
for kind in ('Front','Hind'):
    for side in 'LR':
        index=mesh.vertex_groups[f'{kind}Hoof_{side}'].index
        ids=[v.index for v in mesh.data.vertices if any(g.group==index and g.weight>.999 for g in v.groups)]
        ids=np.array(ids);bottom=rest[ids,2].min();soles[kind,side]=ids[rest[ids,2]<bottom+.004]
        assert len(soles[kind,side])>3
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 and len(v.groups)<=4 for v in mesh.data.vertices)
def evaluated():
    obj=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=obj.to_mesh()
    points=np.array([tuple(v.co) for v in data.vertices]);obj.to_mesh_clear();return points
report={}
for act in bpy.data.actions:
    rig.animation_data.action=act
    low=10;stretch=1;max_slip=0;previous={};samples=0;worst=None
    for f in np.arange(float(act.frame_range[0]),float(act.frame_range[1])+.1,.5):
        sc.frame_set(int(f),subframe=f-int(f));co=evaluated();samples+=1
        low=min(low,float(co[:,2].min()))
        ratio=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1)[keep]/length[keep]
        stretch=max(stretch,float(np.quantile(ratio,.99)))
        if act.name in ('Walking','Running'):
            period=1 if act.name=='Walking' else .75
            stride=.48 if act.name=='Walking' else .60
            duty=.62 if act.name=='Walking' else .50
            shifts={('Hind','L'):0,('Front','L'):.75,('Hind','R'):.5,('Front','R'):.25}
            if act.name=='Running':shifts={('Hind','L'):0,('Front','R'):0,('Hind','R'):.5,('Front','L'):.5}
            time=(f-1)/sc.render.fps
            for key,ids in soles.items():
                phase=(time/period+shifts[key])%1
                center=co[ids].mean(0)+np.array([0,-stride*time/period,0])
                contact=.02<phase<duty-.02
                if key in previous and contact and previous[key][0]:
                    slip=float(np.linalg.norm((center-previous[key][1])[:2]))
                    if slip>max_slip:worst={'leg':list(key),'time':float(time),'phase':float(phase),'z':float(center[2])};max_slip=slip
                previous[key]=(contact,center)
    report[act.name]={'half_frame_samples':samples,'minimum_z_m':low,'p99_edge_stretch':stretch,
                      'max_planted_hoof_drift_per_half_frame_m':max_slip,'worst_contact':worst}
(P/'work/dense_motion_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert all(v['minimum_z_m']>-.015 for v in report.values()),'Floor penetration'
assert all(v['max_planted_hoof_drift_per_half_frame_m']<.005 for v in report.values()),'Hoof skating'
