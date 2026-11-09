"""v2 UVs for the body and head texture domains (Blender): unwrap the +X half only, then give every -X face the UVs
of its mirror face, so both halves share one island set (mirrored halves may overlap: the paint is symmetric, and
the half gets twice the texel density). Wing faces keep the procedural layout from scripts/build_wing.py.

Body: charts by dominant bone; the half neck, trunk and tail are discs (open on the midline) and unwrap angle-based
in one piece each, legs, feet and crest shells by smart projection; islands at one density, concave packing (52 %
of the square instead of 18-27 % from smart projection alone). Head: smart projection charts re-unwrapped
angle-based, as v1. Any folded triangles are cut into their own charts and re-unwrapped until no texel is covered
twice (2048 raster). Usage: uv_v2.py -- <in.blend> <out.blend>"""
import bpy, bmesh, json, math, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
me = o.data
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
me.uv_layers.active = me.uv_layers['UVMap']
centre_x = np.array([f.center.x for f in me.polygons])
side_a = centre_x >= -1e-7


def overlapping(faces, n=2048):
    me.calc_loop_triangles(); uv = me.uv_layers.active.data
    owner = np.full((n, n), -1, np.int64); bad = set()
    for t in me.loop_triangles:
        if not bool(faces(me.polygons[t.polygon_index])): continue
        p0, p1, p2 = [np.array(uv[l].uv) * n for l in t.loops]
        den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(den) < 1e-9: continue
        lo = np.maximum(np.floor(np.minimum(np.minimum(p0, p1), p2)).astype(int), 0)
        hi = np.minimum(np.ceil(np.maximum(np.maximum(p0, p1), p2)).astype(int), n - 1)
        x, y = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w0 = ((p1[1] - p2[1]) * (x - p2[0]) + (p2[0] - p1[0]) * (y - p2[1])) / den
        w1 = ((p2[1] - p0[1]) * (x - p2[0]) + (p0[0] - p2[0]) * (y - p2[1])) / den
        m = (w0 > 1e-6) & (w1 > 1e-6) & (1 - w0 - w1 > 1e-6)
        iy, ix = (y[m] - .5).astype(int), (x[m] - .5).astype(int); prev = owner[iy, ix]
        if (prev >= 0).any():
            bad.add(t.polygon_index); bad.update(int(me.loop_triangles[q].polygon_index) for q in np.unique(prev[prev >= 0]))
        owner[iy, ix] = t.index
    return sorted(bad)


def repair(faces, margin):
    for attempt in range(16):
        bpy.ops.object.mode_set(mode='OBJECT'); bad = overlapping(faces)
        print('UV pass', attempt, 'overlapping faces', len(bad), flush=True)
        if not bad: break
        b = bmesh.new(); b.from_mesh(me); b.faces.ensure_lookup_table()
        for fi in bad:
            for e in b.faces[fi].edges: e.seam = True
        b.to_mesh(me); b.free(); select(faces); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
        for p in me.polygons: p.select = bool(p.index in set(bad))
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_linked(delimit={'SEAM'})
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
        select(faces); bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    else:
        raise RuntimeError('UV folds remain')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.mark_seam(clear=True); bpy.ops.object.mode_set(mode='OBJECT')


def select(faces):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.select = bool(faces(p))
    bpy.ops.object.mode_set(mode='EDIT')


def unwrap_smart(faces, margin):
    select(faces)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, area_weight=0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    repair(faces, margin)


def unwrap_charts(faces, margin):
    """Body: the +X half of neck, trunk and tail is a disc (open along the midline), so each unwraps in one
    angle-based chart; legs, feet and crest shells take smart projection; then islands are scaled to one density."""
    names = {g.index: g.name for g in o.vertex_groups}
    dom = [names[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices]
    def chart(n):
        if n.startswith('Neck'): return 'neck'
        if n in ('Spine1', 'Spine2', 'Root'): return 'trunk'
        if n.startswith('Tail'): return 'tail' if int(n[4:]) <= 5 else 'tail2'
        if 'Fore' in n or 'Hind' in n: return 'leg_' + n[1:]
        return 'other'
    from collections import Counter
    lab = [Counter(chart(dom[v]) for v in f.vertices).most_common(1)[0][0] for f in me.polygons]
    pa = np.array([v.value for v in me.attributes['part'].data]); shell = [pa[list(f.vertices)].max() > 0 for f in me.polygons]
    b = bmesh.new(); b.from_mesh(me); b.faces.ensure_lookup_table()
    for e in b.edges:
        fs = [f.index for f in e.link_faces]; e.seam = len(fs) == 2 and lab[fs[0]] != lab[fs[1]]
    b.to_mesh(me); b.free()
    big = lambda f: faces(f) and lab[f.index] in ('neck', 'trunk', 'tail', 'tail2') and not shell[f.index]
    select(big); bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
    select(lambda f: faces(f) and not big(f))
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, area_weight=0, correct_aspect=True, scale_to_bounds=False)
    select(faces); bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    repair(faces, margin)


unwrap_charts(lambda f: f.material_index == 0 and side_a[f.index], .003)
unwrap_smart(lambda f: f.material_index == 1 and side_a[f.index], .004)

# mirror copy
co = np.array([v.co[:] for v in me.vertices]); kd = kdtree.KDTree(len(co))
for i, p in enumerate(co): kd.insert(Vector(p), i)
kd.balance(); partner = np.array([kd.find(Vector((-p[0], p[1], p[2])))[1] for p in co])
key = {frozenset(f.vertices): f.index for f in me.polygons if side_a[f.index]}
uv = me.uv_layers.active.data; copied = 0; missing = 0
for f in me.polygons:
    if side_a[f.index] or f.material_index == 2: continue
    src = key.get(frozenset(partner[list(f.vertices)].tolist()))
    if src is None: missing += 1; continue
    sp = me.polygons[src]; by_vertex = {me.loops[l].vertex_index: l for l in sp.loop_indices}
    for l in f.loop_indices:
        uv[l].uv = uv[by_vertex[partner[me.loops[l].vertex_index]]].uv; copied += 1
assert missing == 0, missing
me.calc_loop_triangles(); stats = {}
for slot, label in enumerate(['body', 'head', 'wings']):
    ratios = []
    for t in me.loop_triangles:
        if t.material_index != slot or not side_a[t.polygon_index]: continue
        xyz = np.array([me.vertices[i].co[:] for i in t.vertices]); q = np.array([uv[i].uv[:] for i in t.loops])
        ar = np.linalg.norm(np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])) * .5; b = abs(np.linalg.det(np.column_stack([q[1] - q[0], q[2] - q[0]]))) * .5
        if ar > 1e-10: ratios.append(b / ar)
    stats[label] = {'triangles_half': len(ratios), 'uv_area_per_m2_percentiles_1_50_99': np.percentile(ratios, [1, 50, 99]).tolist(),
                    'texels_per_m_median': float(np.sqrt(np.median(ratios)) * 2048)}
stats['mirrored_loops'] = copied
(P / 'work/v2/uv_report.json').write_text(json.dumps(stats, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=a[1]); print('UV_V2', stats)
