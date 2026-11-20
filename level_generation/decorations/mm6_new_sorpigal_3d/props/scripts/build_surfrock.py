"""Surf rocks `searka01` / `searkb01`: a Poly Haven scan through ../scripts/build_prop.py (props/<prop>/), plus a
foam ring at the waterline around its footprint: a flat band from just inside the rock's outline at the base to
FOAM_WIDTH outside it, at FOAM_Z, material Foam (blended, double-sided, openyamm_uv_scroll drifting it slowly round
the rock). Writes work/<prop>_export.glb. Usage: blender --background --python build_surfrock.py -- <prop> <name>"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

prop, name = sys.argv[sys.argv.index('--') + 1:]
FOAM_Z, FOAM_WIDTH, FOAM_DRIFT = 0.035, 0.45, [0.025, 0.0]
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(pl.PROPS, prop, 'work', f'{prop}_export.glb'))
rocks = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: len(o.name))
for o in rocks:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
foam = pl.material('Foam', 'foam', alpha=True, extras={'openyamm_uv_scroll': FOAM_DRIFT, 'openyamm_specular': 0.2})
# footprint: outermost vertex radius per angle among the lowest vertices of the full-detail scan
points = np.array([v.co[:] for v in rocks[0].data.vertices])
low = points[points[:, 2] < 0.18]
angles = np.arctan2(low[:, 1], low[:, 0]); radii = np.hypot(low[:, 0], low[:, 1])


def footprint(segments):
    out = []
    for k in range(segments):
        a = 2 * math.pi * k / segments
        d = np.abs((angles - a + math.pi) % (2 * math.pi) - math.pi)
        near = radii[d < math.pi / segments * 1.5]
        out.append((a, float(near.max()) if near.size else float(radii.mean())))
    return out


def ring(level, segments):
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    outline = footprint(segments)
    inner, outer = [], []
    for k, (a, r) in enumerate(outline):
        wobble = 1 + 0.12 * math.sin(a * 5 + 1.3) + 0.08 * math.sin(a * 11)
        inner.append(bm.verts.new((math.cos(a) * r * 0.94, math.sin(a) * r * 0.94, FOAM_Z)))
        outer.append(bm.verts.new((math.cos(a) * (r + FOAM_WIDTH * wobble), math.sin(a) * (r + FOAM_WIDTH * wobble),
                                   FOAM_Z - 0.01)))
    circumference = sum(r for _, r in outline) * 2 * math.pi / segments
    for k in range(segments):
        j = (k + 1) % segments
        f = bm.faces.new((inner[k], inner[j], outer[j], outer[k]))
        for loop, (u, v) in zip(f.loops, ((k, 0), (k + 1, 0), (k + 1, 1), (k, 1))):
            loop[uv].uv = (u / segments * max(1, round(circumference)), v * 0.5)
    obj = pl.to_object(f'foam{level}', bm, foam, smooth=False)
    pl.white_colour(obj)
    return obj


objects = []
for level, rock in enumerate(rocks):
    pl.white_colour(rock)                    # the scan's ambient occlusion is in its base colour
    objects.append(pl.join(name if level == 0 else f'{name}_LOD{level}', [rock, ring(level, (32, 20, 12, 8)[level])]))
    print('LEVEL', level, objects[-1].name, 'tris', pl.triangles(objects[-1]))
pl.export(objects, os.path.join(pl.PROPS, 'work', f'{prop}_export.glb'))
