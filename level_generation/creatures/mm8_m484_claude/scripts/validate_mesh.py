import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth.blend'))
for name in ['Body','AxeMesh']:
 m=bpy.data.objects[name].data;before=(len(m.vertices),len(m.edges),len(m.polygons));changed=m.validate(verbose=True);print('VALIDATE',name,changed,before,(len(m.vertices),len(m.edges),len(m.polygons)))
