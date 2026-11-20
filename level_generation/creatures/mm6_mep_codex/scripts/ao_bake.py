import bpy,runpy,sys,bmesh
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for layer,kind in [('UVMap','body'),('HeadUV','head')]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'));b=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(b.data);tag=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[tag])!=(kind=='head')],context='FACES');bm.to_mesh(b.data);bm.free();b.data.uv_layers.active=b.data.uv_layers[layer];b.data.uv_layers[layer].active_render=True
 sys.argv=['ao','--','Body',str(p/f'work/ao_{kind}.png'),'.035','1024'];runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
