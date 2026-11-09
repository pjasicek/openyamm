"""Measure connected fingers on the unrigged hand shells before local repair."""
from pathlib import Path
import bpy
import json
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
report={}
for name,sg in [('P03',1),('P02',-1)]:
    obj=bpy.data.objects[name]
    c=np.array([tuple(v.co) for v in obj.data.vertices])
    edges=np.array([tuple(e.vertices) for e in obj.data.edges])
    boundary=[]
    counts=np.zeros(len(edges),int)
    import bmesh
    bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
    wrist=np.mean([np.array(v.co) for v in bm.verts if any(e.is_boundary for e in v.link_edges)],axis=0)
    bm.free()
    d=np.array([sg*.20,-.25,-.947]);d/=np.linalg.norm(d);t=np.cross(d,[0,1,0])*sg;t/=np.linalg.norm(t)
    q=(c-wrist)@d;w=(c-wrist)@t
    rows=[]
    for cut in [.07,.09,.11,.13,.15,.17,.19,.21,.23]:
        ids=set(np.where(q>cut)[0].tolist());adj={i:[] for i in ids}
        for a,b in edges:
            if int(a) in ids and int(b) in ids:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
        comps=[]
        while ids:
            stack=[ids.pop()];component=[]
            while stack:
                v=stack.pop();component.append(v)
                for n in adj[v]:
                    if n in ids:ids.remove(n);stack.append(n)
            if len(component)>3:comps.append(component)
        rows.append({'cut':cut,'components':[{'verts':len(v),'mean_w':float(w[v].mean()),'qmax':float(q[v].max()),'ids':v} for v in comps]})
    report[name]={'wrist':wrist.tolist(),'direction':d.tolist(),'thumb_axis':t.tolist(),'rows':rows}
    print(name,'wrist',wrist,'q range',q.min(),q.max())
    for row in rows:print('CUT',row['cut'],[(v['verts'],round(v['mean_w'],3),round(v['qmax'],3)) for v in row['components']])
(p/'work/hand_components.json').write_text(json.dumps(report,indent=2))
