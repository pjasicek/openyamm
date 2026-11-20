from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];d=json.loads((P/'work/surface_checks.json').read_text())
for name in ['Running','Death','Walking']:
 for part in ['0','1','2']:
  rat,f,edge=d['roles'][name]['piece_edge_stretch'][part];print('EDGE',name,part,rat,f)
  for i in edge:
   v=o.data.vertices[i];print(i,tuple(v.co),[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups if g.weight>.01])
