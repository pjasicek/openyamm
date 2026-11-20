"""A pieced Meshy upload on a template's locked layout (work/<template>/layout.blend: the UVs, and so every tier's
maps, stay as they are): the bow (README.md "Bow v2: pieced upload"), the claymore and the staff ("Legendary v2").

Usage: blender --background --python prep_pieced.py -- <template>

The claymore and the staff (README.md "Legendary v2") are long and thin, so one full-length view gave their blade and
shaft 11-14 px per unit: they are cut into CONFIG's pieces, each stood upright by its chord (the staff leans), with
their flats toward Meshy's front as before (no turn).

At idle and at the draw the camera looks along the bow's plane at the limb's belly (the face toward the string); the
v1 guides showed the bow in profile, 25 px per unit, with that face edge-on, so Meshy smeared its paint there. Here the
bow is cut at its natural material breaks (tip fittings, limbs, riser: PIECES, glTF y) and each piece is turned so its
chord stands upright and its belly faces Meshy's front; the pieces stand side by side, the lower limb (never on screen
at idle) at half scale, so the upper limb and the riser fill a 1024 x 1536 guide at about 45 px per unit, face on. The
string (its own 48-triangle part) is left out: post.py keeps its texels from the tier's earlier paint.

Writes into work/w_bow/pieced/: upload.glb (the pieces with the layout's UVs, wound with their normals),
guide_{front,back}.png (plain grey), reference_{front,back}.png and, per earlier tier paint t<n>/basecolor.png,
previous_t<n>_{front,back}.png (that paint in the same framing), pieces.json.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
NAME = argv[0] if argv else 'w_bow'
WORK = os.path.join(PROJECT, 'work', NAME)
OUT = os.path.join(WORK, 'pieced')
os.makedirs(OUT, exist_ok=True)

# Per template: pieces as (glTF y range of face centres, scale), left to right; turn: degrees about the vertical after
# standing a piece upright (the bow's belly to the front); string: leave the bow's string out.
CONFIG = {
    # Upper tip, upper limb, riser, lower limb, lower tip (the lower half never on screen at idle: half scale).
    'w_bow': {'pieces': [((37.0, 99.0), 1.0), ((6.0, 37.0), 1.0), ((-6.0, 6.0), 1.0), ((-37.0, -6.0), 0.5),
                         ((-99.0, -37.0), 0.5)], 'turn': 90.0, 'string': True},
    # Blade's upper and lower half, hilt (guard, grip, pommel).
    'w_claymore': {'pieces': [((44.0, 99.0), 1.0), ((12.0, 44.0), 1.0), ((-99.0, 12.0), 1.0)], 'turn': 0.0,
                   'string': False},
    # Prongs and upper shaft, two shaft pieces, the butt (half scale: below the hands).
    'w_staff': {'pieces': [((5.0, 99.0), 1.0), ((-25.0, 5.0), 1.0), ((-55.0, -25.0), 1.0), ((-999.0, -55.0), 0.5)],
                'turn': 0.0, 'string': False},
}
PIECES = CONFIG[NAME]['pieces']
GAP = 1.2

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'layout.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.faces.ensure_lookup_table()

# The string: the linked part whose x stays near -15.7 (Blender x = glTF x).
string = set()
seen = set()
for f in bm.faces:
    if f.index in seen:
        continue
    part, stack = [], [f]
    seen.add(f.index)
    while stack:
        g = stack.pop()
        part.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index)
                    stack.append(h)
    xs = [v.co.x for g in part for v in g.verts]
    if CONFIG[NAME]['string'] and len(part) < 100 and max(xs) - min(xs) < 0.5:
        string.update(g.index for g in part)
print('PIECED string faces', len(string), flush=True)
# Marked in a face layer: the bisect below renumbers the faces (its parts copy the layer).
string_layer = bm.faces.layers.int.new('string')
for f in bm.faces:
    f[string_layer] = 1 if f.index in string else 0

# Long sliver triangles (the claymore's blade, the staff's shaft) cross the cuts: bisected at each cut height first.
# UVs are affine on a triangle, so the parts map onto exactly the same texels (the paint lands as on the whole one).
cuts = sorted({b for (lo, hi), _ in PIECES for b in (lo, hi) if abs(b) < 900})
for z in cuts:
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0.0, 0.0, z), plane_no=(0.0, 0.0, 1.0))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.faces.ensure_lookup_table()

# Blender z is glTF y. The piece per face in a face layer (indices change with the delete and the split).
layer = bm.faces.layers.int.new('piece')
for f in bm.faces:
    z = sum(v.co.z for v in f.verts) / len(f.verts)
    f[layer] = -1 if f[string_layer] else next(i for i, ((lo, hi), _) in enumerate(PIECES) if lo <= z < hi)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] < 0], context='FACES')
split = [e for e in bm.edges if len({f[layer] for f in e.link_faces}) > 1]
bmesh.ops.split_edges(bm, edges=split)
bm.faces.ensure_lookup_table()
bm.faces.index_update()
piece = {f.index: f[layer] for f in bm.faces}

record = []
x = 0.0
for i, ((lo, hi), scale) in enumerate(PIECES):
    verts = list({v for f in bm.faces if piece[f.index] == i for v in f.verts})
    co = np.array([v.co[:] for v in verts])
    # Chord in the bow plane (Blender XZ): the mean of the lowest and highest tenth of the piece.
    order = np.argsort(co[:, 2])
    n = max(3, len(co) // 10)
    a, b = co[order[:n]].mean(0), co[order[-n:]].mean(0)
    angle = math.atan2(b[0] - a[0], b[2] - a[2])          # tilt of the chord from +Z toward +X
    # Upright (about Blender Y, the bow plane's normal), then the belly (-X) to Meshy's front (-Y), then scaled.
    upright = Matrix.Rotation(angle, 4, 'Y')
    turn = Matrix.Rotation(math.radians(CONFIG[NAME]['turn']), 4, 'Z')
    m = Matrix.Scale(scale, 4) @ turn @ upright
    for v in verts:
        v.co = m @ v.co
    co = np.array([v.co[:] for v in verts])
    lo3, hi3 = co.min(0), co.max(0)
    shift = Vector((x - lo3[0], -(lo3[1] + hi3[1]) / 2, -(lo3[2] + hi3[2]) / 2))
    for v in verts:
        v.co += shift
    x += (hi3[0] - lo3[0]) + GAP
    record.append({'y_range': [lo, hi], 'scale': scale, 'tilt_deg': round(math.degrees(angle), 2),
                   'faces': sum(1 for f in bm.faces if piece[f.index] == i),
                   'size': np.round(hi3 - lo3, 2).tolist()})
co = np.array([v.co[:] for v in bm.verts])
mid = (co.min(0) + co.max(0)) / 2
for v in bm.verts:
    v.co.x -= mid[0]
up = bpy.data.meshes.new('upload')
bm.to_mesh(up)
bm.free()
# (meshy_request.py --pieced winds it with its normals into upload_meshy.glb, as for the v1 upload.)
upload = bpy.data.objects.new('upload', up)
bpy.context.scene.collection.objects.link(upload)
obj.hide_render = True
obj.hide_set(True)
up.materials.clear()
for o in bpy.data.objects:
    o.select_set(o == upload)
bpy.context.view_layer.objects.active = upload
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x, scene.render.resolution_y = 1024, 1536
co = np.array([v.co[:] for v in up.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
ext = np.ptp(co, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.clip_end = 1000
cam.data.ortho_scale = max(ext[2] / 0.9, ext[0] * 1.5 / 0.9)
scene.camera = cam
px_per_unit = 1536 / cam.data.ortho_scale
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0))}


def render(prefix, image_path=None):
    if image_path is None:
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'SINGLE'
        scene.display.shading.single_color = (0.6, 0.6, 0.6)
        up.materials.clear()
    else:
        scene.display.shading.light = 'FLAT'
        scene.display.shading.color_type = 'TEXTURE'
        mat = bpy.data.materials.new(os.path.basename(image_path))
        mat.use_nodes = True
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(image_path)
        tex.interpolation = 'Closest'
        mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        up.materials.clear()
        up.materials.append(mat)
    for name, d in views.items():
        cam.location = ctr + d * 300
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(OUT, f'{prefix}_{name}.png')
        bpy.ops.render.render(write_still=True)


render('guide')
render('reference', os.path.join(WORK, 'maps', 'old_color.png'))
for tier in (1, 2, 3, 4):
    paint = os.path.join(WORK, f't{tier}', 'basecolor.png')
    if os.path.exists(paint):
        render(f'previous_t{tier}', paint)
json.dump({'pieces': record, 'string_faces': len(string), 'ortho_scale': cam.data.ortho_scale,
           'px_per_unit': round(px_per_unit, 1), 'old_px_per_unit': 24.6}, open(os.path.join(OUT, 'pieces.json'), 'w'),
          indent=1)
print('PIECED done', json.dumps(record), 'px/unit %.1f' % px_per_unit, flush=True)
