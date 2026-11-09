"""45 % step -> retexture master for the male peasant (user 2026-10-13: regenerate head and body textures).
In: work/ladder.blend (Cand_45) and the accepted master ../mm6_pman_claude_20261013/work/textured_uv.blend (pieces:
0 tunic, 1 face/neck skin, 2 hair, 3 leggings, 4/5 arms, 6/7 boots, 10 belt, 11 buckle; every piece is one connected
component; head set = pieces 1 and 2). Every reduced component takes its majority source piece (nearest source vertex
at rest). Fresh UVs: UVMap over the whole figure (Meshy's body return sees the head too; only the body faces use it),
HeadUV over the head faces alone. REA_SOURCE_PIECES (default "1") keeps those pieces at source density with their
source weights: at 45 % the lips collapsed into a notch (review/r45/face_compare.png), and the face is what players look
at. Out: work/master_r45.blend, texturing/pman_{body,head}_upload.glb, work/master.json."""
import json
import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(os.path.dirname(HERE), 'mm6_pman_claude_20261013', 'work', 'textured_uv.blend')
CAND = os.environ.get('REA_CAND', 'Cand_45')
HEAD_PIECES = {1, 2}


def rest(rig):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=SOURCE)
rest(bpy.data.objects['Rig'])
src = bpy.data.objects['Body']
sco = [src.matrix_world @ v.co for v in src.data.vertices]
spiece = [a.value for a in src.data.attributes['piece'].data]

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; rest(rig)
tree = kdtree.KDTree(len(sco))
for i, c in enumerate(sco):
    tree.insert(c, i)
tree.balance()
cand = bpy.data.objects[CAND]; me = cand.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
near = [spiece[tree.find(cand.matrix_world @ v.co)[1]] for v in bm.verts]
piece = [0] * len(bm.verts); seen = set(); components = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    vals, counts = np.unique([near[i] for i in comp], return_counts=True)
    label = int(vals[counts.argmax()])
    for i in comp:
        piece[i] = label
    components.append((len(comp), label, round(float(counts.max() / len(comp)), 3)))
bm.free()
pa = me.attributes.get('piece') or me.attributes.new('piece', 'INT', 'POINT')
pa.data.foreach_set('value', piece)

# source pieces replace their reduced components (whole components: no seam)
KEEP = {int(x) for x in os.environ.get('REA_SOURCE_PIECES', '1').split(',') if x}
if KEEP:
    b = bmesh.new(); b.from_mesh(me); pl = b.verts.layers.int['piece']
    bmesh.ops.delete(b, geom=[v for v in b.verts if v[pl] in KEEP], context='VERTS'); b.to_mesh(me); b.free()
    with bpy.data.libraries.load(SOURCE, link=False) as (data_from, data_to):
        data_to.objects = ['Body']
    part = data_to.objects[0]; part.name = 'SourcePart'; bpy.context.scene.collection.objects.link(part)
    part.parent = None; part.matrix_world = cand.matrix_world.copy()
    b = bmesh.new(); b.from_mesh(part.data); pl = b.verts.layers.int['piece']
    bmesh.ops.delete(b, geom=[v for v in b.verts if v[pl] not in KEEP], context='VERTS'); b.to_mesh(part.data); b.free()
    for m in list(part.modifiers):
        part.modifiers.remove(m)
    for name in [l.name for l in part.data.uv_layers][1:]:
        part.data.uv_layers.remove(part.data.uv_layers[name])
    for name in [a.name for a in part.data.attributes if a.name in ('head', 'finger', 'orig_co')]:
        part.data.attributes.remove(part.data.attributes[name])
    part.data.materials.clear()
    for m in me.materials:
        part.data.materials.append(m)
    for g in part.vertex_groups:
        if cand.vertex_groups.get(g.name) is None:
            cand.vertex_groups.new(name=g.name)
    for o in bpy.data.objects:
        o.select_set(o in (cand, part))
    bpy.context.view_layer.objects.active = cand
    bpy.ops.object.join()
    me = cand.data
    piece = [a.value for a in me.attributes['piece'].data]
    print('SOURCE PIECES', sorted(KEEP), 'triangles now', sum(len(p.vertices) - 2 for p in me.polygons))
head = [int(piece[p.vertices[0]] in HEAD_PIECES) for p in me.polygons]
ha = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
ha.data.foreach_set('value', head)

# fresh UVs
for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
me.uv_layers.new(name='UVMap'); me.uv_layers.new(name='HeadUV')
for o in bpy.data.objects:
    o.select_set(o == cand)
bpy.context.view_layer.objects.active = cand


def overlapping(layer, faces, n=1024):
    """Faces whose UV triangles cover a texel centre another triangle already covers (1024 raster)."""
    me.calc_loop_triangles(); uv = me.uv_layers[layer].data
    owner = np.full((n, n), -1, np.int64); bad = set()
    for t in me.loop_triangles:
        if not faces(me.polygons[t.polygon_index]):
            continue
        a, b2, c = [np.array(uv[l].uv) * n for l in t.loops]
        den = (b2[1] - c[1]) * (a[0] - c[0]) + (c[0] - b2[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        lo = np.maximum(np.floor(np.minimum(np.minimum(a, b2), c)).astype(int), 0)
        hi = np.minimum(np.ceil(np.maximum(np.maximum(a, b2), c)).astype(int), n - 1)
        x, y = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w0 = ((b2[1] - c[1]) * (x - c[0]) + (c[0] - b2[0]) * (y - c[1])) / den
        w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
        m = (w0 > 1e-6) & (w1 > 1e-6) & (1 - w0 - w1 > 1e-6)
        iy, ix = (y[m] - .5).astype(int), (x[m] - .5).astype(int)
        prev = owner[iy, ix]
        if (prev >= 0).any():
            bad.add(t.polygon_index)
            bad.update(int(me.loop_triangles[p].polygon_index) for p in np.unique(prev[prev >= 0]))
        owner[iy, ix] = t.index
    return sorted(bad)


def unwrap(layer, faces, margin):
    me.uv_layers.active = me.uv_layers[layer]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = faces(p)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, area_weight=0, correct_aspect=True,
                             scale_to_bounds=False)
    # smart-project charts fold on curved shells (hair, ears): keep its charts as seams, re-unwrap them angle-based
    bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    # folds remain inside hair charts: cut every overlapping triangle into its own chart, re-unwrap, repeat
    for attempt in range(6):
        bpy.ops.object.mode_set(mode='OBJECT')
        bad = overlapping(layer, faces)
        print('UV', layer, 'pass', attempt, 'overlapping faces', len(bad), flush=True)
        if not bad:
            break
        b = bmesh.new(); b.from_mesh(me); b.faces.ensure_lookup_table()
        for fi in bad:
            for e in b.faces[fi].edges:
                e.seam = True
        b.to_mesh(me); b.free()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
        bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    else:
        raise RuntimeError(f'{layer}: UV folds remain')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.mark_seam(clear=True)
    bpy.ops.object.mode_set(mode='OBJECT')


unwrap('UVMap', lambda p: True, .004)
unwrap('HeadUV', lambda p: bool(head[p.index]), .006)
me.uv_layers.active = me.uv_layers['UVMap']
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
bpy.data.objects.remove(bpy.data.objects['Body'], do_unlink=True)
for o in list(bpy.data.objects):
    if o.name.startswith('Cand_'):
        if o is not cand:
            bpy.data.objects.remove(o, do_unlink=True)
cand.name = 'Body'; cand.hide_render = False


def export(which, out, layer):
    ob = cand.copy(); ob.data = me.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = cand.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    b = bmesh.new(); b.from_mesh(ob.data); hl = b.faces.layers.int['head']
    if which == 'head':
        bmesh.ops.delete(b, geom=[f for f in b.faces if f[hl] == 0], context='FACES')
        bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    b.to_mesh(ob.data); b.free()
    for name in [u.name for u in ob.data.uv_layers if u.name != layer]:
        ob.data.uv_layers.remove(ob.data.uv_layers[name])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False,
                              export_attributes=False)
    n = len(ob.data.polygons); bpy.data.objects.remove(ob, do_unlink=True)
    return n


os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
counts = {'body_upload': export('body', os.path.join(HERE, 'texturing', 'pman_body_upload.glb'), 'UVMap'),
          'head_upload': export('head', os.path.join(HERE, 'texturing', 'pman_head_upload.glb'), 'HeadUV')}
report = {'source_pieces': sorted(KEEP), 'triangles': len(me.polygons), 'head_faces': int(sum(head)), 'components': components, **counts}
json.dump(report, open(os.path.join(HERE, 'work', 'master.json'), 'w'), indent=1)
bpy.context.view_layer.objects.active = cand
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
print('MASTER', json.dumps({k: v for k, v in report.items() if k != 'components'}), report['components'])
