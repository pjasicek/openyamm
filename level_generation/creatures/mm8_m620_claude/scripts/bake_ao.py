"""Bake short-range occlusion on separate body/head charts using the shared creature baker."""
from pathlib import Path
import bpy,bmesh,sys,runpy
p=Path(__file__).resolve().parents[1]
for layer,suffix,want in [('UVMap','',0),('HeadUV','_head',1)]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
 b=bpy.data.objects['Body'];b.data.uv_layers.active=b.data.uv_layers[layer]
 b.data.uv_layers[layer].active_render=True
 occluder=b.copy();occluder.data=b.data.copy();bpy.context.scene.collection.objects.link(occluder)
 for mesh,keep in [(b,want),(occluder,1-want)]:
  bm=bmesh.new();bm.from_mesh(mesh.data);h=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[h]!=keep],context='FACES');bm.to_mesh(mesh.data);bm.free()
 sys.argv=['bake_creature_ao.py','--','Body',str(p/f'work/ao{suffix}.png'),'.035','1024']
 runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
