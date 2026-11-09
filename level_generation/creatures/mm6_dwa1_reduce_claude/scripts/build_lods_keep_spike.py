"""tools/build_actor_lods.py with the helmet spike protected. The default LODs of the reduced body collapse the 8 cm
spike in LOD2/LOD3 (top 1.40 -> 1.32 m), and the actors regression measures the coarsest LOD (dwarf tiers 7 % short).
Every LOD's decimate modifier gets an inverted vertex group (weight 1 on the spike and its collar: z > KEEP_Z within
KEEP_R of the spike axis, Blender rest coordinates; a non-inverted group decimates only its own vertices), removed
again after the collapse. Same LOD triangle counts, every LOD 1.401 m tall.
Usage: blender -b -P build_lods_keep_spike.py -- <lod0.glb> <dst.glb> <mesh node>   (LOD_RATIOS, default 0.5,0.18,0.06)"""
import os, sys, types
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
KEEP_Z, KEEP_R, AXIS = float(os.environ.get('KEEP_Z', '1.30')), 0.04, (-0.006, 0.048)
real_apply = bpy.ops.object.modifier_apply
kept = []


def apply_with_keep(modifier):
    obj = bpy.context.view_layer.objects.active; mod = obj.modifiers[modifier]
    if mod.type == 'DECIMATE':
        ids = [v.index for v in obj.data.vertices if (w := obj.matrix_world @ v.co).z > KEEP_Z
               and (w.x - AXIS[0]) ** 2 + (w.y - AXIS[1]) ** 2 < KEEP_R ** 2]
        g = obj.vertex_groups.new(name='LOD_Keep'); g.add(ids, 1.0, 'REPLACE')
        mod.vertex_group = g.name; mod.invert_vertex_group = True; kept.append((obj.name, len(ids)))
        result = real_apply(modifier=modifier)
        obj.vertex_groups.remove(obj.vertex_groups['LOD_Keep'])
        return result
    return real_apply(modifier=modifier)


class Ops:                                    # bpy.ops with object.modifier_apply wrapped; the rest passes through
    def __getattr__(self, name):
        sub = getattr(bpy.ops, name)
        return _Object(sub) if name == 'object' else sub


class _Object:
    def __init__(self, sub): self.sub = sub
    def __getattr__(self, name): return apply_with_keep if name == 'modifier_apply' else getattr(self.sub, name)


class Bpy(types.ModuleType):
    def __getattr__(self, name): return Ops() if name == 'ops' else getattr(bpy, name)


src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
ratios = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.18,0.06').split(','))
sys.modules['bpy'] = Bpy('bpy')               # generate() imports bpy inside the function
try:
    L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=ratios)
finally:
    sys.modules['bpy'] = bpy
print('KEPT', kept)
