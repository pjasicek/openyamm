import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));me=bpy.data.objects['Body'].data;r=bpy.data.objects['Rig']
for s,ids in [('L',[165,164,167]),('R',[673,678,677])]:
 el=r.data.bones[f'B_{s}_Forearm'].head_local;ax=(r.data.bones[f'B_{s}_Hand'].head_local-el).normalized();P=[me.vertices[i].co for i in ids];n=(P[1]-P[0]).cross(P[2]-P[0]).normalized();print('CAP',s,'normal dot',n.dot(ax),'t/r',[(round((v-el).dot(ax),4),round(((v-el)-ax*(v-el).dot(ax)).length,4)) for v in P],flush=True)
