"""Greybox stand-ins for the Brood Spires' new decorations until their Meshy models are made and approved
(level_generation/props/hesper_decorations, designs hes_spire_* and the rest). Metres, glTF Y up, at the design's size
(BROOD_SPIRES.md section 14): the build places them and sizes their collision from these bounds.

    blender --background --factory-startup --python level_generation/projects/hesper_out3/author_standins_blender.py

Writes standins/<name>.glb. A stand-in is replaced by its model simply by the model existing: the stage reads the
decoration project's work folders before this one (hesper_stage/decorations.yml source_dirs).
"""
import math
from pathlib import Path

import bpy

OUTPUT = Path(__file__).resolve().parent / 'standins'


def material(name, colour, emission=None, strength=2.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Roughness'].default_value = rough
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def finish(o, mat, smooth=False):
    o.data.materials.append(mat)
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def cone(r1, r2, depth, z, mat, verts=8, x=0.0, y=0.0, tilt=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                    location=(x, y, z + depth / 2), rotation=tilt)
    return finish(bpy.context.object, mat)


def sphere(r, loc, scale, mat, sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, mat, smooth=True)


def box(loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, mat)


def tube_along(points, radius, mat, verts=8):
    """A tapered tube through points (x, y, z), radius a list per point."""
    curve = bpy.data.curves.new('tube', 'CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, (x, y, z), r in zip(spline.points, points, radius):
        p.co = (x, y, z, 1)
        p.radius = r
    curve.bevel_depth = 1.0
    curve.bevel_resolution = max(1, verts // 4)
    o = bpy.data.objects.new('tube', curve)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, mat)


def export(name):
    """One mesh with every transform applied: the stage and the build size a model from its vertex bounds."""
    bpy.ops.object.select_all(action='SELECT')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    bpy.context.object.name = name
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT / (name + '.glb')), export_format='GLB', export_yup=True,
                              use_selection=True)
    clear()


def spire(height, base, mat, glow, bone, windows=3, spikes=6):
    cone(base, base * 0.08, height * 0.92, 0, mat, verts=9)
    cone(base * 1.6, base * 0.5, height * 0.12, 0, mat, verts=7)                       # the root flare
    for k in range(windows):                                                            # glowing slit windows
        z = height * (0.18 + 0.55 * k / max(1, windows - 1)) if windows > 1 else height * 0.4
        r = base * (1 - z / height) + 0.05
        box((0, -r * 0.92, z), (r * 0.35, r * 0.25, height * 0.09), glow)
    for k in range(spikes):                                                             # bone spikes
        a = k * 2.4
        z = height * (0.15 + 0.7 * k / spikes)
        r = base * (1 - z / height)
        cone(r * 0.25, 0.02, r * 1.4, 0, bone, verts=5, x=math.cos(a) * r, y=math.sin(a) * r,
             tilt=(math.pi / 2.6 * -math.sin(a), math.pi / 2.6 * math.cos(a), 0)).location.z = z
    cone(base * 0.12, 0.01, height * 0.12, height * 0.9, bone, verts=5)


def build():
    OUTPUT.mkdir(exist_ok=True)
    clear()
    resin = material('resin', (0.07, 0.035, 0.08), rough=0.35)
    resin_dark = material('resin dark', (0.03, 0.02, 0.035), rough=0.6)
    glow = material('window glow', (1.0, 0.45, 0.1), emission=(1.0, 0.42, 0.08), strength=3.0)
    amber = material('egg amber', (0.95, 0.5, 0.12), emission=(0.9, 0.42, 0.08), strength=1.5, rough=0.25)
    bone = material('bone', (0.82, 0.76, 0.62), rough=0.55)
    ceramic = material('ceramic', (0.78, 0.76, 0.7), rough=0.5)
    gold = material('gold', (0.75, 0.55, 0.22), rough=0.35)
    acid = material('acid', (0.55, 0.75, 0.08), emission=(0.45, 0.65, 0.05), strength=1.2, rough=0.15)
    crust = material('crust', (0.78, 0.73, 0.38), rough=0.7)
    green = material('nest glow', (0.4, 0.6, 0.1), emission=(0.35, 0.6, 0.05), strength=1.0)
    cyan = material('beacon', (0.6, 0.85, 1.0), emission=(0.5, 0.8, 1.0), strength=3.0)
    cloth = material('cloth', (0.6, 0.08, 0.06), rough=0.8)

    spire(30.0, 2.6, resin, glow, bone, windows=4, spikes=9)
    export('hes_spire_great')
    spire(16.0, 1.6, resin, glow, bone, windows=2, spikes=5)
    export('hes_spire_mid')
    for k, (x, y, h) in enumerate(((0.0, 0.0, 8.0), (1.0, 0.6, 6.0), (-0.8, 0.7, 5.5))):
        cone(1.0, 0.05, h, 0, resin, verts=7, x=x, y=y)
        cone(0.25, 0.01, 1.2, h - 0.6, bone, verts=5, x=x, y=y)
        box((x, y - 0.75, h * 0.3), (0.3, 0.2, h * 0.2), glow)
    cone(2.2, 1.0, 1.2, 0, resin, verts=8)
    export('hes_spire_cluster')
    spire(27.0, 2.8, resin, glow, bone, windows=4, spikes=8)
    cone(1.4, 4.2, 2.5, 26.0, resin_dark, verts=10)                                    # the roost cup
    for s in (-1, 1):                                                                   # its two tusks
        tube_along([(s * 3.6, 0, 27.5), (s * 4.4, 0, 30.5), (s * 3.2, 0, 33.0), (s * 1.6, 0, 34.0)],
                   [0.6, 0.45, 0.25, 0.05], bone)
    export('hes_spire_roost')
    for k, (x, ang, length, r) in enumerate(((-7.0, 0.05, 7.0, 2.4), (0.0, -0.08, 6.0, 1.9), (6.5, 0.12, 6.0, 1.3))):
        bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=r, radius2=r * 0.7, depth=length,
                                        location=(x, 0, r * 0.8), rotation=(0, math.pi / 2, ang))
        finish(bpy.context.object, resin)
        box((x, -r * 0.95, r * 0.9), (length * 0.4, 0.3, r * 0.4), glow)
        cone(0.3, 0.02, 2.0, r * 1.3, bone, verts=5, x=x + 0.5, y=0.6)
    export('hes_spire_fallen')

    sphere(4.5, (0, 0, 0), (1, 1, 0.66), resin)
    for k in range(6):
        a = k * 1.05
        sphere(0.9, (math.cos(a) * 4.0, math.sin(a) * 4.0, 0.5), (1, 1, 1.25), amber)
    for k in range(4):
        cone(0.3, 0.02, 1.6, 2.4, bone, verts=5, x=math.cos(k * 1.6) * 1.5, y=math.sin(k * 1.6) * 1.5)
    export('hes_hive_mound')
    sphere(3.0, (0, 0, -0.5), (1, 1, 0.3), resin_dark)
    for k, (x, y, r) in enumerate(((0, 0, 1.0), (1.4, 0.5, 0.8), (-1.3, 0.6, 0.85), (0.4, -1.3, 0.75),
                                   (-0.8, -1.1, 0.6), (2.2, -0.6, 0.5), (-2.2, -0.2, 0.55))):
        sphere(r, (x, y, r * 0.6), (1, 1, 1.25), amber)
    export('hes_egg_mound')
    for name, glowmat in (('hes_nest_mound', green), ('hes_nest_mound_dead', resin_dark)):
        sphere(3.5, (0, 0, -0.6), (1, 0.9, 0.55), resin_dark)
        for k in range(5):
            a = k * 1.25
            sphere(0.55, (math.cos(a) * 2.9, math.sin(a) * 2.6, 0.5), (1, 1, 0.7), glowmat)
        sphere(2.0, (0.6, 0.4, 0.9), (1, 1, 0.6), crust if name.endswith('mound') else resin_dark)
        export(name)
    box((0, 0, 1.2), (5.0, 5.0, 2.4), ceramic)
    box((0.6, -0.4, 2.7), (3.4, 3.2, 0.7), ceramic)
    cone(3.6, 2.2, 3.2, 0, resin, verts=10)
    cone(1.7, 1.6, 0.6, 3.4, resin_dark, verts=12)                                      # the socket on top
    box((0, -2.6, 1.6), (1.2, 0.2, 0.25), glow)
    export('hes_turret_mount_k')
    tube_along([(-6.0, 0, 0.6), (-3.0, 0.6, 0.9), (0.0, 1.0, 1.0), (3.0, 0.7, 0.8), (5.5, 0.0, 0.6)],
               [0.9, 0.7, 0.6, 0.55, 0.45], bone)
    sphere(1.1, (-6.0, 0, 0.8), (1, 1, 0.9), bone)
    export('hes_giant_rib')
    box((0, 0, 0.12), (4.0, 3.0, 0.25), crust)
    box((0, -1.55, -0.1), (3.6, 0.15, 0.35), acid)
    export('hes_acid_shelf')
    cone(7.0, 4.5, 8.0, 0, resin, verts=12)
    cone(4.5, 2.5, 9.0, 8.0, resin, verts=10)
    cone(2.5, 0.2, 7.0, 17.0, resin, verts=8)
    cone(0.5, 0.02, 4.0, 22.0, bone, verts=5)
    for k in range(8):
        a = k * math.pi / 4
        box((math.cos(a) * 6.1, math.sin(a) * 6.1, 3.0), (1.2, 1.2, 3.5), glow, rot=(0, 0, a))
    for s in (-1, 1):
        tube_along([(s * 2.6, 0, 16.0), (s * 4.0, 0, 19.0), (s * 3.0, 0, 22.0)], [0.5, 0.35, 0.05], bone)
    export('hes_hatchery_tower')
    cone(26.0, 14.0, 6.0, 0, resin_dark, verts=14)                                      # the root mound's buttresses
    cone(14.0, 9.0, 12.0, 6.0, resin, verts=12)
    cone(9.0, 6.0, 12.0, 18.0, resin, verts=10)
    cone(6.0, 3.5, 12.0, 30.0, resin, verts=10)
    cone(3.5, 0.3, 22.0, 42.0, resin, verts=8)
    for k in range(4):
        z = 10.0 + 11.0 * k
        box((9.5 - k * 2.0, 0, z), (0.4, 3.0, 2.2), glow)                              # the east face's rib windows
    for a in (0.6, 2.7, 4.6):                                                           # the grafted dishes
        x, y = math.cos(a) * 4.8, math.sin(a) * 4.8
        cone(3.2, 1.2, 1.0, 52.0, ceramic, verts=12, x=x, y=y, tilt=(0.5 * math.sin(a), -0.5 * math.cos(a), 0))
        sphere(0.6, (x, y, 53.5), (1, 1, 1), cyan)
    for s in (-1, 1):
        tube_along([(s * 7.0, 4.0, 18.0), (s * 9.0, 4.0, 30.0), (s * 7.0, 4.0, 42.0)], [1.2, 0.8, 0.1], bone)
    export('hes_relay_spire')
    sphere(1.0, (0, 0, 22.5), (60.0, 20.0, 22.5), resin_dark, sub=3)                    # the hull, 120 x 40 x 45
    for k in range(12):                                                                 # ribs vaulting over it
        x = -50.0 + 100.0 * k / 11
        r = 20.0 * math.sqrt(max(0.05, 1 - (x / 60.0) ** 2)) + 0.6
        tube_along([(x, -r, 6.0), (x, -r * 0.7, 22.5 + r * 0.6), (x, 0, 22.5 + r * 1.05),
                    (x, r * 0.7, 22.5 + r * 0.6), (x, r, 6.0)], [0.9, 0.9, 0.9, 0.9, 0.9], bone)
    for k in range(9):                                                                  # amber openings on both flanks
        x = -40.0 + 80.0 * k / 8
        r = 20.0 * math.sqrt(max(0.05, 1 - (x / 60.0) ** 2))
        for s in (-1, 1):
            box((x, s * r * 0.98, 16.0), (4.0, 1.0, 3.0), amber)
    export('hes_seedship')
    tube_along([(0, 0, 0), (2.0, 0, 20.0), (4.0, 0, 40.0), (3.0, 0, 58.0), (-2.0, 0, 70.0)],
               [3.0, 2.5, 2.0, 1.4, 0.3], bone)
    sphere(0.9, (1.4, -2.4, 8.0), (1, 0.5, 1), cyan)
    export('hes_cradle_arch')
    for k, (w, h) in enumerate(((0.34, 0.14), (0.28, 0.12), (0.22, 0.12), (0.14, 0.1))):
        z = sum(hh for _, hh in ((0.34, 0.14), (0.28, 0.12), (0.22, 0.12), (0.14, 0.1))[:k])
        box((0.02 * k, 0, z + h / 2), (w, w * 0.8, h), ceramic, rot=(0, 0, k * 0.4))
    box((0.0, -0.13, 0.33), (0.08, 0.02, 0.25), cloth)
    export('hes_trail_cairn')
    # The ag-flyer wreck: a crashed colony crop flyer, nose down, a wing torn off beside it (18 m).
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.3, depth=12.0, location=(0, 0, 1.0),
                                        rotation=(0, math.pi / 2 - 0.12, 0))
    finish(bpy.context.object, ceramic)
    cone(1.3, 0.3, 3.0, 0, ceramic, verts=10, x=7.2, y=0, tilt=(0, math.pi / 2 + 0.25, 0)).location.z = 0.2
    box((-1.0, 3.2, 1.4), (4.0, 5.0, 0.18), ceramic, rot=(0.12, 0, 0.1))
    box((1.5, -5.0, 0.3), (3.6, 4.0, 0.16), ceramic, rot=(0.3, 0.1, -0.4))
    box((-5.5, 0, 2.3), (1.6, 0.15, 1.6), gold)
    box((0, -1.25, 1.2), (6.0, 0.05, 0.25), gold)
    export('hes_agflyer_wreck')


if __name__ == '__main__':
    build()
