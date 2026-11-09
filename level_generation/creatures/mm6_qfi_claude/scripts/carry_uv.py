"""Carry the textured UV layers (UVMap from the body retexture, HeadUV painted by the head retexture) from the previous
master (work/anim_v4_unshifted.blend) onto the rebuilt one (work/anim_v3.blend), loop by loop: the topology is
unchanged (only the placement moved), so the paid textures still fit. Writes work/anim_v4.blend."""
import bpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v3.blend'))
me = bpy.data.objects['Queen'].data
with bpy.data.libraries.load(str(P / 'work' / 'anim_v4_unshifted.blend')) as (src, dst):
    dst.meshes = [n for n in src.meshes if n == me.name] or src.meshes[:1]
old = dst.meshes[0]
assert len(old.loops) == len(me.loops) and len(old.polygons) == len(me.polygons), 'topology changed'
for name in ('UVMap', 'HeadUV'):
    if name not in me.uv_layers:
        me.uv_layers.new(name=name)
    data = [0.0] * (2 * len(me.loops))
    old.uv_layers[name].data.foreach_get('uv', data)
    me.uv_layers[name].data.foreach_set('uv', data)
me.uv_layers.active = me.uv_layers['UVMap']
print('CARRY', len(me.loops), 'loops', [l.name for l in me.uv_layers])
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
