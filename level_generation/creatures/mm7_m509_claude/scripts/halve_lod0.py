"""Halve the runtime LOD0 (user, 2026-10-20: "reduce tris now", all six batch-L models to about 50 %) on the textured,
rigged master, so no new texturing is needed: a Collapse Decimate is applied to the body mesh BEFORE its Armature
modifier (vertex groups and every UV layer are interpolated; game asset modelling guidelines: decimate after the
weights). Protection through the modifier's inverted vertex group: pieces under MINP triangles (eyes, teeth, buttons,
studs, whisker strips) are kept whole (weight 1), and vertices weighted more than 0.3 to a PROTECT bone get that
entry's weight (the face; on the small animals also the legs, paws and tail, which collapsed into flat blades and lost
their paws when only the face was protected), so the collapse spends its cuts on the large smooth surfaces. The ratio
is solved for RATIO of the current triangle count over the whole mesh. Other objects (the blaster prop) are untouched.
Env: HALVE_MESH (Body), RATIO (0.5), MINP (120), SEAM_W (0.8, UV-seam vertices), PROTECT (comma-separated
bone-name prefixes, each optionally =weight), PROTECT_W (0.6, the default weight), FACE (a bone whose front skin is
kept whole), FACE_DY (0.0).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
MESH = os.environ.get('HALVE_MESH', 'Body'); RATIO = float(os.environ.get('RATIO', '0.5'))
MINP = int(os.environ.get('MINP', '120')); PW = float(os.environ.get('PROTECT_W', '0.6'))
PROTECT = [(e.split('=')[0], float(e.split('=')[1]) if '=' in e else PW)
           for e in os.environ.get('PROTECT', '').split(',') if e]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects[MESH]; me = body.data


def tris(m):
    return sum(len(p.vertices) - 2 for p in m.polygons)


before = tris(me); nv = len(me.vertices)
w = np.zeros(nv)
if 'piece' in me.attributes and me.attributes['piece'].domain == 'POINT':
    pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    ft = {}
    for p in me.polygons:
        k = int(pv[p.vertices[0]]); ft[k] = ft.get(k, 0) + len(p.vertices) - 2
    small = [k for k, t in ft.items() if t < MINP]
    w[np.isin(pv, small)] = 1.0
    print('HALVE small pieces kept whole', len(small), 'tris', sum(ft[k] for k in small))
# UV seams: a vertex whose loops carry more than one UV (any layer) is weighted SEAM_W against collapse: an unprotected
# collapse across a seam smeared the texture (the dog's flank and cheek). 1.0 never collapses them but stops at
# 54-92 % on fragmented UVs (the Earth Elemental's transferred Meshy UVs put 86 % of its vertices on a seam); 0.8
# reaches 50 % on all six with no visible smear in the textured renders.
SEAM_W = float(os.environ.get('SEAM_W', '0.8'))
if SEAM_W > 0:
    seam = np.zeros(nv, bool)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    for uv in me.uv_layers:
        a = np.empty(len(me.loops) * 2); uv.data.foreach_get('uv', a); a = np.round(a.reshape(-1, 2), 5)
        first = np.full((nv, 2), np.nan)
        for li in range(len(lv)):
            v = lv[li]
            if np.isnan(first[v, 0]):
                first[v] = a[li]
            elif (first[v] != a[li]).any():
                seam[v] = True
    w[seam] = np.maximum(w[seam], SEAM_W)
    print('HALVE UV-seam vertices weighted', SEAM_W, int(seam.sum()), 'of', nv)
for prefix, pw in PROTECT:
    idx = {g.index for g in body.vertex_groups if g.name.startswith(prefix)}
    for v in me.vertices:
        if idx and sum(e.weight for e in v.groups if e.group in idx) > 0.3:
            w[v.index] = max(w[v.index], pw)
# FACE=<bone>: the front of that bone's skin (weight > 0.3, ahead of the bone's head by FACE_DY m along -Y, the model's
# front) is blocked completely (weights below 1 only reorder the cuts: at 0.6-0.95 the Blaster Guy's mouth, lips and
# brows were still merged away, user review 2026-10-20); the hair and the back of the head still reduce.
FACE = os.environ.get('FACE', '')
if FACE:
    fg = body.vertex_groups[FACE].index; rig = body.find_armature()
    fy = (rig.matrix_world @ rig.data.bones[FACE].head_local).y - float(os.environ.get('FACE_DY', '0.0'))
    face = [v.index for v in me.vertices if sum(e.weight for e in v.groups if e.group == fg) > 0.3
            and (body.matrix_world @ v.co).y < fy]
    w[face] = 1.0
    print('HALVE face vertices blocked', len(face))
g = body.vertex_groups.new(name='_halve_keep')
for i in np.nonzero(w > 0)[0]:
    g.add([int(i)], float(w[i]), 'REPLACE')
m = body.modifiers.new('halve', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = RATIO
m.vertex_group = '_halve_keep'; m.invert_vertex_group = True
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_move_to_index(modifier='halve', index=0)
bpy.ops.object.modifier_apply(modifier='halve')
body.vertex_groups.remove(body.vertex_groups['_halve_keep'])
print('HALVE', MESH, before, '->', tris(body.data), f'({tris(body.data) / before:.0%})', 'protected bones', PROTECT)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
