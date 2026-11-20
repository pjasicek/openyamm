import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'work/round2_studs';out.mkdir(exist_ok=True)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round2_cuff/lod{level}.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['ForearmBlade'];M=rig.data.bones['ForearmBlade'].matrix_local;iv=M.inverted();co=[iv@v.co for v in ob.data.vertices];adj=[[]for _ in co]
 for e in ob.data.edges:i,j=e.vertices;adj[i].append(j);adj[j].append(i)
 todo=set(range(len(co)))
 while todo:
  part=[todo.pop()]
  for i in part:
   for j in adj[i]:
    if j in todo:todo.remove(j);part.append(j)
  ar=np.array([tuple(co[i])for i in part]);span=ar.max(0)-ar.min(0)
  if span.max()<.05 and ar[:,2].max()<.20:
   center=ar.mean(0);cx=-.043 if center[2]<.09 else -.033;delta=Vector((center[0]-cx,center[1],0)).normalized()*.026
   for i in part:ob.data.vertices[i].co=M@(co[i]+delta)
 path=out/f'lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));sel['ForearmBlade'][str(level)]['blend']=str(path.relative_to(P))
(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2))
