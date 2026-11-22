"""Stage 1 (Blender): pose the source creature, bake the pose into a static mesh, add horns, stand it on a carved
plinth and save the high-detail statue (work/<id>/high.blend: objects HighFigure, HighPlinth) plus preview renders.
Model units: metres = game units / 100; origin at the plinth's bottom centre; front toward Blender -Y (glTF +Z, the
decoration's facing direction). Usage: blender -b --python build_high.py -- <id>"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sys.path.insert(0, HERE)
import posing  # noqa: E402

idol_id = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'idols.json')))[idol_id]
work = os.path.join(PROJECT, 'work', idol_id)
os.makedirs(work, exist_ok=True)

arm, body = posing.import_creature(os.path.join(REPO, cfg['source']))
posing.apply_pose(arm, cfg['pose'])
head_frame = None
if cfg.get('horns'):
    pb_head = arm.pose.bones['mixamorig:Head']
    pb_top = arm.pose.bones['mixamorig:HeadTop_End']
    head_frame = (arm.matrix_world @ pb_head.head, arm.matrix_world @ pb_top.head)
fig = posing.bake_static(arm, body)
fig.name = 'HighFigure'
me = fig.data

# Drop parts (eyes: the idol's sockets stay empty) and weld the import's seam splits.
bm = bmesh.new()
bm.from_mesh(me)
drop = {i for i, m in enumerate(me.materials) if m and m.name in cfg['drop_materials']}
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context='FACES')
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.to_mesh(me)
bm.free()
print('FIGURE faces', len(me.polygons))

# Feet centre to the origin, soles at z = 0.
zs = [v.co.z for v in me.vertices]
zmin, zmax = min(zs), max(zs)
feet = [v.co for v in me.vertices if v.co.z < zmin + 0.06 * (zmax - zmin)]
cx = (min(p.x for p in feet) + max(p.x for p in feet)) / 2
cy = (min(p.y for p in feet) + max(p.y for p in feet)) / 2
to_origin = Matrix.Translation((-cx, -cy, -zmin))
bulk = Matrix.Diagonal((cfg['bulk'][0], cfg['bulk'][1], 1.0, 1.0))
me.transform(bulk @ to_origin)


def horn_mesh(side, base, top, spec):
    """A tapered horn swept along a smooth path in the head's frame (side, up, forward = -Y)."""
    L = (top - base).length
    up = (top - base).normalized()
    fwd = Vector((0, -1, 0))
    fwd = (fwd - up * fwd.dot(up)).normalized()
    right = Vector((side, 0, 0))
    right = (right - up * right.dot(up) - fwd * right.dot(fwd)).normalized()
    root = base + up * spec['root_up'] * L + right * spec['root_side'] * L + fwd * spec['root_fwd'] * L
    cu = bpy.data.curves.new('horn', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = spec['radius'] * L
    cu.bevel_resolution = 2
    cu.resolution_u = 4
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    pts = spec['path']
    sp.points.add(len(pts) - 1)
    for i, (s, u, f) in enumerate(pts):
        p = root + right * s * L + up * u * L + fwd * f * L
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
        sp.points[i].radius = 1.0 - 0.94 * (i / (len(pts) - 1)) ** 0.9
    sp.use_endpoint_u = True
    sp.order_u = 3
    ob = bpy.data.objects.new('horn', cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    hm = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    return hm


if head_frame:
    xf = bulk @ to_origin
    base, top = xf @ head_frame[0], xf @ head_frame[1]
    me.materials.append(bpy.data.materials.new('HornStone'))
    horn_slot = len(me.materials) - 1
    bm = bmesh.new()
    bm.from_mesh(me)
    for side in (1, -1):
        hm = horn_mesh(side, base, top, cfg['horns'])
        before = len(bm.faces)
        bm.from_mesh(hm)
        bm.faces.ensure_lookup_table()
        for f_ in bm.faces[before:]:
            f_.material_index = horn_slot
        bpy.data.meshes.remove(hm)
    bm.to_mesh(me)
    bm.free()

# Scale so the highest point sits at figure_top above the plinth's top, feet sunk 2 cm into it.
zs = [v.co.z for v in me.vertices]
plinth_h = cfg['plinth']['height']
scale = (cfg['figure_top'] - plinth_h) / (max(zs) - min(zs))
me.transform(Matrix.Translation((0, 0, plinth_h - 0.02)) @ Matrix.Scale(scale, 4))
lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)])
hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
print('FIGURE scale %.3f bounds %s %s' % (scale, tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi)))


def plinth_mesh(width, height, name):
    """Stepped square plinth: base course, chamfered block, overhanging cap with a chamfered top; open bottom.
    Every ring has 12 vertices (3 segments per side) so the top is a 3 x 3 grid."""
    h = width / 2
    f = height / 0.96
    rings = [(h, 0.0), (h, 0.17 * f), (h - 0.07, 0.24 * f), (h - 0.12, 0.25 * f), (h - 0.12, 0.74 * f),
             (h - 0.05, 0.80 * f), (h - 0.03, 0.88 * f), (h - 0.09, height)]

    def square(r):
        corners = [(-r, -r), (r, -r), (r, r), (-r, r)]
        out = []
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            for s in range(3):
                out.append((a[0] + (b[0] - a[0]) * s / 3, a[1] + (b[1] - a[1]) * s / 3))
        return out

    bm = bmesh.new()
    loops = [[bm.verts.new((x, y, z)) for x, y in square(r)] for r, z in rings]
    for a, b in zip(loops, loops[1:]):
        for i in range(12):
            j = (i + 1) % 12
            bm.faces.new((a[i], a[j], b[j], b[i]))
    top, r = loops[-1], rings[-1][0]
    inner = [bm.verts.new((x, y, height)) for x, y in square(r / 3)[::3]]
    # grid rows: ring index layout 0..11 runs (-r,-r) -> (r,-r) -> (r,r) -> (-r,r)
    g = [[top[0], top[1], top[2], top[3]],
         [top[11], inner[0], inner[1], top[4]],
         [top[10], inner[3], inner[2], top[5]],
         [top[9], top[8], top[7], top[6]]]
    for j in range(3):
        for i in range(3):
            bm.faces.new((g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


pm = plinth_mesh(cfg['plinth']['width'], plinth_h, 'HighPlinth')
plinth = bpy.data.objects.new('HighPlinth', pm)
bpy.context.scene.collection.objects.link(plinth)
stone = bpy.data.materials.new('PlinthStone')
pm.materials.append(stone)
# outward normals: the open bottom confuses recalc on some rings; check the top face points up
top_up = max(pm.polygons, key=lambda p: p.center.z).normal.z
if top_up < 0:
    pm.flip_normals()
print('PLINTH faces', len(pm.polygons))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'high.blend'))

# Preview renders (workbench) of the high statue.
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.5, 0.5, 0.52)
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 500, 700
cam_data = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.lens = 50
centre = Vector((0, 0, 3.9))
for view, az in (('front', 0), ('q', 35), ('side', 90), ('back', 160)):
    a = math.radians(az)
    eye = Vector((math.sin(a) * 12, -math.cos(a) * 12, 1.7))
    cam.location = eye
    cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(work, f'high_{view}.png')
    bpy.ops.render.render(write_still=True)
print('HIGH_DONE')
