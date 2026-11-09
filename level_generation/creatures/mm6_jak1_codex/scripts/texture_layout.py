import bpy,runpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['transfer','--',str(P/'work/production_body.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/textured_master.blend')];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
body=bpy.data.objects['Body'];me=body.data
with bpy.data.libraries.load(str(P/'work/head_uv_master.blend'))as(src,dst):dst.meshes=['Body']
ref=dst.meshes[0];assert len(ref.polygons)==len(me.polygons);flags=[v.value for v in ref.attributes['head'].data];me.attributes['head'].data.foreach_set('value',flags);uv=me.uv_layers.new(name='HeadUV');uv.data.foreach_set('uv',[x for v in ref.uv_layers['HeadUV'].data for x in v.uv]);me.uv_layers.active=me.uv_layers['UVMap'];bpy.data.meshes.remove(ref);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
for layer in ['UVMap','HeadUV']:
 sys.argv=['raster','--',str(P/'work/textured_master.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
# The separate AO maps stay separate from the engine's MR-red specular mask.
for layer,tag in [('UVMap','body'),('HeadUV','head')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];me=body.data;me.uv_layers.active=me.uv_layers[layer]
 # Overlapping charts belonging to the other set must not overwrite this set's bake.
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hd])!=(tag=='head')],context='FACES');bm.to_mesh(me);bm.free()
 bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=4
 sys.argv=['ao','--','Body',str(P/f'textures/jak1_{tag}_ao.png'),'.035','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
