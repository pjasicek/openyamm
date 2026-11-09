import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));me=bpy.data.objects['Body'].data;uvs={u.name:[v.uv[:] for v in u.data] for u in me.uv_layers};co=np.array([v.co[:] for v in me.vertices]);face=[list(f.vertices) for f in me.polygons]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));me=bpy.data.objects['Body'].data;assert np.allclose(co,np.array([v.co[:] for v in me.vertices])) and face==[list(f.vertices) for f in me.polygons]
for u in list(me.uv_layers):me.uv_layers.remove(u)
for name,values in uvs.items():
 u=me.uv_layers.new(name=name)
 for a,v in zip(u.data,values):a.uv=v
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers['UVMap'].active_render=True;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
