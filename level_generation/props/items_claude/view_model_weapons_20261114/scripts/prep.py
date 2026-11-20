"""Step 3 (README.md): the UV layout of one weapon model, its Meshy upload and the Codex guides.

Usage: blender --background --python prep.py -- <kind> [max_aspect] [--upload-only]
(--upload-only: the locked layout.blend kept, only the upload and the guides written again)

Reads work/<kind>/model.blend (build.py) and writes into work/<kind>/:
  layout.blend        the model with its UVs (locked once an upload went to Meshy: sparrow packs differently per run)
  uv_report.json      uv_atlas report plus the segmentation cuts
  layout_measure.glb  the assembled model in glTF space with a grey 2048 placeholder (texture_quality.py, gutter_fill.py)
  upload.glb          the Meshy upload: the model cut into kinds.py's pieces, stood side by side (same UVs, no material)
  guide_<view>.png    plain grey orthographic renders of the upload, 1024 x 1536 (portrait) or 1536 x 1024 (landscape)

Layout: uv_atlas.unwrap() defaults (PartUV charts, seam pass, sparrow), the head (faces above kinds.py head_z) 1.4x
denser; then islands longer than max_aspect times their width (the shaft's long cylinders) are cut into equal pieces
and everything is repacked with sparrow (the Oblivion skins' segment step).
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
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas  # noqa: E402
from kinds import KINDS  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
UPLOAD_ONLY = '--upload-only' in argv
argv = [a for a in argv if a != '--upload-only']
KIND = argv[0]
MAX_ASPECT = float(argv[1]) if len(argv) > 1 else 4.0
CFG = KINDS[KIND]
OUT = os.path.join(PROJECT, 'work', KIND)

def layout():
    global obj, me, report
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'model.blend'))
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    me = obj.data
    region = np.array([d.value for d in me.attributes['region'].data])
    centre_z = np.array([p.center.z for p in me.polygons])

    # The head's vertex group (denser UVs).
    head = obj.vertex_groups.new(name='Head')
    head_verts = sorted({v for p in me.polygons if p.center.z > CFG['head_z'] for v in p.vertices})
    if head_verts:
        head.add(head_verts, 1.0, 'REPLACE')

    report = uv_atlas.unwrap(obj, head_groups=('Head',), head_factor=1.4 if head_verts else 1.0)
    print('UV_REPORT', json.dumps({k: report[k] for k in report if k in ('atlas', 'charts_used', 'packer_used',
                                                                        'fallbacks', 'islands')}), flush=True)
    region = np.array([d.value for d in me.attributes['region'].data])

    # Segment long islands and repack.
    tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
    loops = np.array([p.loop_indices[:] for p in me.polygons], np.int64)
    uvl = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float64)
    uv = uvl[loops]
    island = uv_atlas._islands(uv, tri)
    new_island = island.copy()
    next_id = island.max() + 1
    cuts = []
    for i in np.unique(island):
        faces = np.nonzero(island == i)[0]
        pts = uv[faces].reshape(-1, 2)
        ctr = pts.mean(0)
        w, v = np.linalg.eigh(np.cov((pts - ctr).T))
        axis, side = v[:, 1], v[:, 0]
        along = (pts - ctr) @ axis
        length, width = np.ptp(along), max(np.ptp((pts - ctr) @ side), 1e-9)
        k = int(math.ceil(length / width / MAX_ASPECT))
        if k <= 1:
            continue
        cen = (uv[faces].mean(1) - ctr) @ axis
        edges = np.linspace(along.min(), along.max(), k + 1)
        piece = np.clip(np.searchsorted(edges, cen, side='right') - 1, 0, k - 1)
        for p in range(1, k):
            new_island[faces[piece == p]] = next_id
            next_id += 1
        cuts.append({'island': int(i), 'faces': int(len(faces)), 'aspect': round(float(length / width), 2), 'pieces': k})
    print('SEGMENT cuts', len(cuts), flush=True)
    if cuts:
        new_island = np.unique(new_island, return_inverse=True)[1].ravel()
        packed, kk = uv_atlas._sparrow(uv, new_island, 2048, 1.0, 4, 60, 5, 0.66)
        packed = np.asarray(packed, np.float64).reshape(-1, 3, 2)
        layer = me.uv_layers['UVMap']
        for f in range(len(tri)):
            for c in range(3):
                layer.data[int(loops[f, c])].uv = packed[f, c]
        me.update()
        uv = packed
    use = float(np.abs(np.cross(np.c_[uv[:, 1] - uv[:, 0], np.zeros(len(uv))],
                                np.c_[uv[:, 2] - uv[:, 0], np.zeros(len(uv))])[:, 2]).sum() / 2)
    report['segment'] = {'max_aspect': MAX_ASPECT, 'cuts': cuts, 'islands': int(new_island.max() + 1),
                         'uv_sum': round(use, 4)}
    json.dump(report, open(os.path.join(OUT, 'uv_report.json'), 'w'), indent=1, default=str)
    print('SEGMENT islands', int(new_island.max() + 1), 'uv sum', round(use, 4), flush=True)

    img = bpy.data.images.new(f'{KIND}_placeholder', 2048, 2048)
    img.pixels[:] = np.full(2048 * 2048 * 4, 0.5, np.float32)
    img.filepath_raw = os.path.join(OUT, 'placeholder.png')
    img.file_format = 'PNG'
    img.save()
    mat = bpy.data.materials.new('placeholder')
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    me.materials.clear()
    me.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'layout.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'layout_measure.glb'), use_selection=True, export_format='GLB',
                              export_yup=True, export_animations=False)



if UPLOAD_ONLY:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'layout.blend'))
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    me = obj.data
    report = json.load(open(os.path.join(OUT, 'uv_report.json')))
else:
    layout()

# The upload: pieces split apart and stood side by side (left to right in kinds.py order), bottoms level.
bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
piece_of = np.zeros(len(bm.faces), np.int32)
for f in bm.faces:
    # The middle of the face's height: both triangles of a lathe quad land in the same piece.
    zs = [v.co.z for v in f.verts]
    z = (min(zs) + max(zs)) / 2
    piece_of[f.index] = next(i for i, (lo, hi) in enumerate(CFG['pieces']) if lo <= z < hi)
split = [e for e in bm.edges if len({piece_of[f.index] for f in e.link_faces}) > 1]
bmesh.ops.split_edges(bm, edges=split)
bm.faces.ensure_lookup_table()
pieces = []
for i in range(len(CFG['pieces'])):
    verts = list({v for f in bm.faces if piece_of[f.index] == i for v in f.verts})
    pieces.append(verts)
x = 0.0
gap = 1.5
for i, verts in enumerate(pieces):
    co = np.array([v.co for v in verts])
    lo, hi = co.min(0), co.max(0)
    shift = Vector((x - lo[0], 0.0, -lo[2]))
    for v in verts:
        v.co += shift
    x += (hi[0] - lo[0]) + gap
total = np.array([v.co for v in bm.verts])
mid = (total.min(0) + total.max(0)) / 2
for v in bm.verts:
    v.co.x -= mid[0]
up = bpy.data.meshes.new('upload')
bm.to_mesh(up)
bm.free()
upload = bpy.data.objects.new('upload', up)
bpy.context.scene.collection.objects.link(upload)
obj.hide_render = True
for o in bpy.data.objects:
    o.select_set(o == upload)
bpy.context.view_layer.objects.active = upload
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.6)
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
co = np.array([v.co for v in up.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
ext = np.ptp(co, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.clip_end = 1000
scene.camera = cam
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)),
         'right': Vector((-1, 0, 0)), 'top': Vector((0, 0, 1)), 'bottom': Vector((0, 0, -1))}
guides = {}
for name in CFG['views']:
    d = views[name]
    # The frame's long side follows the view's larger extent.
    across = [i for i in range(3) if abs(d[i]) < 0.5]
    w_ext, h_ext = (ext[0], ext[1]) if name in ('top', 'bottom') else (ext[across[0]], ext[2])
    portrait = h_ext >= w_ext
    scene.render.resolution_x, scene.render.resolution_y = (1024, 1536) if portrait else (1536, 1024)
    # ortho_scale spans the frame's larger side; the other side is 2/3 of it.
    big, small = (h_ext, w_ext) if portrait else (w_ext, h_ext)
    cam.data.ortho_scale = max(big / 0.9, small * 1.5 / 0.9)
    cam.location = ctr + d * 300
    up_vec = 'Y'
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    path = os.path.join(OUT, f'guide_{name}.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    guides[name] = {'size': [scene.render.resolution_x, scene.render.resolution_y],
                    'ortho_scale': cam.data.ortho_scale}
json.dump({'pieces': CFG['pieces'], 'guides': guides}, open(os.path.join(OUT, 'upload.json'), 'w'), indent=1)
print('PREP done', KIND, len(me.polygons), 'tris', 'atlas', report.get('atlas'))
