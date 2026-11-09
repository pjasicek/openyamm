from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_parts.blend'))
bm=bmesh.new();bm.from_mesh(bpy.data.objects['H00'].data)
for e in bm.edges:
 if e.is_manifold:continue
 print('HEAD_EDGE',json.dumps({'points':[list(v.co) for v in e.verts],'faces':[{'area':f.calc_area(),'normal':list(f.normal),'points':[list(v.co) for v in f.verts]} for f in e.link_faces]}),flush=True)
