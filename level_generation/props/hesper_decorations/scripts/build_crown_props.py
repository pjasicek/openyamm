"""Build the Crown's new props (hes_out4; hard-surface, Blender) into work/hard_surface/.

    blender --background --factory-startup --python scripts/build_crown_props.py [-- <name> ...]

Designs: design/kreegan_world/zone4/THE_CROWN.md sections 12 and 14, KITS.md ("The Crown's large models", "Light
fixtures"); concepts z4_03, z4_04, z4_06, z4_08 and z4_10. Built with the shared hard-surface kit
(build_hard_surface.py: materials, UV density, export), with the zone 4 texture sets added (K9 Lattice, K10 palace,
K5 grafted). Models in metres, origin at the foot (the base's centre), the front along -y (glTF +z).

  hes_ion_cannon, _dark      the Ancient ion cannon on a bastion: white-gold barrel on a yoke, black resin roots
  hes_great_cannon, _dark, _c1.._c5
                             the one great cannon on the Crownspire's dome (concepts/monsters/ion_cannon.png): a 50 m
                             head on a yoke 20 m across; rest, dark and the five wind-up stages of its glow zones
  hes_node_mast, _off        a ceramic capacitor mast with two prongs and a violet-white arc (off: no arc)
  hes_glyph_plate            a black resin slab, its front `hkglyph` fitted once
  hes_grafting_frame         resin arches holding a captured Ancient capacitor cell
  hes_membrane_banner        a bone pole, cross-bar and a violet membrane banner (`hpbanner` fitted once)
  hes_cable_spool            a Lattice cable spool on a resin cradle
  hes_trophy_pile            broken Ancient plates, a ceramic helmet on a bone stake, gold rings
  hes_pen_post               a cage pen's collar post: resin post, gilded cap, resin chains, a glowing collar
  hes_crawler_wreck          a scorched Ancient crawler hull broken open on its front (a locker stands inside)
  hes_fire_bowl_gilded       a polished resin fire bowl on gilded claws, an ember bed (the flame is a light)
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hard_surface as hs  # noqa: E402
from build_hard_surface import cube, faceted_rock, lathe, round_cylinder  # noqa: E402

K9 = os.path.join(hs.ART, 'textures_k9_lattice', 'masters')
K10 = os.path.join(hs.ART, 'textures_k10_palace', 'masters')
K5 = os.path.join(hs.ART, 'textures_k5_grafted', 'masters')
hs.TEXTURES.update({
    **{name: os.path.join(K9, name + '.png') for name in ['hocannon', 'hntrim', 'hnresin', 'hncapac', 'hnstrip']},
    **{name: os.path.join(K10, name + '.png') for name in ['homast', 'hpbanner']},
    'hkglyph': os.path.join(K5, 'hkglyph.png'),
    'hlscorch': os.path.join(hs.DERIVED, 'hlscorch.png'),
})
hs.MATERIALS.update({
    'cannon': ('hocannon', 0.45, 0.0, 1.0),          # white ceramic panels in a gold-and-resin lattice
    'gold_band': ('hntrim', 0.35, 0.85, 1.0),        # the Lattice's gold band (rings, bands, hubs)
    'nresin': ('hnresin', 0.35, 0.0, 1.2),           # Kreegan resin with violet veins (K9)
    'presin': ('hnresin', 0.15, 0.0, 0.8),           # the palace's polished resin
    'capac': ('hncapac', 0.45, 0.0, 0.8),            # white ceramic ringed with thin gold lines
    'mast': ('homast', 0.45, 0.0, 0.8),              # white ceramic, gold bands, dark slots
    'cable': ('hnstrip', 0.5, 0.2, 1.0),             # dark cable with a violet line (wound: the line runs round)
    'bone': ('hoterm', 0.5, 0.0, 0.8),
    'banner': ('hpbanner', 0.85, 0.0, 0.6),          # fitted once (fit_faces)
    'glyph': ('hkglyph', 0.4, 0.0, 1.2),             # fitted once (fit_faces)
    'membrane': ('flat_52_24_66', 0.8, 0.0, 0.0),    # the banner's edges
    'scorch': ('hlscorch', 0.85, 0.1, 1.2),          # the hull, burnt
    'coal': ('flat_26_20_22', 0.9, 0.0, 0.0),
    # Glowing (constant emissive colour): the cannon's emitter, the masts' arc, the embers, the collar.
    'emitter': ('flat_90_150_255', 0.2, 0.0, 0.0, (0.3, 0.6, 1.0)),
    'arc': ('flat_205_175_255', 0.2, 0.0, 0.0, (0.8, 0.68, 1.0)),
    'ember': ('flat_150_55_15', 0.8, 0.0, 0.0, (0.95, 0.36, 0.06)),
    'collar': ('flat_100_20_110', 0.3, 0.0, 0.0, (0.6, 0.08, 0.72)),
    # Their dark states: dark glass.
    'emitter_dark': ('hlglass', 0.15, 0.0, 0.4), 'seam_dark': ('hlglass', 0.3, 0.0, 0.4),
})


def scorch_texture():
    """hlhull burnt: the hull texture darkened under tileable soot blotches (work/hard_surface/derived/)."""
    path = hs.TEXTURES['hlscorch']
    if os.path.exists(path):
        return
    os.makedirs(hs.DERIVED, exist_ok=True)
    image = bpy.data.images.load(hs.TEXTURES['hlhull'])
    w, h = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rng = np.random.default_rng(4)
    field = np.kron(rng.random((4, 4)), np.ones((h // 4, w // 4))).astype(np.float32)
    for _ in range(160):                                       # np.roll wraps: the blotches tile
        field = (np.roll(field, 3, 0) + np.roll(field, -3, 0) + np.roll(field, 3, 1) + np.roll(field, -3, 1) + field) / 5
    field = (field - field.min()) / (field.max() - field.min())
    dark = (0.16 + 0.28 * field)[..., None]
    rgb = pixels[..., :3] * dark + np.array([0.025, 0.018, 0.014], np.float32) * (1 - dark)
    out = bpy.data.images.new('hlscorch', w, h)
    out.pixels[:] = np.concatenate([rgb, pixels[..., 3:]], -1).ravel()
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(image)


def link(mesh, name):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def sweep(points, radii, key, sides=6):
    """A smooth tube along a polyline (roots, claws, prongs, stakes, cables): `radii` per point, a last radius of 0
    ends in a point, other ends are capped flat (hard rim); nothing reaches below the ground (z 0). Frames by parallel transport. UVs at the shared density:
    u round the tube by arc length (one seam), v along it by length."""
    mat = hs.material(key)
    width, height = mat.node_tree.nodes['Image Texture'].image.size
    repeat_u, repeat_v = width / 4 / 100, height / 4 / 100
    pts = [Vector(p) for p in points]
    count = len(pts)
    tangents = []
    for i in range(count):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, count - 1)]
        tangents.append((b - a).normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    normal = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    frames = []
    for t in tangents:
        normal = (normal - t * normal.dot(t)).normalized()
        frames.append((normal, t.cross(normal)))
    length = [0.0]
    for a, b in zip(pts, pts[1:]):
        length.append(length[-1] + (b - a).length)
    mean_r = sum(r for r in radii if r > 0) / max(1, len([r for r in radii if r > 0]))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rings = []
    for p, r, (n, b) in zip(pts, radii, frames):
        if r > 0:
            rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r)
                          for k in range(sides)])
        else:
            rings.append(bm.verts.new(p))
    for i in range(count - 1):
        lower, upper = rings[i], rings[i + 1]
        for k in range(sides):
            j = (k + 1) % sides
            u0, u1 = k / sides * 2 * math.pi * mean_r / repeat_u, (k + 1) / sides * 2 * math.pi * mean_r / repeat_u
            v0, v1 = length[i] / repeat_v, length[i + 1] / repeat_v
            if isinstance(upper, list):
                face = bm.faces.new([lower[k], lower[j], upper[j], upper[k]])
                coords = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
            else:
                face = bm.faces.new([lower[k], lower[j], upper])
                coords = ((u0, v0), (u1, v0), ((u0 + u1) / 2, v1))
            for loop, c in zip(face.loops, coords):
                loop[uv].uv = c
            face.smooth = True
    caps = [bm.faces.new(list(reversed(rings[0])))]
    if isinstance(rings[-1], list):                        # an end with a radius is capped too
        caps.append(bm.faces.new(rings[-1]))
    for cap in caps:
        for loop in cap.loops:
            loop[uv].uv = (loop.vert.co.x / repeat_u, loop.vert.co.y / repeat_v)
        for k in range(sides):
            bm.edges.get([cap.verts[k], cap.verts[(k + 1) % sides]]).smooth = False
    bmesh.ops.triangulate(bm, faces=caps)
    for v in bm.verts:                                     # a root's flared foot sits on the ground, not under it
        v.co.z = max(v.co.z, 0.0)                          # (the build snaps the lowest point to the ground)
    mesh = bpy.data.meshes.new('sweep')
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    return link(mesh, 'sweep')


def torus(major, minor, location, key, rotation=(0, 0, 0), segments=16, minor_segments=6, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=segments,
                                     minor_segments=minor_segments, location=location)
    obj = bpy.context.active_object
    obj.scale = scale
    if isinstance(rotation, Quaternion):
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = rotation
    else:
        obj.rotation_euler = rotation
    hs.finish(obj, key)
    bpy.ops.object.shade_smooth()
    return obj


def fit_faces(obj, key, direction=(0, -1, 0), both=False):
    """Map `key`'s texture once over the object's faces that look along `direction` (seen from the front, -y: its x-z
    extent), the rest keeping their material; with `both`, the back faces too, mirrored so they read from behind."""
    mat = hs.material(key)
    obj.data.materials.append(mat)
    index = len(obj.data.materials) - 1
    d = Vector(direction)
    faces = [p for p in obj.data.polygons if p.normal.dot(d) > 0.5 or (both and p.normal.dot(d) < -0.5)]
    xs = [obj.data.vertices[v].co.x for p in faces for v in p.vertices]
    zs = [obj.data.vertices[v].co.z for p in faces for v in p.vertices]
    layer = obj.data.uv_layers.active.data
    for p in faces:
        p.material_index = index
        back = p.normal.dot(d) < 0
        for li in p.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            u = (co.x - min(xs)) / (max(xs) - min(xs))
            layer[li].uv = (1 - u if back else u, (co.z - min(zs)) / (max(zs) - min(zs)))
    return obj


def chain(points, key, link_length=0.22, thickness=0.03):
    """Chain links along a polyline, each turned a quarter about the chain from the last."""
    pts = [Vector(p) for p in points]
    step = link_length * 0.72
    distance, k = 0.0, 0
    for a, b in zip(pts, pts[1:]):
        seg = b - a
        while distance < seg.length:
            centre = a + seg.normalized() * distance
            align = Vector((1, 0, 0)).rotation_difference(seg.normalized())
            turn = Quaternion(seg.normalized(), math.pi / 2 * (k % 2)) @ align
            torus(link_length / 2 - thickness, thickness, centre, key, rotation=turn, segments=6, minor_segments=3,
                  scale=(1.0, 0.62, 1.0))
            distance += step
            k += 1
        distance -= seg.length


def ground_clamp(obj):
    """Flatten whatever of a part lies under the ground (z 0) onto it: a sunken rock keeps the model's foot at 0."""
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, -obj.location.z)
    return obj


def radial(r, angle, z):
    return (r * math.cos(angle), r * math.sin(angle), z)


# --- The ion cannon -----------------------------------------------------------------------------------------------
PIVOT = Vector((0, 0, 5.6))
RAISE = math.radians(8)
AIM = Vector((0, -math.cos(RAISE), math.sin(RAISE)))        # the barrel's axis: forward (-y), raised 8 degrees
BARREL_TURN = (math.pi / 2 - RAISE, 0, 0)                   # turns a part's local +z onto AIM
BARREL = [(1.0, -5.0), (1.55, -4.4), (1.75, -2.6), (1.68, -0.4), (1.25, 3.0), (0.86, 8.5), (0.6, 15.4)]


def barrel_radius(z):
    for (r0, z0), (r1, z1) in zip(BARREL, BARREL[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return BARREL[-1][0]


def on_barrel(z):
    return PIVOT + AIM * z


def ion_cannon(lit):
    """The Ancient ion cannon on a corner bastion (z4_03, z4_08): a tapering white-gold barrel 22 m long with gold
    rings and a blue emitter tip, on a yoke of two ceramic cheeks over a turntable and a base drum (radius 5), black
    resin roots gripping the drum from the bastion's top and climbing the cheeks, resin spikes round the deck.
    Pivot 5.6 m up; the barrel points along -y (glTF +z), raised 8 degrees. Lit: the emitter and thin seams glow
    blue-white; dark: dark glass."""
    seam, emitter = ('seam', 'emitter') if lit else ('seam_dark', 'emitter_dark')
    # The base: a drum, a gold ring, a turntable.
    lathe([(5.0, 0.0), (5.0, 1.0), (4.5, 1.4)], (0, 0, 0), 'cannon', 18)
    round_cylinder(4.3, 0.24, (0, 0, 1.46), 'gold_band', 18)
    lathe([(4.0, 1.5), (4.0, 2.0), (3.2, 2.4)], (0, 0, 0), 'cannon', 18)
    # The yoke: two cheeks with rounded tops round the pivot, gold hubs, a glowing slot down each.
    for x in (-2.45, 2.45):
        cube((0.8, 3.6, PIVOT.z - 2.2), (x, 0, (PIVOT.z + 2.2) / 2), 'cannon')
        round_cylinder(1.8, 0.8, (x, 0, PIVOT.z), 'cannon', 16, rotation=(0, math.pi / 2, 0))
        round_cylinder(1.0, 0.3, (x * 1.2, 0, PIVOT.z), 'gold_band', 10, rotation=(0, math.pi / 2, 0))
        cube((0.06, 0.12, 2.4), (x * 1.18, -1.2, 3.5), seam)
    # The barrel (white ceramic), its gold rings, the muzzle collar and the emitter tip; glowing seams at the breech
    # and before the muzzle.
    lathe(BARREL, PIVOT, 'ceramic', 16, rotation=BARREL_TURN)
    for z in (-4.0, 4.6, 9.4):
        round_cylinder(barrel_radius(z - 0.2) + 0.06, 0.4, on_barrel(z), 'gold_band', 16, rotation=BARREL_TURN)
    for z in (1.9, 13.6):
        round_cylinder(barrel_radius(z - 0.06) + 0.035, 0.14, on_barrel(z), seam, 16, rotation=BARREL_TURN)
    round_cylinder(0.8, 0.8, on_barrel(15.6), 'gold_band', 16, rotation=BARREL_TURN)
    lathe([(0.62, 15.9), (0.5, 16.75), (0.14, 17.25)], PIVOT, emitter, 16, rotation=BARREL_TURN)
    # Resin roots grown up the drum's flank and over its edge onto the turntable, two climbing each cheek, resin
    # spikes on the drum's top.
    rng = random.Random(21)
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.2
        twist = rng.uniform(-0.1, 0.1)
        path = [radial(r, a + twist * i, z) for i, (r, z) in
                enumerate([(5.65, 0.0), (5.12, 0.6), (4.75, 1.36), (4.08, 1.82), (3.55, 2.32)])]
        sweep(path, [0.42, 0.28, 0.21, 0.13, 0.0], 'nresin', 5)
    for x in (-1, 1):
        for y in (-0.9,):
            sweep([(x * 3.5, y, 2.3), (x * 3.05, y * 1.05, 3.3), (x * 2.95, y * 0.95, 4.5), (x * 2.98, y * 0.8, 5.4)],
                  [0.3, 0.24, 0.15, 0.0], 'nresin', 5)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.6
        sweep([radial(4.6, a, 1.2), radial(4.75, a, 2.2), radial(4.95, a, 3.3)], [0.3, 0.15, 0.0], 'nresin', 5)


# --- The node mast ------------------------------------------------------------------------------------------------
def node_mast(lit):
    """A slender capacitor mast on a node blockhouse's crown (z4_03, z4_04): a black resin foot (radius 0.8) with
    resin claws, a tapering white ceramic shaft with gold bands to 10.3 m, a gold collar and two curved ceramic prongs
    whose gold tips stand 0.9 apart at 12 m, the violet-white arc between them (an emissive tube; the light is the
    hes_lattice_coil light). Off: no arc, the tips dark."""
    tip = 'arc' if lit else 'seam_dark'
    lathe([(0.8, 0.0), (0.62, 0.3), (0.4, 0.8), (0.3, 1.3)], (0, 0, 0), 'nresin', 12)
    for k in range(4):
        a = k * 2 * math.pi / 4 + 0.3
        sweep([radial(0.95, a, 0.0), radial(0.5, a, 0.7), radial(0.32, a, 1.8)], [0.12, 0.09, 0.0], 'nresin', 5)
    lathe([(0.3, 1.25), (0.24, 5.0), (0.17, 10.3)], (0, 0, 0), 'mast', 12)
    for z, r in ((1.35, 0.33), (5.0, 0.28), (8.6, 0.23)):
        round_cylinder(r, 0.14, (0, 0, z), 'gold_band', 12)
    lathe([(0.22, 10.1), (0.3, 10.35), (0.2, 10.6)], (0, 0, 0), 'gold_band', 12)
    for x in (-1, 1):                                  # the prongs: a fork opening upward, the tips flaring out
        path = [(x * 0.1, 0, 10.5), (x * 0.36, 0, 10.68), (x * 0.5, 0, 11.05), (x * 0.54, 0, 11.6),
                (x * 0.6, 0, 12.05), (x * 0.72, 0, 12.4)]
        sweep(path, [0.12, 0.11, 0.095, 0.08, 0.06, 0.0], 'bone', 6)
        sweep([(x * 0.6, 0, 12.05), (x * 0.65, 0, 12.22), (x * 0.72, 0, 12.4)], [0.065, 0.05, 0.0], tip, 5)
    if lit:                                            # two jagged strands from tip to tip
        for strand, (lift, seed) in enumerate(((0.0, 5), (0.12, 9))):
            rng = random.Random(seed)
            path = [(-0.66 + 1.32 * i / 7, rng.uniform(-0.06, 0.06),
                     12.26 + lift * math.sin(math.pi * i / 7) + (rng.uniform(-0.13, 0.13) if 0 < i < 7 else 0))
                    for i in range(8)]
            sweep(path, [0.05 - 0.015 * strand] * 7 + [0.0], 'arc', 4)


# --- The glyph plate ----------------------------------------------------------------------------------------------
def glyph_plate():
    """A black resin slab 6.0 x 0.8 x 9.0 on a short stub, its front face (-y) carrying `hkglyph` once (the square
    texture stretched 1.5 times up the 2:3 face)."""
    cube((4.8, 0.62, 0.3), (0, 0, 0.15), 'nresin')
    slab = cube((6.0, 0.8, 9.0), (0, 0, 0.3 + 4.5), 'nresin')
    fit_faces(slab, 'glyph')


# --- The grafting frame -------------------------------------------------------------------------------------------
def grafting_frame():
    """A Kreegan grafting frame (z4_06): two pointed resin arches 3 m wide and 3.75 m tall, cross ribs, gold spikes on
    the apexes, a captured Ancient capacitor cell (white-gold, its middle band still glowing) held across the middle
    by four resin claws over a resin stump, cables hanging from the apex to the cell's ends."""
    for y in (-0.55, 0.55):
        for x in (-1, 1):
            sweep([(x * 1.45, y, 0.0), (x * 1.48, y, 1.4), (x * 1.0, y, 2.95), (x * 0.06, y, 3.68)],
                  [0.17, 0.14, 0.11, 0.09], 'nresin', 6)
            sweep([(x * 1.45, y, 0.25), (x * 1.75, y * 1.25, 0.1), (x * 1.95, y * 1.4, 0.0)], [0.12, 0.08, 0.0],
                  'nresin', 5)                                                  # a foot claw
        hs.cone(0.12, 0.0, 0.6, (0, y, 3.95), 'trim', 8)
    for x, z in ((0.0, 3.62), (-1.4, 2.0), (1.4, 2.0)):
        sweep([(x, -0.62, z), (x, 0.0, z + 0.06), (x, 0.62, z)], [0.08, 0.08, 0.08], 'nresin', 5)
    lathe([(0.25, -0.95), (0.44, -0.75), (0.45, 0.0), (0.44, 0.75), (0.25, 0.95)], (0, 0, 1.72),
          'cannon', 12, rotation=(0, math.pi / 2, 0))
    for x in (-0.98, 0.98):
        round_cylinder(0.3, 0.1, (x, 0, 1.72), 'trim', 12, rotation=(0, math.pi / 2, 0))
    round_cylinder(0.47, 0.1, (0, 0, 1.72), 'seam', 12, rotation=(0, math.pi / 2, 0))
    lathe([(0.5, 0.0), (0.3, 0.35), (0.22, 0.95), (0.36, 1.32)], (0, 0, 0), 'nresin', 8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sweep([(sx * 1.42, sy * 0.55, 1.2), (sx * 1.0, sy * 0.5, 1.12), (sx * 0.72, sy * 0.42, 1.45),
                   (sx * 0.58, sy * 0.3, 1.98)], [0.09, 0.08, 0.06, 0.0], 'nresin', 5)
    for (x0, y0), x1 in (((-0.1, -0.45), -0.85), ((0.1, 0.45), 0.85), ((0.0, -0.5), 0.5)):
        sweep([(x0, y0, 3.5), (x0 + (x1 - x0) * 0.4, y0 * 0.7, 2.7), (x0 + (x1 - x0) * 0.8, y0 * 0.3, 2.25),
               (x1, 0, 2.12)], [0.04] * 4, 'cable', 4)


# --- The membrane banner ------------------------------------------------------------------------------------------
def membrane_banner():
    """A Kreegan standard (z4_06, z4_05): a bone pole 4.2 m on three gilded claw feet, a bone cross-bar with gold ends
    at 3.9 m, a violet membrane banner 1.5 x 3.0 hanging from it in front of the pole (`hpbanner` once, front and
    back), a gilded spear tip with a crescent."""
    lathe([(0.075, 0.0), (0.06, 4.2)], (0, 0, 0), 'bone', 8)
    lathe([(0.2, 0.0), (0.13, 0.12), (0.09, 0.35)], (0, 0, 0), 'presin', 8)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        sweep([radial(0.06, a, 0.45), radial(0.25, a, 0.25), radial(0.48, a, 0.06), radial(0.62, a, 0.0)],
              [0.05, 0.045, 0.03, 0.0], 'trim', 5)
    round_cylinder(0.04, 1.8, (0, -0.1, 3.9), 'bone', 8, rotation=(0, math.pi / 2, 0))
    for x in (-1, 1):
        hs.cone(0.06, 0.0, 0.2, (x * 1.0, -0.1, 3.9), 'trim', 8, rotation=(0, x * math.pi / 2, 0))
    lathe([(0.075, 4.15), (0.075, 4.22), (0.045, 4.3)], (0, 0, 0), 'trim', 8)
    hs.cone(0.06, 0.0, 0.32, (0, 0, 4.44), 'trim', 8)
    for x in (-1, 1):
        sweep([(0, 0, 4.18), (x * 0.16, 0, 4.22), (x * 0.22, 0, 4.36), (x * 0.16, 0, 4.5)], [0.035, 0.03, 0.02, 0.0],
              'trim', 5)
    # The banner: a gently waving membrane (8 columns), 2 cm thick.
    bm = bmesh.new()
    columns, w, top, bottom, depth = 8, 1.5, 3.9, 0.9, 0.02
    grid = []
    for i in range(columns + 1):
        x = -w / 2 + w * i / columns
        y = -0.1 + 0.03 * math.sin(i / columns * 2 * math.pi)
        grid.append([bm.verts.new((x, y + dy, z)) for dy, z in ((-depth / 2, bottom), (-depth / 2, top),
                                                                (depth / 2, top), (depth / 2, bottom))])
    for i in range(columns):
        a, b = grid[i], grid[i + 1]
        for k in range(4):
            bm.faces.new([a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]])
    bm.faces.new(list(reversed(grid[0])))
    bm.faces.new(grid[-1])
    mesh = bpy.data.meshes.new('banner')
    bm.to_mesh(mesh)
    bm.free()
    banner = link(mesh, 'banner')
    hs.finish(banner, 'membrane')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    fit_faces(banner, 'banner', both=True)


# --- The cable spool ----------------------------------------------------------------------------------------------
def cable_spool():
    """A Lattice cable spool lying on its side (axis along x): 2.6 m resin flanges with gold rims, the wound cable
    (dark with violet lines running round), a gold hub on an axle resting on two resin A-frames on a resin cradle
    slab, the loose end of the cable run out along the ground in front (-y)."""
    zc = 1.52
    turn = (0, math.pi / 2, 0)
    cube((2.3, 2.0, 0.18), (0, 0, 0.09), 'nresin')
    for x in (-0.84, 0.84):
        round_cylinder(1.3, 0.14, (x, 0, zc), 'nresin', 20, rotation=turn)
        round_cylinder(1.33, 0.08, (x, 0, zc), 'trim', 20, rotation=turn)
    round_cylinder(1.0, 1.56, (0, 0, zc), 'cable', 20, rotation=turn)
    round_cylinder(0.12, 2.3, (0, 0, zc), 'girder', 8, rotation=turn)
    for x in (-1, 1):
        round_cylinder(0.34, 0.1, (x * 0.96, 0, zc), 'gold_band', 12, rotation=turn)
        round_cylinder(0.2, 0.1, (x * 1.1, 0, zc), 'trim', 8, rotation=turn)
        for y in (-1, 1):
            sweep([(x * 1.1, y * 0.95, 0.15), (x * 1.1, y * 0.5, 0.95), (x * 1.1, y * 0.05, zc)],
                  [0.13, 0.1, 0.08], 'nresin', 5)
    sweep([(0.35, -0.98, 1.55), (0.38, -1.12, 0.8), (0.46, -1.45, 0.12), (0.7, -2.3, 0.07), (1.15, -3.3, 0.07)],
          [0.07] * 5, 'cable', 5)


# --- The trophy pile ----------------------------------------------------------------------------------------------
def trophy_pile():
    """The Kreegans' trophies (z4_06): a low heap of broken Ancient wall plates (white-gold) over rubble, a cracked
    Ancient ceramic helmet impaled on a bone stake at the top, gold rings scattered and one hung on the stake."""
    ground_clamp(faceted_rock(0.85, (0, 0, 0.12), 'plate', 41, stretch=(1.3, 1.1, 0.5)))
    ground_clamp(faceted_rock(0.45, (0.75, -0.45, 0.08), 'plate', 42, stretch=(1.2, 1.0, 0.55)))
    rng = random.Random(13)
    plates = [((1.0, 0.7, 0.07), (-0.55, -0.35, 0.45), (0.5, -0.3, 0.4)),
              ((0.9, 0.6, 0.07), (0.5, -0.5, 0.42), (-0.55, 0.2, -0.5)),
              ((1.1, 0.75, 0.07), (0.15, 0.55, 0.5), (-0.4, -0.45, 0.2)),
              ((0.8, 0.55, 0.07), (-0.85, 0.45, 0.25), (0.15, 0.6, 1.1)),
              ((0.7, 0.5, 0.06), (0.95, 0.25, 0.15), (0.0, -0.25, 2.0)),
              ((0.6, 0.45, 0.06), (-0.2, -0.85, 0.12), (0.2, 0.05, 0.6))]
    for size, location, rotation in plates:
        ground_clamp(cube(size, location, 'cannon', rotation=rotation))
    for k in range(4):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.7, 1.15)
        ground_clamp(faceted_rock(rng.uniform(0.12, 0.2), (math.cos(a) * r, math.sin(a) * r, 0.06), 'ceramic',
                                  50 + k, stretch=(1.2, 1.0, 0.6)))
    sweep([(0.05, 0.05, 0.2), (0.02, 0.02, 0.9), (0.0, 0.0, 1.5)], [0.08, 0.06, 0.0], 'bone', 6)
    # The helmet: a ceramic dome with a gold brow band and a dark visor, tilted on the stake.
    def helmet():
        lathe([(0.27, 0.0), (0.3, 0.16), (0.24, 0.38), (0.08, 0.48)], (0, 0, 0), 'ceramic', 10)
        round_cylinder(0.305, 0.07, (0, 0, 0.16), 'trim', 10)
        cube((0.3, 0.12, 0.08), (0, -0.26, 0.08), 'glass')                         # the visor
        cube((0.03, 0.04, 0.2), (0.12, -0.24, 0.3), 'glass', rotation=(0.3, 0.5, 0.4))   # the crack
    hs.assemble(helmet, (0.0, 0.0, 1.02), (0.25, -0.15, 0.4))
    for location, rotation in (((0.6, 0.1, 0.42), (0.5, 0.2, 0)), ((-0.7, -0.6, 0.12), (0.1, 0.0, 0)),
                               ((0.85, -0.75, 0.1), (0.2, -0.1, 0))):
        torus(0.17, 0.035, location, 'trim', rotation=rotation, segments=10, minor_segments=4)
    torus(0.15, 0.03, (0.0, 0.0, 0.85), 'trim', rotation=(0.4, 0.3, 0), segments=10, minor_segments=4)


# --- The pen post -------------------------------------------------------------------------------------------------
def pen_post():
    """A collar post of the Kept market's cage pens (z4_05, z4_06): a black resin post 2.2 m on a flared foot, a gold
    band, a gilded cap and finial, a resin hook arm in front (-y) with a resin chain down to a collar glowing
    violet-red, a second chain draped from the post to the ground beside it."""
    lathe([(0.32, 0.0), (0.2, 0.2), (0.12, 0.5)], (0, 0, 0), 'nresin', 8)
    lathe([(0.12, 0.45), (0.1, 1.98)], (0, 0, 0), 'nresin', 8)
    round_cylinder(0.125, 0.07, (0, 0, 1.05), 'trim', 8)
    lathe([(0.17, 1.94), (0.17, 2.02), (0.03, 2.2)], (0, 0, 0), 'trim', 8)
    sweep([(0, -0.05, 1.72), (0, -0.28, 1.8), (0, -0.4, 1.72), (0, -0.4, 1.62)], [0.05, 0.045, 0.035, 0.0],
          'nresin', 5)
    chain([(0, -0.4, 1.6), (0, -0.4, 0.98)], 'nresin')
    torus(0.15, 0.03, (0, -0.4, 0.82), 'collar', rotation=(math.pi / 2 - 0.3, 0, 0.4), segments=12,
          minor_segments=4)
    chain([(0.11, 0.0, 1.2), (0.38, 0.06, 0.55), (0.58, 0.1, 0.07), (0.95, 0.16, 0.07)], 'nresin')


# --- The crawler wreck --------------------------------------------------------------------------------------------
# The hull's cross-section (y, z), counter-clockwise seen from +x, and its stations along x with their height scale
# (the nose wedge at -x). Edges 4 and 5 are the front (-y) slope and wall; they are torn out between x -2.4 and 2.0.
HULL_SECTION = [(-1.7, 0.0), (1.7, 0.0), (1.7, 1.9), (1.2, 2.9), (-1.2, 2.9), (-1.7, 1.9)]
HULL_STATIONS = [(-4.4, 0.55), (-3.6, 1.0), (-2.4, 1.0), (2.0, 1.0), (4.0, 1.0), (4.3, 0.9)]
HULL_LIFT = 0.25                                            # the belly's height over the track's foot
SAG = math.atan2(HULL_LIFT, 3.95)                           # resting on its +y track and its -y belly edge
OPENING = (2, (4, 5))                                       # station span, section edges


def hull_shell():
    bm = bmesh.new()
    rings = [[bm.verts.new((x, y, HULL_LIFT + z * s)) for y, z in HULL_SECTION] for x, s in HULL_STATIONS]
    n = len(HULL_SECTION)
    for i in range(len(rings) - 1):
        for j in range(n):
            if i == OPENING[0] and j in OPENING[1]:
                continue
            bm.faces.new([rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % n], rings[i][(j + 1) % n]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bm.normal_update()
    mesh = bpy.data.meshes.new('hull')
    bm.to_mesh(mesh)
    bm.free()
    obj = link(mesh, 'hull')
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    shell = obj.modifiers.new('shell', 'SOLIDIFY')
    shell.thickness = 0.16
    shell.offset = -1.0
    bpy.ops.object.modifier_apply(modifier='shell')
    hs.finish(obj, 'hull')
    # The burnt and torn parts: the inside and the roof burnt, the outer plates beside the opening torn.
    scorch, torn = hs.material('scorch'), hs.material('hull_torn')
    obj.data.materials.append(scorch)
    obj.data.materials.append(torn)
    for p in obj.data.polygons:
        c, nrm = p.center, p.normal
        inward = Vector((c.x * 0.3, c.y, c.z - HULL_LIFT - 1.4)).dot(nrm) < 0
        if inward or (nrm.z > 0.9 and c.z > 2.7) or (c.x < -3.5 and nrm.x < -0.5 and c.z > 0.8):
            p.material_index = 1
        elif nrm.y < -0.5 and (-3.6 < c.x < -2.4 or 2.0 < c.x < 4.0):
            p.material_index = 2
    return obj


def crawler_wreck():
    """A wrecked Ancient crawler (THE_CROWN.md section 14; z4_03's wreck): a white hull-plated tracked body 8.7 m long
    on its +y track, the front (-y) torn open between x -2.4 and 2.0 (4.4 m wide, the inside floor 0.16 up, 2.7 m
    clear: the dare locker stands inside), the inside, the roof and the nose burnt black, torn plates bent out round
    the opening, a fallen wall plate. The -y track is off, lying flat on the ground off the +x end, two of its road
    wheels left on their stubs, one fallen. A broken sensor turret on the roof. The whole body sags 4 degrees toward
    the lost track."""
    def body():
        hull_shell()
        # The +y track: a stadium of track plates round five road wheels, its foot on the ground.
        cube((7.6, 0.55, 0.9), (0.0, 1.98, 0.45), 'scrap')
        for x in (-3.8, 3.8):
            round_cylinder(0.45, 0.55, (x, 1.98, 0.45), 'scrap', 12, rotation=(math.pi / 2, 0, 0))
        for x in (-2.8, -1.4, 0.0, 1.4, 2.8):
            round_cylinder(0.36, 0.08, (x, 2.28, 0.42), 'hull', 10, rotation=(math.pi / 2, 0, 0))
            round_cylinder(0.14, 0.06, (x, 2.33, 0.42), 'trim', 6, rotation=(math.pi / 2, 0, 0))
        cube((8.0, 0.12, 0.14), (0.0, 1.76, 2.2), 'trim')                     # the gold band over the track
        # The -y side: bare wheel stubs, the band left in pieces.
        for x in (-2.8, -1.4, 0.0, 1.4, 2.8):
            round_cylinder(0.1, 0.35, (x, -1.88, 0.5), 'girder', 6, rotation=(math.pi / 2, 0, 0))
        for x in (-3.75, 3.75):                                             # the idler and the drive sprocket
            round_cylinder(0.45, 0.14, (x, -1.95, 0.85), 'hull', 12, rotation=(math.pi / 2, 0, 0))
            round_cylinder(0.18, 0.08, (x, -2.04, 0.85), 'trim', 8, rotation=(math.pi / 2, 0, 0))
        cube((1.2, 0.12, 0.14), (-3.0, -1.76, 2.2), 'trim')
        cube((1.6, 0.12, 0.14), (3.0, -1.76, 2.2), 'trim')
        # Torn plates bent out at the opening's ends, jagged stubs of the slope hanging from the roof's edge.
        cube((0.9, 0.12, 1.5), (-2.75, -1.95, 1.4), 'hull_torn', rotation=(0.25, 0, -0.5))
        cube((0.8, 0.12, 1.3), (2.3, -1.95, 1.25), 'hull_torn', rotation=(-0.2, 0, 0.55))
        for x, w, rz in ((-1.9, 0.6, 0.12), (-0.8, 0.5, -0.15), (0.6, 0.7, 0.08), (1.5, 0.45, -0.12)):
            cube((w, 0.12, 0.45), (x, -1.33, 2.88), 'hull_torn', rotation=(-0.464, 0, rz))
        # The broken sensor turret on the roof.
        lathe([(0.8, 3.07), (0.8, 3.4), (0.6, 3.65)], (-1.6, 0.3, 0), 'hull', 14)
        round_cylinder(0.82, 0.08, (-1.6, 0.3, 3.35), 'trim', 14)
        round_cylinder(0.12, 1.1, (-1.6, -0.55, 3.5), 'scorch', 8, rotation=(math.pi / 2 - 0.35, 0, 0.3))
    hull = hs.assemble(body, (0, 0, 0), (SAG, 0, 0))
    hull.location.z = -1.7 * math.sin(SAG)                 # the track's inner foot on the ground
    # On the ground: the thrown track peeled off toward +x, a fallen wheel and a fallen wall plate by the nose (none
    # in front of the opening).
    rng = random.Random(17)
    for k in range(9):                                     # the thrown track: its plates in a loose curve
        t = k / 8
        x, y = 2.2 + 3.7 * t, -1.95 - 2.2 * t - 0.5 * t * t
        cube((0.48, 0.62, 0.1), (x, y, 0.06), 'scrap', rotation=(0, rng.uniform(-0.04, 0.04),
                                                                  -0.62 - 0.3 * t + rng.uniform(-0.08, 0.08)))
    round_cylinder(0.36, 0.08, (-4.4, -2.4, 0.04), 'hull', 12)
    cube((2.2, 1.4, 0.12), (-3.3, -3.0, 0.26), 'hull_torn', rotation=(0.1, 0.12, 0.6))


# --- The gilded fire bowl -----------------------------------------------------------------------------------------
def fire_bowl_gilded():
    """P1's fire bowl in the palace's finish (z4_10, lower right pair): a polished black resin bowl 0.92 m across on
    an hourglass resin stem, three gilded bone claws curling up its sides to horns over the rim and six small gilded
    horns round the rim, a glowing ember bed with dark coals inside. The flame is the decoration's light."""
    lathe([(0.3, 0.0), (0.12, 0.2), (0.09, 0.45), (0.15, 0.72)], (0, 0, 0), 'presin', 10)
    lathe([(0.15, 0.7), (0.3, 0.82), (0.44, 0.98), (0.46, 1.05), (0.4, 1.06), (0.33, 0.93)], (0, 0, 0), 'presin', 14)
    lathe([(0.385, 0.94), (0.385, 0.99), (0.2, 1.03)], (0, 0, 0), 'ember', 14)     # a low mound of embers
    rng = random.Random(8)
    for k in range(5):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.0, 0.22)
        faceted_rock(0.07, (math.cos(a) * r, math.sin(a) * r, 1.0), 'coal', 60 + k, stretch=(1.2, 1.0, 0.6))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        sweep([radial(0.66, a, 0.02), radial(0.5, a, 0.06), radial(0.36, a, 0.28), radial(0.29, a, 0.58),
               radial(0.36, a, 0.84), radial(0.5, a, 1.0), radial(0.6, a, 1.14)],
              [0.025, 0.05, 0.065, 0.06, 0.05, 0.035, 0.0], 'trim', 5)
    for k in range(6):
        a = k * 2 * math.pi / 6
        sweep([radial(0.43, a, 1.0), radial(0.52, a, 1.06), radial(0.56, a, 1.15)], [0.035, 0.025, 0.0], 'trim', 4)


# --- The great ion cannon ----------------------------------------------------------------------------------------
# The one great cannon on the Crownspire's dome (COMBAT.md "Ion cannons", "The look and the shot";
# concepts/monsters/ion_cannon.png, candidate 1). A 50 m firing head on a squat yoke 20 m across over a stepped base.
# The head lies level along -y (glTF +z) on its pivot GC_PIVOT; local head coordinates are (x, up, along the axis
# toward the muzzle), measured from the pivot.
GC_PIVOT = Vector((0.0, 0.0, 12.0))
GC_HEAD = [(3.0, -12.0), (4.6, -11.0), (4.8, -6.0), (4.2, -2.0), (3.6, 2.0), (3.2, 29.5), (3.7, 30.0), (3.5, 33.0),
           (2.6, 34.0)]                                     # (radius, along): an octagon, slab-sided, flat on top
GC_TURN = (math.pi / 2, 0, 0)                               # turns a part's local +z onto the head's axis (-y)
GC_RINGS = (7.0, 12.0, 17.0, 22.0, 27.0)                    # the capacitor rings, breech to muzzle
GC_PRONGS = (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3)
GC_TIP = 38.0                                               # the prongs' tips, along the axis from the pivot
GC_ZONES = ['breech', 'pods', 'ring1', 'ring2', 'ring3', 'ring4', 'ring5', 'muzzle']
GC_LEVELS = {'dark': ('hlglass', 0.15, 0.0, 0.4),
             'dim': ('flat_60_32_100', 0.25, 0.0, 0.0, (0.24, 0.08, 0.46), 2.0),
             'lit': ('flat_220_200_255', 0.2, 0.0, 0.0, (0.82, 0.68, 1.0), 10.0),
             'hot': ('flat_250_245_255', 0.2, 0.0, 0.0, (1.0, 0.95, 1.0), 16.0)}   # strengths: read across the crater
# One material per zone and level (HS_gc_<zone>_<level>), so each zone is its own primitive in the GLB.
hs.MATERIALS.update({f'gc_{zone}_{level}': value for zone in GC_ZONES for level, value in GC_LEVELS.items()})
# The states: the zones lit at each stage of the wind-up (dark: powered down, and the instant after a shot).
GC_STATES = {'dark': {}, 'rest': {}, 'c1': {'breech'}, 'c2': {'breech', 'pods'},
             'c3': {'breech', 'pods', 'ring1', 'ring2'},
             'c4': {'breech', 'pods', 'ring1', 'ring2', 'ring3', 'ring4', 'ring5'}, 'c5': set(GC_ZONES)}


def gc_radius(z):
    for (r0, z0), (r1, z1) in zip(GC_HEAD, GC_HEAD[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return GC_HEAD[-1][0]


def gc_point(x, up, along):
    """A head-local point (x, up, along the axis toward the muzzle) in the model's coordinates."""
    return GC_PIVOT + Vector((x, -along, up))


def octagon(obj):
    """Turn an 8-sided part on the head's axis an eighth of a turn about it (flat top, bottom and sides) and shade it
    flat: the head's slabs."""
    obj.rotation_euler = (0, math.pi / 8, 0)
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    for p in obj.data.polygons:
        p.use_smooth = False
    return obj


def bone_fin(along, scale):
    """A backswept bone fin on the head's flat top: a five-sided blade, thinner toward its tip, raked to the rear."""
    top = GC_PIVOT.z + gc_radius(along) * math.cos(math.pi / 8) - 0.3
    y0 = -along
    profile = [(-1.8, 0.0), (1.4, 0.0), (1.6, 1.0), (2.8, 3.0), (0.4, 1.8)]        # (rearward, up)
    half = [0.3, 0.3, 0.2, 0.06, 0.2]
    bm = bmesh.new()
    sides = [[bm.verts.new((sx * h * scale, y0 + dy * scale, top + dz * scale)) for (dy, dz), h in zip(profile, half)]
             for sx in (-1, 1)]
    bm.faces.new(sides[0])
    bm.faces.new(list(reversed(sides[1])))
    for k in range(5):
        j = (k + 1) % 5
        bm.faces.new([sides[0][j], sides[0][k], sides[1][k], sides[1][j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    mesh = bpy.data.meshes.new('fin')
    bm.to_mesh(mesh)
    bm.free()
    return hs.finish(link(mesh, 'fin'), 'bone')


def great_cannon(state):
    """The great ion cannon (concept candidate 1). A stepped round base of ceramic slabs (radius 12) with resin roots,
    a resin course and a gold turning ring; a squat yoke platform 20 m across with two cheeks and gold hubs holding
    the pivot 12 m up. The head: a slab-sided white ceramic octagon (`hoterm`; `hocannon`'s lattice at the shared
    density made a fine mosaic of a 50 m head), its belly and lower flanks black resin, gold collars and bands,
    50 m from the breech to the prong tips, wider at the breech, bone fins raked back along its spine, resin cables
    from the yoke into the breech. Four glow zones, each its own material: the breech core (a round window in gold on
    each side of the breech), the twin capacitor pods (on the breech's upper flanks), five capacitor rings along the
    barrel and the muzzle crown (the bore and the inner blades of three prongs). `state` sets each zone dark, dim
    violet, lit violet-white or, for the muzzle in c5, white-hot; c5 adds three arcs between the prong tips."""
    lit = GC_STATES[state]

    def zone(name):
        if state == 'dark':
            level = 'dark'
        elif name == 'muzzle' and state == 'c5':
            level = 'hot'
        else:
            level = 'lit' if name in lit else 'dim'
        return f'gc_{name}_{level}'

    # The base: a sloped course of ceramic slabs, a resin course, the gold turning ring; buttress slabs and roots.
    lathe([(12.0, 0.0), (12.0, 0.5), (11.0, 2.2)], (0, 0, 0), 'cannon', 20)
    round_cylinder(10.6, 0.8, (0, 0, 2.6), 'nresin', 20)
    round_cylinder(10.3, 0.4, (0, 0, 3.2), 'gold_band', 20)
    for k in range(10):
        a = k * 2 * math.pi / 10 + math.pi / 10
        ground_clamp(cube((1.6, 2.6, 2.6), (math.cos(a) * 11.7, math.sin(a) * 11.7, 1.2), 'cannon',
                          rotation=(0, -0.3, a)))
    for k in range(5):
        a = k * 2 * math.pi / 5
        sweep([radial(12.6, a, 0.0), radial(11.9, a + 0.03, 0.9), radial(11.1, a + 0.05, 1.95),
               radial(10.5, a + 0.06, 2.6), radial(9.8, a + 0.07, 3.1)], [0.6, 0.45, 0.35, 0.22, 0.0], 'nresin', 5)
    # The yoke: a platform 20 m across, two cheeks with rounded tops round the pivot, gold hubs.
    lathe([(10.0, 3.4), (10.0, 4.4), (8.6, 5.6)], (0, 0, 0), 'cannon', 20)
    for x in (-5.1, 5.1):
        cube((1.6, 5.6, GC_PIVOT.z - 5.0), (x, 0, (GC_PIVOT.z + 5.0) / 2), 'cannon')
        round_cylinder(2.8, 1.6, (x, 0, GC_PIVOT.z), 'cannon', 16, rotation=(0, math.pi / 2, 0))
        round_cylinder(1.8, 0.4, (x * 1.17, 0, GC_PIVOT.z), 'gold_band', 12, rotation=(0, math.pi / 2, 0))
    # The head and its gold collars; the capacitor rings, each with a gold band on either side.
    head = octagon(lathe(GC_HEAD, GC_PIVOT, 'ceramic', 8, rotation=GC_TURN))
    head.data.materials.append(hs.material('nresin'))      # the belly and lower flanks: Kreegan resin
    for p in head.data.polygons:
        if p.normal.z < -0.3:
            p.material_index = 1
    octagon(round_cylinder(gc_radius(30.0) + 0.12, 0.5, gc_point(0, 0, 30.3), 'gold_band', 8, rotation=GC_TURN))
    octagon(round_cylinder(gc_radius(-6.2) + 0.1, 0.5, gc_point(0, 0, -5.9), 'gold_band', 8, rotation=GC_TURN))
    for k, along in enumerate(GC_RINGS):
        octagon(round_cylinder(gc_radius(along - 0.5) + 0.16, 1.0, gc_point(0, 0, along), zone(f'ring{k + 1}'), 8,
                               rotation=GC_TURN))
        for side in (-0.72, 0.72):
            octagon(round_cylinder(gc_radius(along + side - 0.2) + 0.1, 0.4, gc_point(0, 0, along + side),
                                   'gold_band', 8, rotation=GC_TURN))
    # The breech core: a round window in a gold rim on each side of the breech.
    side = gc_radius(-8.5) * math.cos(math.pi / 8)
    for sx in (-1, 1):
        round_cylinder(2.0, 0.2, gc_point(sx * (side + 0.05), 0, -8.5), 'gold_band', 14, rotation=(0, math.pi / 2, 0))
        round_cylinder(1.6, 0.2, gc_point(sx * (side + 0.15), 0, -8.5), zone('breech'), 14,
                       rotation=(0, math.pi / 2, 0))
    # The twin capacitor pods on the breech's upper flanks, gold-capped and strapped.
    for sx in (-1, 1):
        d = gc_radius(-6.0) * math.cos(math.pi / 8) + 0.9
        centre = (sx * d * math.cos(math.pi / 4), d * math.sin(math.pi / 4))
        lathe([(0.6, -5.0), (1.25, -4.3), (1.4, -3.4), (1.4, 3.4), (1.25, 4.3), (0.6, 5.0)],
              gc_point(centre[0], centre[1], -6.5), zone('pods'), 10, rotation=GC_TURN)
        for along in (-8.6, -6.5, -4.4):
            round_cylinder(1.5, 0.4, gc_point(centre[0], centre[1], along), 'gold_band', 10, rotation=GC_TURN)
        for along in (-11.5, -1.5):
            round_cylinder(0.75, 0.6, gc_point(centre[0], centre[1], along), 'gold_band', 10, rotation=GC_TURN)
    # Bone fins raked back along the spine, largest over the breech.
    for k, along in enumerate((-9.0, -4.0, 2.0, 8.5, 15.0, 21.0, 26.0)):
        bone_fin(along, 1.7 - 0.13 * k)
    # Resin cables from the yoke's rear into the breech's belly.
    for x in (-2.6, -0.9, 0.9, 2.6):
        sweep([(x, 6.0, 5.4), (x * 1.15, 8.5, 5.0), (x * 1.15, 11.2, 6.2), (x, 11.4, 7.6), (x, 10.6, 8.4)],
              [0.42] * 5, 'nresin', 6)
    # The muzzle crown: the bore glowing in the muzzle's face, three ceramic prongs with glowing inner blades.
    round_cylinder(1.5, 0.3, gc_point(0, 0, 34.1), zone('muzzle'), 12, rotation=GC_TURN)
    for a in GC_PRONGS:
        def at(r, along):
            return gc_point(r * math.cos(a), r * math.sin(a), along)
        sweep([at(2.9, 32.0), at(3.1, 34.5), at(2.6, 36.5), at(1.9, GC_TIP)], [0.75, 0.6, 0.4, 0.0], 'ceramic', 6)
        sweep([at(2.4, 33.8), at(2.55, 34.6), at(2.15, 36.4), at(1.75, GC_TIP - 0.3)], [0.35, 0.3, 0.2, 0.0],
              zone('muzzle'), 5)
    if state == 'c5':                                      # arcs crawling between the prong tips
        rng = random.Random(3)
        for i, a in enumerate(GC_PRONGS):
            b = GC_PRONGS[(i + 1) % 3]
            if b < a:
                b += 2 * math.pi
            points = []
            for k in range(8):
                t = k / 7
                inner = 0 < k < 7
                r = 1.9 - 0.5 * math.sin(math.pi * t) + (rng.uniform(-0.6, 0.6) if inner else 0.0)
                phi = a + (b - a) * t + (rng.uniform(-0.12, 0.12) if inner else 0.0)
                along = GC_TIP - 0.2 + (rng.uniform(-0.9, 0.9) if inner else 0.0)
                points.append(gc_point(r * math.cos(phi), r * math.sin(phi), along))
            sweep(points, [0.2] * 7 + [0.0], 'gc_muzzle_hot', 4)


MODELS = {
    'hes_ion_cannon': lambda: ion_cannon(True), 'hes_ion_cannon_dark': lambda: ion_cannon(False),
    'hes_great_cannon': lambda: great_cannon('rest'), 'hes_great_cannon_dark': lambda: great_cannon('dark'),
    **{f'hes_great_cannon_{state}': (lambda st: lambda: great_cannon(st))(state)
       for state in ('c1', 'c2', 'c3', 'c4', 'c5')},
    'hes_node_mast': lambda: node_mast(True), 'hes_node_mast_off': lambda: node_mast(False),
    'hes_glyph_plate': glyph_plate, 'hes_grafting_frame': grafting_frame,
    'hes_membrane_banner': membrane_banner, 'hes_cable_spool': cable_spool, 'hes_trophy_pile': trophy_pile,
    'hes_pen_post': pen_post, 'hes_crawler_wreck': crawler_wreck, 'hes_fire_bowl_gilded': fire_bowl_gilded,
}

if __name__ == '__main__':
    hs.MODELS.update(MODELS)
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(MODELS)
    for model in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scorch_texture()
        hs.build(model)
