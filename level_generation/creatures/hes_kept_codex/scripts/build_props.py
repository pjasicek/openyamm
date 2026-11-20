"""Kept collar, pick, blunt club and small scrap chest plate; local authoring coordinates, not fitted yet."""
import json
import math
import os
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/props'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0


def material(name, colour, roughness=0.8, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = 0
    if emission:
        shader.inputs['Emission Color'].default_value = (*emission, 1)
        shader.inputs['Emission Strength'].default_value = 1
        mat['openyamm_bloom'] = True
    return mat


RESIN = material('Kept_Resin', (0.018, 0.014, 0.023), 0.64)
GLOW = material('Kept_Glow', (0.65, 0.09, 0.006), 0.45, (1, 0.16, 0.008))
SCRAP = material('Kept_Scrap', (0.12, 0.10, 0.075), 0.77)
CLOTH = material('Kept_Wrap', (0.115, 0.075, 0.045), 0.93)
CERAMIC = material('Kept_Ceramic', (0.42, 0.34, 0.235), 0.83)


def box(name, centre, size, mat, rotation=0, bevel=0.002):
    bm = bmesh.new()
    transform = Matrix.Translation(centre) @ Matrix.Rotation(rotation, 4, 'Y')
    transform @= Matrix.Diagonal((*size, 1))
    bmesh.ops.create_cube(bm, size=1, matrix=transform)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect='EDGES')
    return mesh_object(name, bm, mat)


def mesh_object(name, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    assert all(face.calc_area() > 1e-10 for face in bm.faces), name
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def ring(name, rx, ry, thickness, z0, z1, mat, segments=16):
    bm = bmesh.new()
    loops = []
    for x, y, z in ((rx, ry, z0), (rx, ry, z1),
                    (rx-thickness, ry-thickness, z0), (rx-thickness, ry-thickness, z1)):
        loops.append([bm.verts.new((x*math.cos(i*math.tau/segments),
                                   y*math.sin(i*math.tau/segments), z)) for i in range(segments)])
    for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
        for i in range(segments):
            j = (i+1) % segments
            bm.faces.new((loops[a][i], loops[a][j], loops[b][j], loops[b][i]))
    return mesh_object(name, bm, mat)


def shaft(name, stations, mat, axis='Z'):
    bm = bmesh.new()
    loops = []
    for height, radius in stations:
        points = []
        for i in range(8):
            u, v = radius*math.cos(i*math.tau/8), radius*math.sin(i*math.tau/8)
            points.append(bm.verts.new((u, v, height) if axis == 'Z' else (height, u, v)))
        loops.append(points)
    for a, b in zip(loops, loops[1:]):
        for i in range(8):
            j = (i+1) % 8
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    return mesh_object(name, bm, mat)


def export(name, objects, purpose):
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    obj = objects[0]
    obj.name = name
    triangles = len(obj.data.polygons)
    assert 0 < triangles < 1500, (name, triangles)
    obj['purpose'] = purpose
    obj['fit_status'] = 'unfitted authoring prop; no runtime binding'
    filepath = OUT / f'{name}.glb'
    bpy.ops.export_scene.gltf(filepath=str(filepath), use_selection=True, export_format='GLB',
                              export_yup=True, export_animations=False, export_skins=False,
                              export_extras=True, export_materials='EXPORT')
    report[name] = {'file': str(filepath.relative_to(ROOT)), 'triangles': triangles,
                    'purpose': purpose, 'status': 'unfitted', 'metres': list(obj.dimensions)}
    obj.hide_set(True)
    return obj


report = {}
parts = [ring('ResinBand', 0.085, 0.075, 0.012, -0.034, 0.034, RESIN)]
for i in range(8):
    angle = i*math.tau/8
    rib = box('ResinRib', (0, 0, 0), (0.012, 0.018, 0.074), RESIN, bevel=0)
    rib.location = (0.084*math.cos(angle), 0.074*math.sin(angle), 0)
    rib.rotation_euler.z = angle
    parts.append(rib)
parts.extend([box('FrontNode', (0, -0.081, 0), (0.045, 0.022, 0.075), RESIN, bevel=0.005),
              box('OrangeNode', (0, -0.094, 0), (0.012, 0.005, 0.052), GLOW, bevel=0),
              box('RearSeam', (0, 0.079, 0), (0.007, 0.006, 0.052), GLOW, bevel=0)])
export('hes_kept_collar', parts, 'Black resin control collar; orange factor-only front node and rear seam.')

parts = [shaft('PickHandle', [(-0.12, 0.018), (0.43, 0.019), (0.46, 0.023)], CLOTH)]
head = shaft('PickHead', [(-0.23, 0.004), (-0.11, 0.020), (0, 0.031), (0.11, 0.021), (0.20, 0.005)],
             SCRAP, axis='X')
head.location.z = 0.43
parts.append(head)
parts.append(box('PickSocket', (0, 0, 0.43), (0.064, 0.060, 0.067), SCRAP, bevel=0.004))
export('hes_kept_pick', parts, 'Short mining pick; grip centre at origin, shaft along +Z, strike head at +Z.')

parts = [shaft('ClubHandle', [(-0.12, 0.018), (0.32, 0.021), (0.48, 0.035)], CLOTH)]
for x, y, z, angle in ((-0.032, -0.006, 0.40, -0.08), (0.025, 0.010, 0.42, 0.07), (0, -0.030, 0.39, 0.04)):
    parts.append(box('BluntScrap', (x, y, z), (0.048, 0.065, 0.21), SCRAP, angle, bevel=0.006))
for z in (0.325, 0.445):
    parts.append(ring('HeadBinding', 0.074, 0.069, 0.008, z, z+0.018, CLOTH, segments=8))
export('hes_kept_club', parts, 'Crude blunt scrap club; no spikes or energy; grip centre at origin.')

bm = bmesh.new()
outline = [(-0.10, -0.11), (0.08, -0.11), (0.115, -0.07), (0.12, 0.08),
           (0.07, 0.12), (-0.085, 0.115), (-0.12, 0.045), (-0.115, -0.075)]
loops = [[bm.verts.new((x, y, z)) for x, z in outline] for y in (-0.007, 0.007)]
for i in range(8):
    j = (i+1) % 8
    bm.faces.new((loops[0][i], loops[0][j], loops[1][j], loops[1][i]))
bm.faces.new(loops[0])
bm.faces.new(list(reversed(loops[1])))
plate = mesh_object('ScrapPlate', bm, CERAMIC)
export('hes_kept_plate', [plate], 'Small chipped ceramic chest plate; straps require fitting to the chosen shirt.')

with (ROOT / 'review/prop_inventory.json').open('w') as stream:
    json.dump(report, stream, indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'props.blend'))
print(json.dumps(report, indent=2), flush=True)
# The sandbox's PulseAudio shutdown hangs after completed writes, even with -noaudio.
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
