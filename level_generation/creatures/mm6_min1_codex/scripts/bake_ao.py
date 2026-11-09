import bpy,bmesh,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for part,uv in [('body','UVMap'),('head','HeadUV')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 for o in bpy.data.objects:o.hide_render=o!=b
 b.parent=None
 for m in list(b.modifiers):b.modifiers.remove(m)
 bm=bmesh.new();bm.from_mesh(b.data);layer=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[layer])!=(part=='head')],context='FACES');bm.to_mesh(b.data);bm.free();b.data.uv_layers.active=b.data.uv_layers[uv]
 for layer in list(b.data.uv_layers):layer.active_render=layer.name==uv
 bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=4
 sys.argv=['bake_creature_ao.py','--','Body',str(P/f'textures/min1_{part}_ao.png'),'.04','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
