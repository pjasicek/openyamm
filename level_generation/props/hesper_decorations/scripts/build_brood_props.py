"""Build the Brood Spires' hard-surface decorations (hes_out3) into work/hard_surface/.

    blender --background --factory-startup --python scripts/build_brood_props.py [-- <name> ...]

The two pieces of design/kreegan_world/zone3/BROOD_SPIRES.md section 14 (KITS.md) made in Blender rather than Meshy,
in the shared hard-surface kit (build_hard_surface.py: materials, UV density, export). Metres, nose and front as the
greybox stand-ins they replace (hesper_out3/author_standins_blender.py), so the map's placement is unchanged:

  hes_trail_cairn    a Hesperian trail cairn: white ceramic shards stacked, a red-and-gold cloth strip (z3_05), 1.2 m
                     (the design's 0.6 doubled at the integrator's review)
  hes_agflyer_wreck  a crashed colony crop flyer, nose down in the marsh, its right wing torn off and lying beside it,
                     creep grown over its tail (event 20: "Agri-Service 3"), 18 m long, the nose at +x
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hard_surface as hs  # noqa: E402
from build_hard_surface import cone, cube, cylinder, finish, open_tube, shard  # noqa: E402

hs.MATERIALS.update({
    # The colony's livery: Landfall's white prefab panel with its teal and orange stripe.
    'livery': ('hhprefab', 0.5, 0.15, 1.0),
    'nozzle': ('flat_60_62_64', 0.5, 0.6, 0.0),
    'cockpit': ('flat_24_30_34', 0.1, 0.2, 0.0),
})


def loft(sections, key, rotation=(0, 0, 0)):
    """A closed box loft along x through rectangular sections (x, half width, bottom, top), cube-projected (finish)."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in ((x, -w, b), (x, w, b), (x, w, t), (x, -w, t))] for x, w, b, t in sections]
    for a, c in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new([a[i], a[j], c[j], c[i]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new('loft')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('loft', mesh)
    obj.rotation_euler = rotation
    bpy.context.collection.objects.link(obj)
    return finish(obj, key)


def root(points, radii, key='resin', sides=6):
    """A tapered tube through points (x, y, z): a creep root."""
    curve = bpy.data.curves.new('root', 'CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, (x, y, z), radius in zip(spline.points, points, radii):
        point.co = (x, y, z, 1)
        point.radius = radius
    curve.bevel_depth = 1.0
    curve.bevel_resolution = max(1, sides // 4)
    obj = bpy.data.objects.new('root', curve)
    bpy.context.collection.objects.link(obj)
    for other in bpy.context.selected_objects:
        other.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.active_object, key)


def trail_cairn():
    """White ceramic shards stacked in a cairn, a red-and-gold cloth strip tied round its middle and hanging. Built at
    twice the design's 0.6 m (the integrator, 2026-10-23: at 0.6 it was lost on the pale lane)."""
    k_size = 2.0
    rng = random.Random(23)
    slabs = ((0.36, 0.13), (0.3, 0.11), (0.24, 0.1), (0.17, 0.09))
    for k, (w, h) in enumerate(slabs):
        z = sum(hh for _, hh in slabs[:k])
        cube((w * k_size, w * rng.uniform(0.7, 0.9) * k_size, h * k_size),
             (0.015 * k * k_size, -0.01 * k * k_size, (z + h / 2) * k_size), 'ceramic',
             rotation=(rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), k * 0.45 + rng.uniform(-0.1, 0.1)))
    shard(0.16 * k_size, 0.05 * k_size, (0.02 * k_size, 0.0, 0.43 * k_size), 'ceramic', 5)   # a shard on top
    for k in range(4):                                                    # loose shards at the foot
        a = k * 1.7 + 0.4
        cube((0.13 * k_size, 0.08 * k_size, 0.03 * k_size),
             (math.cos(a) * 0.27 * k_size, math.sin(a) * 0.24 * k_size, 0.015 * k_size), 'ceramic',
             rotation=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), a))
    cube((0.27 * k_size, 0.23 * k_size, 0.035 * k_size), (0.0, 0.0, 0.25 * k_size), 'banner',
         rotation=(0, 0, 0.45))                                           # the strip round the stack
    cube((0.06 * k_size, 0.015 * k_size, 0.22 * k_size), (0.05 * k_size, -0.135 * k_size, 0.15 * k_size), 'banner',
         rotation=(0.08, 0, 0.12))                                        # its hanging ends
    cube((0.05 * k_size, 0.015 * k_size, 0.16 * k_size), (-0.03 * k_size, -0.13 * k_size, 0.17 * k_size), 'banner',
         rotation=(-0.05, 0, -0.15))


def agflyer_wreck():
    """A colony crop flyer (a high-wing tilt-fan craft with a spray tank and booms), crashed nose down: the nose
    crumpled, the right wing torn off at the root and lying beside it, resin creep grown up
    over the tail boom."""
    parts = []
    before = set(bpy.context.scene.objects)
    # The fuselage: the cabin in the colony livery, the crushed nose in torn hull, the tail boom.
    loft([(-6.0, 0.9, 0.7, 2.4), (-3.0, 1.35, 0.25, 3.0), (3.0, 1.35, 0.25, 3.0), (4.6, 1.2, 0.35, 2.8)], 'livery')
    loft([(4.6, 1.2, 0.35, 2.8), (6.2, 0.85, 0.55, 2.0), (7.1, 0.45, 0.9, 1.5)], 'hull_torn')
    loft([(2.2, 1.05, 2.95, 2.95), (3.8, 1.05, 2.5, 3.25), (4.9, 0.9, 2.2, 2.75)], 'cockpit')       # the canopy
    loft([(-6.0, 0.55, 1.5, 2.3), (-11.0, 0.28, 1.85, 2.2)], 'livery')
    loft([(-10.9, 0.08, 2.2, 2.2), (-9.2, 0.12, 2.2, 2.2), (-9.9, 0.08, 4.4, 4.4), (-11.0, 0.06, 4.6, 4.6)],
         'hull')                                                                                    # the fin
    cube((1.3, 4.2, 0.12), (-10.3, 0.0, 2.25), 'hull')                                             # tailplane
    # The wings: the left whole with its ducted fan and spray boom, the right a torn stub.
    cube((2.4, 5.3, 0.22), (0.7, 4.0, 3.05), 'hull')
    cube((2.4, 1.2, 0.22), (0.7, -1.95, 3.05), 'hull_torn')
    open_tube(1.15, 0.75, (0.7, 7.2, 3.0), 'trim', 18, thickness=0.12)
    for k in range(3):
        cube((2.0, 0.12, 0.03), (0.7, 7.2, 3.0), 'girder', rotation=(0.0, 0.0, k * math.pi / 3))
    cylinder(0.3, 0.6, (0.7, 7.2, 2.95), 'panel', 10)                                               # its hub
    cylinder(0.06, 5.0, (-0.6, 4.0, 2.85), 'girder', 8, rotation=(math.pi / 2, 0, 0))              # spray boom
    for k in range(7):
        cone(0.05, 0.02, 0.18, (-0.6, 1.8 + 0.7 * k, 2.73), 'nozzle', 6)
    # The spray tank on the back, banded with hazard stripes; skids under the cabin, the right one folded under.
    cylinder(0.9, 3.4, (-2.4, 0.0, 3.6), 'panel', 16, rotation=(0, math.pi / 2, 0))
    for x in (-3.9, -0.9):
        cylinder(0.93, 0.25, (x, 0.0, 3.6), 'hazard', 16, rotation=(0, math.pi / 2, 0))
    cube((7.5, 0.16, 0.16), (-0.5, 1.1, 0.0), 'girder')
    cube((5.0, 0.16, 0.16), (-2.0, -0.85, 0.12), 'girder', rotation=(0.0, 0.0, 0.25))
    for x in (-3.0, 1.8):
        cube((0.14, 0.14, 0.55), (x, 1.05, 0.3), 'girder', rotation=(0.2, 0, 0))
    # Resin creep grown up over the tail boom and the fin's foot: glossy lumps draped over it.
    for k, (x, r) in enumerate(((-7.0, 0.75), (-8.1, 0.85), (-9.3, 0.8), (-10.2, 0.6))):
        hs.faceted_rock(r, (x, 0.05 * (-1) ** k, 1.95), 'resin', 40 + k, stretch=(1.3, 1.0, 0.75), subdivisions=2)
    craft = hs.join([o for o in bpy.context.scene.objects if o not in before])
    craft.rotation_euler = (0.07, 0.16, 0.0)                     # nose down (+x falls) and listing to the torn side
    parts.append(craft)
    # The torn right wing, fallen beside the craft with its fan and a length of boom.
    before = set(bpy.context.scene.objects)
    cube((2.4, 5.0, 0.22), (0.0, 0.0, 0.0), 'hull')
    cube((2.4, 0.5, 0.24), (0.0, 2.6, 0.0), 'hull_torn')
    open_tube(1.15, 0.75, (0.0, -3.4, 0.05), 'trim', 18, thickness=0.12)
    cylinder(0.06, 3.6, (-1.3, -0.4, -0.15), 'girder', 8, rotation=(math.pi / 2, 0, 0))
    wing = hs.join([o for o in bpy.context.scene.objects if o not in before])
    wing.location = (-0.4, -6.4, 0.45)
    wing.rotation_euler = (0.18, 0.05, 0.35)
    parts.append(wing)
    # Creep on the marsh round the tail: low resin roots running out from under the boom, on the ground the craft
    # rests on (its lowest point, the nose).
    lowest = min((craft.matrix_world @ v.co).z for v in craft.data.vertices)
    rng = random.Random(31)
    for k in range(7):
        a = k * 2 * math.pi / 7 + rng.uniform(-0.3, 0.3)
        reach = rng.uniform(2.0, 3.4)
        points = [(-8.3 + math.cos(a) * reach * t, math.sin(a) * reach * t * 0.8,
                   lowest + 0.06 + 0.12 * math.sin(math.pi * t)) for t in (0.0, 0.35, 0.7, 1.0)]
        root(points, [0.22, 0.15, 0.09, 0.03], 'resin', 8)
    for side, x in ((1, -8.0), (-1, -9.1)):                       # two climbing up from them to the lumps on the boom
        foot = (x - 0.3, side * 0.9, lowest)
        top = craft.matrix_world @ Vector((x, side * 0.3, 1.7))
        middle = ((foot[0] + top.x) / 2, side * 0.75, (lowest + top.z) / 2)
        root([foot, middle, tuple(top)], [0.3, 0.22, 0.16], 'resin', 8)

MODELS = {'hes_trail_cairn': trail_cairn, 'hes_agflyer_wreck': agflyer_wreck}

if __name__ == '__main__':
    hs.MODELS.update(MODELS)
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(MODELS)
    for model in names:
        hs.build(model)
