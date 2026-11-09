"""Marble pedestal `ped06`: a square stepped plinth, an octagonal drum ringed by two gold tori, an octagonal shaft with
a shallow groove down every edge, a gold ring under a square stepped capital. Proportions traced from the sprite
(194 x 430 px: capital 0.45 x the height wide, shaft 0.26) at its 150-unit height (1.84 m). Speckled grey granite
(`granite`) and the shared `gold`. Each LOD is built at its own detail. Writes work/pedestal_export.glb.
Usage: blender --background --python build_pedestal.py"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
H = 150 / 81.7
mats = {'Granite': pl.material('Granite', 'granite'), 'Gold': pl.material('Gold', 'gold')}
TILE = 0.55                         # granite texture repeat (m)


def square(name, profile, level):
    """Square frustum stack from [(half width, z fraction)] (bottom to top), faces along the axes, flat shaded."""
    corner = [(h * math.sqrt(2) * H, z * H) for h, z in profile]
    perimeter = 8 * max(h for h, _ in profile) * H
    obj = pl.lathe(name, corner, 4, mats['Granite'], u_repeat=perimeter / TILE, v_scale=1 / TILE, cap_top=True,
                   cap_bottom=False, smooth=False)
    obj.rotation_euler = (0, 0, math.pi / 4)
    return obj


def octagon(name, apothem, z0, z1, level, grooves):
    """Octagonal prism (flat faces toward the axes); with grooves each corner is a small V notch."""
    import bmesh
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    ring = []
    corner_r = apothem / math.cos(math.pi / 8)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        if grooves:
            for da, rr in ((-0.075, 1.0), (0.0, 0.93), (0.075, 1.0)):
                r = corner_r * rr if rr < 1 else apothem / math.cos(math.pi / 8 - 0.075)
                ring.append((r * math.cos(a + da), r * math.sin(a + da)))
        else:
            ring.append((corner_r * math.cos(a), corner_r * math.sin(a)))
    n = len(ring)
    lengths = [0.0]
    for i in range(n):
        x0, y0 = ring[i]; x1, y1 = ring[(i + 1) % n]
        lengths.append(lengths[-1] + math.hypot(x1 - x0, y1 - y0))
    bottom = [bm.verts.new((x, y, z0)) for x, y in ring]
    top = [bm.verts.new((x, y, z1)) for x, y in ring]
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        for loop, (li, zz) in zip(f.loops, ((i, z0), (i + 1, z0), (i + 1, z1), (i, z1))):
            loop[uv].uv = (lengths[li] / TILE, zz / TILE)
    obj = pl.to_object(name, bm, mats['Granite'], smooth=False)
    return obj


def torus(name, radius, tube, z, segments, sides):
    profile = [(radius + tube * math.cos(2 * math.pi * j / sides - math.pi / 2),
                z + tube * math.sin(2 * math.pi * j / sides - math.pi / 2)) for j in range(sides + 1)]
    return pl.lathe(name, profile, segments, mats['Gold'], u_repeat=4, v_scale=8)


def build(level):
    parts = []
    # plinth: wide slab, a narrower bevelled step and a low top step
    plinth = [(0.212, 0.0), (0.212, 0.068), (0.205, 0.075), (0.197, 0.078), (0.197, 0.128), (0.188, 0.135),
              (0.180, 0.137), (0.180, 0.152), (0.172, 0.157)]
    if level == 2:
        plinth = [(0.212, 0.0), (0.212, 0.075), (0.197, 0.078), (0.197, 0.135), (0.178, 0.157)]
    parts.append(square('plinth', plinth, level))
    # drum with two gold tori, a short taper into the shaft
    drum_a = 0.158
    parts.append(octagon('drum', drum_a * H, 0.157 * H, 0.232 * H, level, False))
    parts.append(octagon('taper', 0.138 * H, 0.232 * H, 0.250 * H, level, False))
    seg, sides = ((32, 8), (16, 5), (8, 3))[level]
    for z in (0.174, 0.212):
        parts.append(torus(f"ring{z}", 0.172 * H, 0.016 * H, z * H, seg, sides))
    # shaft
    parts.append(octagon('shaft', 0.130 * H, 0.250 * H, 0.800 * H, level, level == 0))
    parts.append(torus("ring_top", 0.139 * H, 0.015 * H, 0.810 * H, seg, sides))
    parts.append(octagon('neck', 0.136 * H, 0.800 * H, 0.822 * H, level, False))
    # capital: two steps out to the thick top slab
    capital = [(0.150, 0.822), (0.150, 0.848), (0.170, 0.852), (0.176, 0.880), (0.196, 0.884), (0.198, 0.902),
               (0.222, 0.906), (0.224, 0.990), (0.216, 1.0)]
    if level == 2:
        capital = [(0.150, 0.822), (0.170, 0.852), (0.196, 0.884), (0.222, 0.906), (0.222, 1.0)]
    parts.append(square('capital', capital, level))
    for o in parts:
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return pl.join(f'pedestal{level}', parts)


lods = []
for level in range(3):
    obj = build(level)
    occl = pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=0.3, strength=0.6)
    obj.name = 'Pedestal' if level == 0 else f'Pedestal_LOD{level}'; obj.data.name = obj.name
    print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'pedestal.blend'))
pl.export(lods, os.path.join(work, 'pedestal_export.glb'))
