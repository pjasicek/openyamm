import bpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'))
r=bpy.data.objects['Rig'];s=bpy.data.objects['SwordMesh'];M=r.data.bones['Sword'].matrix_local.inverted()
classes=json.loads(s['sword_classes']);ids=sorted({i for f,k in zip(s.data.polygons,classes) if k in ['blade','edge'] for i in f.vertices})
print('SWORD_INFO',len(s.data.vertices),len(s.data.polygons),sum(len(f.vertices)-2 for f in s.data.polygons),s.matrix_world[:],s.get('blade_roll_degrees'))
print('BLADE',[(i,list(M@s.data.vertices[i].co)) for i in ids])
