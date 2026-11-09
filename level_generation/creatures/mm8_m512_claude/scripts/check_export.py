"""Check actual exported quadruped skinning and subframe floor clearance with the shared GLB evaluator."""
import json
import sys
from pathlib import Path
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,sample_grid
source=Path(sys.argv[1]) if len(sys.argv)>1 else PROJECT/'export/wolf_pilot.glb'
out=Path(sys.argv[2]) if len(sys.argv)>2 else PROJECT/'work/export_checks.json'
glb=Glb(source);meshes=load_meshes(glb);report={'source':str(source),'sha256':glb.sha256,'clips':{},'failures':[]}
for name,clip,start,end in glb.clips():
    times=sample_grid(start,end,96);poses=glb.pose(clip,times);rows=[]
    for mesh in meshes:
        lows=[];stretch=[];worst={'ratio':0}
        for time,pose in zip(times,poses):
            co=mesh.posed(pose);assert np.isfinite(co).all()
            ratio=np.linalg.norm(co[mesh.edges[:,0]]-co[mesh.edges[:,1]],axis=1)/mesh.lengths
            lows.append(float(co[:,2].min()));stretch.append(float(np.percentile(ratio,99)))
            index=int(np.argmax(ratio))
            if ratio[index]>worst['ratio']:
                worst={'ratio':float(ratio[index]),'time':float(time),'edge':mesh.edges[index].tolist(),
                       'bind_positions':mesh.rest[mesh.edges[index]].tolist()}
        endpoint_error=float(np.max(np.linalg.norm(mesh.posed(poses[0])-mesh.posed(poses[-1]),axis=1)))
        row={'mesh':mesh.label,'triangles':len(mesh.faces),'min_z':min(lows),'p99_stretch':max(stretch),
             'max_stretch':worst,'endpoint_error_m':endpoint_error,'samples':len(times)}
        rows.append(row)
        if min(lows)<-.015:report['failures'].append([name,mesh.label,'floor',min(lows)])
        if max(stretch)>2.5:report['failures'].append([name,mesh.label,'p99 stretch',max(stretch)])
        if worst['ratio']>4.5:report['failures'].append([name,mesh.label,'max stretch',worst])
        if name in ['Standing','Walking','Running','Dead'] and endpoint_error>1e-5:
            report['failures'].append([name,mesh.label,'loop seam',endpoint_error])
    report['clips'][name]={'duration':float(end-start),'meshes':rows}
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source':str(source),'clips':len(report['clips']),'meshes':len(meshes),'failures':report['failures']}))
assert not report['failures'],'Exported mesh gate failed; see report'
