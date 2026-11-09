"""Closed beam-weapon housings in the shared rig's calibrated two-handed grip frame."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
source = Path(args[0]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Rig']
for name in ('Rifle', 'TwinLance'):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.update()
M = rig.data.bones['Rifle'].matrix_local.copy()
layout = json.loads((P / 'work/armour_layout.json').read_text())
rect = layout['plates']['back']['rect']
atlas = layout['atlas']
plate = bpy.data.materials['HKR_Plate']
glow = bpy.data.materials['HKR_Glow']
dark = bpy.data.materials.get('Lancer_Resin') or bpy.data.materials.new('Lancer_Resin')
dark.use_nodes = True
shader = dark.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (0.024, 0.012, 0.028, 1)
shader.inputs['Metallic'].default_value = 0
shader.inputs['Roughness'].default_value = 0.68


def build(name, twin):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')

    def loft(stations, material=0, sides=8, cx=0.0):
        # Stations: forward position, half width, half height, vertical centre.
        rings = []
        for y, rx, rz, z in stations:
            rings.append([bm.verts.new((cx + rx * math.cos(2 * math.pi * k / sides), y,
                                       z + rz * math.sin(2 * math.pi * k / sides))) for k in range(sides)])
        for i in range(len(rings) - 1):
            for k in range(sides):
                kn = (k + 1) % sides
                face = bm.faces.new((rings[i][k], rings[i][kn], rings[i + 1][kn], rings[i + 1][k]))
                face.material_index = material
                for loop, (u, v) in zip(face.loops, ((k/sides, i/(len(rings)-1)),
                        ((k+1)/sides, i/(len(rings)-1)), ((k+1)/sides, (i+1)/(len(rings)-1)),
                        (k/sides, (i+1)/(len(rings)-1)))):
                    loop[uv].uv = ((rect[0] + u*rect[2])/atlas, 1-(rect[1]+v*rect[3])/atlas)
        # Opposite-edge strip caps avoid high-valence fans.
        for ring in (rings[0], list(reversed(rings[-1]))):
            order = [0]
            for k in range(1, sides//2):
                order.extend((k, sides-k))
            order.append(sides//2)
            for k in range(len(order)-2):
                face = bm.faces.new([ring[order[k]], ring[order[k+1]], ring[order[k+2]]])
                face.material_index = material
                for loop in face.loops:
                    loop[uv].uv = ((rect[0]+rect[2]*0.5)/atlas, 1-(rect[1]+rect[3]*0.5)/atlas)

    # The rear grip is raked through the original fist; the left fist supports the forward rail.
    for z0, z1 in [(-0.075, 0.085)]:
        rings = []
        for z in (z0, z1):
            rings.append([bm.verts.new((0.019*math.cos(k*math.pi/4),
                          z*math.tan(math.radians(20))+0.02185*math.sin(k*math.pi/4), z))
                          for k in range(8)])
        for k in range(8):
            face = bm.faces.new((rings[0][k], rings[0][(k+1)%8], rings[1][(k+1)%8], rings[1][k]))
            face.material_index = 2
        for ring in rings:
            for k in range(1, 7):
                face = bm.faces.new((ring[0], ring[k], ring[k+1]))
                face.material_index = 2
    loft([(0.24, .020, .020, .08), (.64, .020, .020, .08)], 2, cx=-.12)
    loft([(.39, .08, .022, .08), (.43, .08, .022, .08)], 2, sides=4, cx=-.06)
    loft([(-.20, .018, .025, .12), (-.18, .020, .030, .12), (-.16, .020, .030, .14),
          (.10, .045, .055, .16), (.42, .045, .055, .17)], 2)
    loft([(-.20, .021, .027, .13), (-.18, .025, .035, .13), (-.17, .023, .030, .14)])
    # Forward strut joins the handguard to the beam housing without entering either fist.
    loft([(.39, .026, .065, .13), (.42, .026, .065, .13)])
    # Long resin spine, exposed hot chamber, ceramic side jaws; no blade or bayonet.
    for cx in ((-.069, .069) if twin else (0.0,)):
        radius = .052 if twin else .065
        loft([(.42, radius, radius, .19), (.47, radius, radius, .19)], 2, cx=cx)
        loft([(.82, radius*.90, radius*.90, .19), (1.28, radius*.80, radius*.80, .19)], 2, cx=cx)
        loft([(.47, radius*.87, radius*.87, .19), (.82, radius*.87, radius*.87, .19)], 1, cx=cx)
        for y in (.47, .55, .63, .71, .79):
            loft([(y, radius, radius, .19), (y+.022, radius, radius, .19)], 2, cx=cx)
        for sign in (-1, 1):
            loft([(.40, .026, .034, .19), (.48, .020, .040, .19), (.60, .012, .025, .19), (.78, .012, .025, .19), (.86, .021, .045, .19),
                  (1.22, .032, .053, .19), (1.43, .018, .033, .19), (1.55, .010, .012, .19)],
                 cx=cx+sign*radius*1.22, sides=4)
        loft([(1.27, radius*.50, radius*.50, .19), (1.33, radius*.82, radius*.82, .19), (1.39, radius*.50, radius*.50, .19)], 1, cx=cx)
    # The rear stock rises above the right forearm in the fitted run.
    for vertex in bm.verts:
        if vertex.co.y < .10 and vertex.co.z > .09:
            vertex.co.z += .10 * (.10 - vertex.co.y) / .30
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.transform(M)
    mesh.materials.append(plate)
    mesh.materials.append(glow)
    mesh.materials.append(dark)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.vertex_groups.new(name='Rifle').add(list(range(len(mesh.vertices))), 1, 'REPLACE')
    obj.modifiers.new('Armature', 'ARMATURE').object = rig
    print('WEAPON', name, len(mesh.polygons), 'triangles')


build('Rifle', False)
build('TwinLance', True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name, point in [('Socket_Muzzle', (0, 1.33, .19)),
                    ('Socket_Muzzle_Left', (-.069, 1.33, .19)),
                    ('Socket_Muzzle_Right', (.069, 1.33, .19))]:
    bone = rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
    bone.head = M @ Vector(point)
    bone.tail = bone.head + M.to_3x3() @ Vector((0, .04, 0))
    bone.parent = rig.data.edit_bones['Rifle']
    bone.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1]).resolve() if len(args) > 1 else P / 'work/armed.blend'))
