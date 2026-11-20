import bpy,bmesh,sys,runpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
for label,layer in [('body','UVMap'),('head','HeadUV')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));body=bpy.data.objects['Body']
 for ob in bpy.data.objects:
  if ob.type=='MESH'and ob!=body:ob.hide_render=True
 bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hd])!=(label=='head')],context='FACES');bm.to_mesh(body.data);bm.free();body.data.uv_layers.active=body.data.uv_layers[layer];body.data.uv_layers.active.active_render=True
 sys.argv=['bake_creature_ao.py','--','Body',str(P/f'work/ao_{label}.png'),'.03','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
