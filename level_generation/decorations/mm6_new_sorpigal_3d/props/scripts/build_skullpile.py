"""Skull pile `sklplrev`: a conical heap of yellowed, dirty skulls (the sprite: 214 x 153 units, about 2.6 x 1.9 m).
One procedural skull per detail level — a deformed sphere whose vertices sit on the features of the non-tiling
`skull` texture (u around, front at u = 0.5; v bottom to top): eye sockets and the nasal cavity pushed in as real
pits, a brow ridge and cheekbones pushed out, hollow temples, a longer, narrower lower face — is instanced in seeded
rings on a cone narrowing to a small crown, over a dark `bone` filler cone that hides the gaps. Sizes vary, and most
skulls face outward with a tilt while some lie sideways, upside down, face up or show the back of the cranium.
COLOR_0 is a strong ambient occlusion (squared, so gaps and sockets go near black) times a per-skull shade. LOD1 and
LOD2 use coarser skulls at the same placements; LOD3 is a lumpy bone mound.
Writes work/skullpile_export.glb. Usage: blender --background --python build_skullpile.py"""
import bpy, bmesh, math, os, random, sys
import numpy as np
from mathutils import Vector, Matrix, Euler, noise
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
HEIGHT = 1.87                       # 153 units at 81.7 units/m
RADIUS = 1.30                       # skull centres of the bottom ring (outer extent about 1.5 m)
SKULL = 0.42                        # mean skull length (front to back)
LAYER = 0.29
# Grid nodes (texture u around, v up) per detail level: dense across the face, so every feature has a vertex.
U_NODES = ([0, 0.14, 0.27, 0.33, 0.375, 0.418, 0.46, 0.5, 0.54, 0.582, 0.625, 0.67, 0.73, 0.86, 1.0],
           [0, 0.2, 0.33, 0.418, 0.5, 0.582, 0.67, 0.8, 1.0],
           [0, 0.25, 0.418, 0.5, 0.582, 0.75, 1.0])
V_NODES = ([0, 0.12, 0.235, 0.29, 0.345, 0.43, 0.505, 0.585, 0.665, 0.75, 0.87, 1.0],
           [0, 0.2, 0.33, 0.43, 0.585, 0.72, 1.0],
           [0, 0.35, 0.585, 0.8, 1.0])
# (u, v, u radius, v radius, radial offset): sockets and nose in, brow, cheekbones and upper jaw out, temples and
# the hollows under the cheekbones in. Centres match the painted features in make_textures.py.
FEATURES = [(0.418, 0.585, 0.065, 0.10, -0.15), (0.582, 0.585, 0.065, 0.10, -0.15),
            (0.5, 0.43, 0.05, 0.10, -0.10),
            (0.5, 0.675, 0.17, 0.05, 0.035),
            (0.375, 0.45, 0.05, 0.07, 0.045), (0.625, 0.45, 0.05, 0.07, 0.045),
            (0.5, 0.29, 0.09, 0.05, 0.02),
            (0.33, 0.6, 0.05, 0.09, -0.035), (0.67, 0.6, 0.05, 0.09, -0.035),
            (0.4, 0.33, 0.04, 0.05, -0.03), (0.6, 0.33, 0.04, 0.05, -0.03)]
mats = {'Skull': pl.material('Skull', 'skull'), 'Bone': pl.material('Bone', 'bone')}


def profile(z, top):
    """Pile radius at height z as a fraction of the base: a cone that keeps a narrow crown, like the sprite."""
    t = min(max(z / top, 0.0), 1.0)
    return 1 - 0.8 * t ** 1.05


def skull_mesh(level):
    """Unit skull (length about 1, front +y, up +z) with u around and v bottom to top."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    for v in V_NODES[level]:
        phi = math.pi * (1 - v)
        row = []
        for u in U_NODES[level]:
            theta = 2 * math.pi * u
            d = Vector((math.sin(phi) * math.sin(theta), -math.sin(phi) * math.cos(theta), math.cos(phi)))
            p = Vector((d.x * 0.36, d.y * 0.48, d.z * 0.40))
            front = max(d.y, 0.0)
            if p.z < 0:                                       # the face reaches lower than the back of the head
                p.z *= 1 + 0.45 * front
                p.x *= 1 - 0.3 * front * min(-d.z / 0.6, 1.0)
            for cu, cv, ru, rv, offset in FEATURES:
                w = 1 - ((u - cu) / ru) ** 2 - ((v - cv) / rv) ** 2
                if w > 0:
                    p += d * offset * w ** 0.7
            row.append((bm.verts.new(p), u, v))
        grid.append(row)
    for lower, upper in zip(grid, grid[1:]):
        for j in range(len(lower) - 1):
            quad = (lower[j], lower[j + 1], upper[j + 1], upper[j])
            f = bm.faces.new([q[0] for q in quad])
            for loop, (_, u, v) in zip(f.loops, quad):
                loop[uv].uv = (u, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # the poles collapse; the u seam keeps its two columns
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def pose(rng, a):
    """Rotation of a skull at angle a around the pile: mostly facing out, the rest lying every which way."""
    yaw = a - math.pi / 2 + rng.uniform(-0.6, 0.6)          # face (+y) outward, give or take
    pitch, roll = rng.uniform(-0.45, 0.5), rng.uniform(-0.4, 0.4)
    kind = rng.random()
    if kind < 0.12:
        yaw += math.pi                                         # back of the cranium out
    elif kind < 0.24:
        roll += math.copysign(math.pi / 2, rng.random() - 0.5)  # on its side
    elif kind < 0.33:
        roll += math.pi                                        # upside down
    elif kind < 0.40:
        pitch += rng.choice((-1.1, 1.1))                       # face up or down
    return Euler((pitch, roll, yaw), 'XYZ')


def placements():
    rng = random.Random(4242)
    out = []
    for i in range(6):
        z = 0.17 + i * LAYER
        r = RADIUS * profile(z, HEIGHT - 0.1)
        sizes = []
        while sum(sizes) * SKULL * 0.85 < 2 * math.pi * r:
            sizes.append(rng.uniform(0.75, 1.35))
        if len(sizes) > 1:
            sizes.pop()
        arc = 2 * math.pi / sum(sizes)
        a = rng.random() * 2 * math.pi
        for size in sizes:
            a += size * arc / 2
            rr = r + rng.uniform(-0.06, 0.05)
            pos = Vector((math.cos(a) * rr, math.sin(a) * rr, z + rng.uniform(-0.05, 0.05) + (size - 1) * 0.08))
            out.append((pos, pose(rng, a), size, rng.uniform(0.7, 1.0), rng.uniform(0.85, 1.0)))
            a += size * arc / 2
    for a in (0.3, 2.4, 4.4):                                 # the crown: three skulls around one on top
        out.append((Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, HEIGHT - SKULL * 0.75)),
                    pose(rng, a), 0.95, rng.uniform(0.7, 1.0), rng.uniform(0.85, 1.0)))
    out.append((Vector((0.02, 0.0, HEIGHT - SKULL * 0.42)), Euler((0.15, 0.0, -0.4), 'XYZ'), 1.0, 0.95, 0.95))
    return out


def instances(level, spots):
    template = pl.to_object('template', skull_mesh(level), mats['Skull'])
    parts = []
    for pos, rot, size, shade, warmth in spots:
        ob = template.copy(); ob.data = template.data.copy()
        bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = Matrix.Translation(pos) @ rot.to_matrix().to_4x4() @ Matrix.Scale(SKULL * size, 4)
        tint = ob.data.attributes.new('shade', 'FLOAT_VECTOR', 'POINT')   # not a colour layer: it is not exported
        tint.data.foreach_set('vector', np.tile([shade, shade * warmth, shade * warmth ** 2],
                                                len(ob.data.vertices)).astype(np.float32))
        parts.append(ob)
    bpy.data.objects.remove(template, do_unlink=True)
    for ob in parts:
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return parts


def mound(segments, rings, bumps, name):
    """Lumpy bone cone: the filler under the skulls (bumps 0) or the far LOD3 heap (bumps: skull-sized lumps)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    top = HEIGHT - (0.15 if bumps == 0 else 0.0)
    base = RADIUS * (0.92 if bumps == 0 else 1.12)
    for i in range(rings + 1):
        t = i / rings
        row = []
        for j in range(segments + 1):
            a = 2 * math.pi * j / segments
            r = base * profile(t, 1.0) if i < rings else 0.0     # closed at the crown
            if bumps:
                r *= 1 + bumps * noise.noise(Vector((math.cos(a) * 2.5, math.sin(a) * 2.5, t * 4.0)))
            row.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, top * t)))
        grid.append(row)
    for i in range(rings):
        for j in range(segments):
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            for loop, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                loop[uv].uv = (uu / segments * 4, vv / rings * 2)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    return pl.to_object(name, bm, mats['Bone'])


def shade(obj, power, floor):
    """COLOR_0 = occlusion^power (gaps and sockets near black) x the per-skull shade; drops the shade attribute."""
    me = obj.data
    colour = me.color_attributes['Color']
    values = np.zeros(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', values)
    values = values.reshape(-1, 4)
    tint = np.ones((len(me.vertices), 3), np.float32)
    if 'shade' in me.attributes:
        raw = np.zeros(len(me.vertices) * 3, np.float32); me.attributes['shade'].data.foreach_get('vector', raw)
        tint = raw.reshape(-1, 3)
        tint[np.all(tint == 0, axis=1)] = 1.0                   # the filler has no shade of its own
        me.attributes.remove(me.attributes['shade'])
        colour = me.color_attributes['Color']
    values[:, :3] = np.maximum(values[:, :3] ** power, floor) * tint
    colour.data.foreach_set('color', values.ravel())
    me.color_attributes.active_color = colour
    return float(values[:, 0].mean())


spots = placements()
lods = []
for level in range(4):
    if level < 3:
        parts = instances(level, spots)
        filler = mound((16, 12, 10)[level], 3, 0.0, f'filler{level}')
        skulls = pl.join(f'skulls{level}', parts + [filler])
    else:
        skulls = mound(18, 6, 0.12, 'heap')
    lo, _ = pl.bounds([skulls])
    skulls.location.z -= lo.z
    bpy.ops.object.select_all(action='DESELECT'); skulls.select_set(True)
    bpy.context.view_layer.objects.active = skulls
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pl.vertex_occlusion(skulls, rays=(32, 20, 16, 12)[level], distance=0.3, strength=1.0)
    mean = shade(skulls, 2.2, 0.02) if level < 3 else shade(skulls, 1.0, 0.0)
    if level == 3:                                              # the far mound: as dark as the heap reads on average
        me = skulls.data; c = me.color_attributes['Color']
        values = np.zeros(len(me.vertices) * 4, np.float32); c.data.foreach_get('color', values)
        values = values.reshape(-1, 4); values[:, :3] *= 0.6; c.data.foreach_set('color', values.ravel())
    skulls.name = 'SkullPile' if level == 0 else f'SkullPile_LOD{level}'; skulls.data.name = skulls.name
    print('LEVEL', level, skulls.name, 'tris', pl.triangles(skulls), 'skulls', len(spots) if level < 3 else 0,
          'skull tris', pl.triangles(parts[0]) if level < 3 else 0, 'mean colour', round(mean, 3))
    lods.append(skulls)
work = os.path.join(pl.PROPS, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'skullpile.blend'))
pl.export(lods, os.path.join(work, 'skullpile_export.glb'))
