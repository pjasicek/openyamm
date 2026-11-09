from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
for name in ['P16','P43','P44','P45','P46','P47']:
 ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
 print(name,'volume',bm.calc_volume(signed=True),'coords',[tuple(v.co) for v in ob.data.vertices] if name=='P43' else '')
 print('FACES',name,[tuple(f.vertices) for f in ob.data.polygons] if name=='P43' else '')
 bm.free()
