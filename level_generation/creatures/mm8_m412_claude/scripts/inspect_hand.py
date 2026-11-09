from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
m=bpy.data.objects['P03'].data
(p/'work/hand_mesh.json').write_text(json.dumps({'vertices':[list(v.co) for v in m.vertices],'faces':[list(f.vertices) for f in m.polygons]}))
