import bpy,json
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_motion.blend'))
for name in ['Body','Axe','Shield']:
 o=bpy.data.objects[name];me=o.data
 print('MESH',name,len(me.vertices),sum(len(f.vertices)-2 for f in me.polygons),[(a.name,a.domain,a.data_type) for a in me.attributes])
 if 'piece' in me.attributes:
  pv=[x.value for x in me.attributes['piece'].data];c=Counter()
  for f in me.polygons:c[pv[f.vertices[0]]]+=len(f.vertices)-2
  print('PIECES',dict(c))
  for n in ['B_Head','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_Thigh','B_L_Calf']:
   b=bpy.data.objects['Rig'].data.bones[n];print(n,tuple(b.head_local),tuple(b.tail_local))
