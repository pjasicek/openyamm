"""FD-02's lectern (D-63 polish, lane S session 10): a carved wooden reading stand in the throne's wood (the Throne of
Legends' own atlas, xeen_throne_claude/work/throne_img0.png: plain wood strip, fluted pilaster, carved panel) with MM9's
open book (mm9_deco_bookflat, copied into the Xeen model, D-44) lying on its sloped desk. Units: game units / 100 in
Blender (the binding height sets the game size). Origin at the foot's bottom centre; the reader's side is -Y in
Blender (glTF +Z, the binding's facing with yaw_offset -90 deg).
Usage: blender -b --python build.py -- [--preview]"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ATLAS = os.path.join(REPO, 'level_generation/decorations/xeen_throne_claude/work/throne_img0.png')
BOOK = os.path.join(REPO, 'assets_source/worlds/mm9/models/mm9_deco_bookflat.glb')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
U = 0.01
# atlas regions (u0, v0, u1, v1) in Blender UV space (v up): plain wood, fluted pilaster, carved panel
WOOD = (0.005, 0.0, 0.13, 1.0)
FLUTE = (0.17, 0.06, 0.37, 0.98)
CARVED = (0.41, 0.53, 0.69, 0.98)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def wood_material():
    m = bpy.data.materials.new('lectern_wood')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(ATLAS)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.62
    bsdf.inputs['Metallic'].default_value = 0.0
    return m


def box(bm, uv, lo, hi, regions, xf=Matrix()):
    """Axis box lo..hi (units) transformed by xf; regions: dict face-normal-key -> atlas rect, default WOOD.
    Each face's UVs fill its rect along the face's two extents (keeps the grain vertical on side faces)."""
    lo, hi = Vector(lo) * U, Vector(hi) * U
    corners = [Vector((x, y, z)) for z in (lo.z, hi.z) for y in (lo.y, hi.y) for x in (lo.x, hi.x)]
    vs = [bm.verts.new(xf @ c) for c in corners]
    faces = {'-z': (0, 2, 3, 1), '+z': (4, 5, 7, 6), '-y': (0, 1, 5, 4), '+y': (2, 6, 7, 3), '-x': (0, 4, 6, 2),
             '+x': (1, 3, 7, 5)}
    for key, idx in faces.items():
        f = bm.faces.new([vs[i] for i in idx])
        u0, v0, u1, v1 = regions.get(key, WOOD)
        # local 2D coordinates on the untransformed box: pick the two axes spanning the face
        axes = {'z': (0, 1), 'y': (0, 2), 'x': (1, 2)}[key[1]]
        pts = [corners[i] for i in idx]
        a0 = [p[axes[0]] for p in pts]
        a1 = [p[axes[1]] for p in pts]
        for loop, p in zip(f.loops, pts):
            s = (p[axes[0]] - min(a0)) / max(max(a0) - min(a0), 1e-6)
            t = (p[axes[1]] - min(a1)) / max(max(a1) - min(a1), 1e-6)
            if key[1] == 'z':
                loop[uv].uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)
            else:   # grain up the side faces
                loop[uv].uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)


me = bpy.data.meshes.new('xeen_lectern')
bm = bmesh.new()
uv = bm.loops.layers.uv.new('UVMap')
box(bm, uv, (-22, -18, 0), (22, 18, 6), {})                                        # foot
box(bm, uv, (-16, -13, 6), (16, 13, 10), {})                                       # plinth step
box(bm, uv, (-6, -6, 10), (6, 6, 86), {'-y': FLUTE, '+y': FLUTE, '-x': FLUTE, '+x': FLUTE})   # post
box(bm, uv, (-20, -15, 86), (20, 15, 98), {'-y': CARVED, '+y': CARVED})           # skirt under the desk
tilt = math.radians(24)
desk_xf = Matrix.Translation((0, 0, 104 * U)) @ Matrix.Rotation(tilt, 4, 'X')     # high edge at +Y (the back)
box(bm, uv, (-27, -20, -3), (27, 20, 1), {}, desk_xf)                              # sloped desk board
box(bm, uv, (-27, -21.5, 1), (27, -19, 4), {}, desk_xf)                             # the lip at its low edge
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me)
bm.free()
lectern = bpy.data.objects.new('xeen_lectern', me)
scene.collection.objects.link(lectern)
me.materials.append(wood_material())
for p in me.polygons:
    p.use_smooth = False

# the open book on the desk, lying in the slope (spine up the slope)
bpy.ops.import_scene.gltf(filepath=BOOK)
book_parts = [o for o in scene.objects if o.type == 'MESH' and o is not lectern]
for o in book_parts:
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix()
    o.data.transform(Matrix.Scale(0.78, 4))
    o.data.transform(Matrix.Rotation(math.radians(float(os.environ.get('BOOK_YAW', '0'))), 4, 'Z'))
    o.data.transform(desk_xf @ Matrix.Translation((0, 0, 1.2 * U)))
for o in list(scene.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [lectern] + book_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = lectern
bpy.ops.object.join()
lectern.name = lectern.data.name = 'xeen_lectern'
while len(lectern.data.uv_layers) > 1:
    lectern.data.uv_layers.remove(lectern.data.uv_layers[-1])
co = [lectern.matrix_world @ v.co for v in lectern.data.vertices]
lo = [min(c[i] for c in co) / U for i in range(3)]
hi = [max(c[i] for c in co) / U for i in range(3)]
print('BOUNDS', [round(x, 1) for x in lo], [round(x, 1) for x in hi], 'TRIS',
      sum(len(p.vertices) - 2 for p in lectern.data.polygons))

if '--preview' in argv:
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 4
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new('w')
    scene.world.color = (0.3, 0.3, 0.32)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 480
    c = Vector((0, 0, 0.6))
    for tag, d in (('q', (0.5, -0.8, 0.45)), ('front', (0.0, -1.0, 0.35)), ('side', (1.0, 0.0, 0.2))):
        d = Vector(d).normalized()
        cam.location = c + d * 2.2
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(PROJECT, 'work', f'preview_{tag}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.objects.remove(sun, do_unlink=True)

lectern.select_set(True)
out = os.path.join(PROJECT, 'export', 'xeen_deco_lectern.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_normals=True, export_animations=False, export_skins=False,
                          export_image_format='AUTO', export_apply=True, export_vertex_color='NONE')
print('EXPORTED', out)
