"""Deformation probes before production clips; assert normalized weights and finite poses."""
from pathlib import Path
import sys,json
import bpy
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import posing as Q,coordinates,render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Wyvern_Rig'];mesh=bpy.data.objects['Wyvern']
rest=coordinates(mesh);edges=np.array([list(e.vertices) for e in mesh.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
report={}
for name in ['rest','up','down','fold','neck','jaw']:
    Q.reset(rig)
    for side,s in [('L',1),('R',-1)]:
        if name in ['up','down']:
            angle=35 if name=='up' else -55
            Q.rotate_world(rig,'UpperWing_'+side,'Y',-s*angle)
            Q.rotate_world(rig,'ForeWing_'+side,'Y',-s*angle*.25)
        if name=='fold':Q.rotate_world(rig,'ForeWing_'+side,'Z',s*35)
    if name=='neck':
        for i in range(1,6):Q.rotate_world(rig,f'Neck{i}','X',-9)
        for i in range(1,10):Q.rotate_world(rig,f'Tail{i}','X',5)
    if name=='jaw':Q.rotate_world(rig,'Jaw','X',30)
    co=coordinates(mesh);assert np.isfinite(co).all()
    ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-6)
    report[name]={'edge_stretch_p99':float(np.quantile(ratio,.99)),'edge_stretch_max':float(ratio.max())}
    for view in ['front','side','quarter']:render('stress_'+name+'_'+view,view)
(P/'review/stress.json').write_text(json.dumps(report,indent=2)+'\n')
print('STRESS',report,flush=True)
