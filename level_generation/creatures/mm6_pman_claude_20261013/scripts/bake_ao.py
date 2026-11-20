import bpy,bmesh,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
original=bpy.data.objects['Body'];parts=[]
for layer,name,head in [('UVMap','body',0),('HeadUV','head',1)]:
 mesh=original.copy();mesh.data=original.data.copy();bpy.context.scene.collection.objects.link(mesh);mesh.name='AO_'+name
 bm=bmesh.new();bm.from_mesh(mesh.data);hl=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[hl]!=head],context='FACES');bm.to_mesh(mesh.data);bm.free()
 mesh.data.uv_layers.active=mesh.data.uv_layers[layer];mesh.data.uv_layers[layer].active_render=True
 parts.append((mesh,name))
bpy.data.objects.remove(original,do_unlink=True)
for mesh,name in parts:
 sys.argv=['bake_ao','--',mesh.name,str(P/'work'/f'ao_{name}.png'),'.03','1024']
 runpy.run_path('level_generation/creatures/claude_shared/bake_creature_ao.py',run_name='__main__')
