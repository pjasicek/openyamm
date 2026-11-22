"""Cut the cleaned guard (work/clean_v1.blend) into rigid plates, one bone each (hard-surface rule), from the joints
and cut planes in scripts/joints.json:
- body shell: boot (Foot) below the boot top, shin with the knee ring (Calf) below the ring's top, thigh (Thigh)
  below the briefs' leg opening (a plane rising from the crotch to the hip), briefs (Pelvis) below the waist band,
  waist band (Spine) below the chest's lower edge, chest (Spine2); the arm: deltoid ball and upper arm (UpperArm:
  within DELTOID of the shoulder, or lateral of arm_min_x below the shoulder) and forearm (Forearm) split by the plane
  through the elbow normal to the shoulder-wrist line;
- separate pieces: hands -> Hand, dome and gem -> Head, hip tubes -> Thigh, soles -> Foot;
- labels smoothed (majority of the face's neighbours, twice), edges between labels split, every cut loop capped
  (caps: part 3), each label decimated (DECIMATE), dark joint spheres (part 2) added at the waist, hips, knees,
  ankles and elbows, sized from the cut loops, on the parent plate.
Face attributes: `bone` (index into BONES), `part` (0 chrome shell, 1 gem, 2 joint sphere, 3 cut cap, 4 hand, 5 dome,
6 tube, 7 sole). Writes work/seg_v1.blend and work/seg_info.json, renders review/seg_*.png coloured by bone."""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'scripts', 'joints.json')))
DELTOID = 0.165
DECIMATE = {'body': 0.42, 'hand': 0.55, 'dome': 0.6, 'tube': 0.6, 'sole': 0.8}
SIDE = ('L', 'R')
BONES = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
for s in SIDE:
    BONES += [f'B_{s}_Clavicle', f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand',
              f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot']
BI = {b: i for i, b in enumerate(BONES)}


def jp(name, side='L'):
    p = Vector(J[name])
    if side == 'R':
        p.x = -p.x
    return p


bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Guard']
bm = bmesh.new(); bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# pieces by connectivity, ranked by size (clean.py's report: 0 body, 1/2 hands, 3 dome, 4/5 soles, 6 gem, 7/8 tubes)
lab = [-1] * len(bm.verts); groups = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = len(groups); g = []
    while st:
        x = st.pop(); g.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = lab[v.index]; st.append(w)
    groups.append(g)
rank = {gi: r for r, gi in enumerate(sorted(range(len(groups)), key=lambda i: -len(groups[i])))}
KIND = {0: 'body', 1: 'hand', 2: 'hand', 3: 'dome', 4: 'sole', 5: 'sole', 6: 'gem', 7: 'tube', 8: 'tube'}
bone_l = bm.faces.layers.int.new('bone'); part_l = bm.faces.layers.int.new('part')
kind_of = {}


def leg_cut_z(ax):
    return min(J['cut_leg_crotch_z'] + J['cut_leg_slope'] * ax, J['cut_leg_max_z'])


def shoulder_side(c, s):
    """> 0 on the arm side of the shoulder plane (normal out and up, through shoulder_cut)."""
    n = Vector(J['shoulder_cut_n']); p0 = Vector(J['shoulder_cut'])
    if s == 'R':
        n.x, p0.x = -n.x, -p0.x
    return (c - p0).dot(n.normalized())


def is_arm(c, s, ax):
    """The arm hangs beside the waist (lateral of arm_min_x between z 1.0 and 1.28); above that the shoulder plane."""
    if c.z <= 1.0:
        return False
    if c.z <= 1.28:
        return ax > J['arm_min_x']
    return shoulder_side(c, s) > 0


def classify(c):
    s = 'L' if c.x >= 0 else 'R'
    ax = abs(c.x)
    if is_arm(c, s, ax):
        S, E, W = jp('shoulder', s), jp('elbow', s), jp('wrist', s)
        if (c - S).dot((E - S).normalized()) < J['pauldron_depth']:
            return f'B_{s}_Clavicle'          # the deltoid ball: a pauldron on the clavicle, the arm turns under it
        n = (W - S).normalized()
        return f'B_{s}_UpperArm' if (c - E).dot(n) < 0 else f'B_{s}_Forearm'
    if ax > 0.1 and c.z < J['cut_boot_z']:
        return f'B_{s}_Foot'
    if ax > 0.1 and c.z < J['cut_knee_top_z']:
        return f'B_{s}_Calf'
    if c.z < leg_cut_z(ax) and ax > 0.02:
        return f'B_{s}_Thigh'
    if c.z < J['cut_briefs_top_z']:
        return 'B_Pelvis'
    if c.z < J['cut_chest_bottom_z']:
        return 'B_Spine'
    return 'B_Spine2'


# clean cut loops: bisect the body shell along every cut plane (restricted to the region the plane separates)
piece_l = bm.faces.layers.int.new('piece')
for f in bm.faces:
    f[piece_l] = rank[lab[f.verts[0].index]]


def bisect(sel, co, no, pieces=(0,)):
    faces = [f for f in bm.faces if f[piece_l] in pieces and sel(f.calc_center_median())]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)


for s in SIDE:
    sg = 1 if s == 'L' else -1
    side = (lambda c, sg=sg: c.x * sg > 0.08)
    bisect(lambda c, f=side: f(c) and c.z < 0.45, (0, 0, J['cut_boot_z']), (0, 0, 1))
    bisect(lambda c, f=side: f(c) and 0.5 < c.z < 0.9, (0, 0, J['cut_knee_top_z']), (0, 0, 1))
    sl = J['cut_leg_slope']
    xm = (J['cut_leg_max_z'] - J['cut_leg_crotch_z']) / sl
    bisect(lambda c, sg=sg, xm=xm: 0.0 < c.x * sg < xm + 0.02 and 0.8 < c.z < 1.25, (0, 0, J['cut_leg_crotch_z']), (-sl * sg, 0, 1))
    bisect(lambda c, sg=sg, xm=xm: c.x * sg > xm - 0.02 and c.x * sg < J['arm_min_x'] and 0.9 < c.z < 1.2, (0, 0, J['cut_leg_max_z']), (0, 0, 1))
    n = Vector(J['shoulder_cut_n']); n.x *= sg; p0 = Vector(J['shoulder_cut']); p0.x *= sg
    bisect(lambda c, sg=sg: c.x * sg > 0.2 and c.z > 1.15, p0, n)
    S, E, W = jp('shoulder', s), jp('elbow', s), jp('wrist', s)
    bisect(lambda c, sg=sg, E=E: c.x * sg > 0.3 and (c - E).length < 0.25, E, (W - S).normalized())
    dn = (E - S).normalized()
    bisect(lambda c, sg=sg, S=S: c.x * sg > 0.3 and (c - S).length < 0.3, S + dn * J['pauldron_depth'], dn)
    # the hand piece carries a long cuff up the forearm: the part on the elbow side of the wrist plane is forearm
    bisect(lambda c, sg=sg: c.x * sg > 0.3, W, (W - E).normalized(), pieces=(1, 2))
bisect(lambda c: abs(c.x) < 0.45 and 0.95 < c.z < 1.2 and abs(c.x) < 0.38, (0, 0, J['cut_briefs_top_z']), (0, 0, 1))
bisect(lambda c: abs(c.x) < 0.45 and 1.15 < c.z < 1.4 and abs(c.x) < 0.38, (0, 0, J['cut_chest_bottom_z']), (0, 0, 1))
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lab = [-1] * len(bm.verts); groups = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = len(groups); g = []
    while st:
        x = st.pop(); g.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = lab[v.index]; st.append(w)
    groups.append(g)
rank = {gi: r for r, gi in enumerate(sorted(range(len(groups)), key=lambda i: -len(groups[i])))}

for f in bm.faces:
    k = KIND.get(rank[lab[f.verts[0].index]], 'body')
    c = f.calc_center_median()
    s = 'L' if c.x >= 0 else 'R'
    kind_of[f.index] = k
    if k == 'body':
        b = classify(c); p = 0
    elif k == 'hand':
        W_, E_ = jp('wrist', s), jp('elbow', s)
        ax_ = (W_ - E_).normalized(); rel = c - E_
        radial = (rel - ax_ * rel.dot(ax_)).length
        cuff = (c - W_).dot(ax_) < 0 and radial < 0.085
        b = f'B_{s}_Forearm' if cuff else f'B_{s}_Hand'; p = 4
    elif k in ('dome', 'gem'):
        b = 'B_Head'; p = 5 if k == 'dome' else 1
    elif k == 'tube':
        b = f'B_{s}_Thigh'; p = 6
    else:
        b = f'B_{s}_Foot'; p = 7
    f[bone_l] = BI[b]; f[part_l] = p
# islands of a label smaller than 40 faces join the label they border most
for it in range(3):
    seen = set(); changed = 0
    for f in bm.faces:
        if f.index in seen or f[part_l] != 0: continue
        comp = [f]; seen.add(f.index); st = [f]
        while st:
            x = st.pop()
            for e in x.edges:
                for g in e.link_faces:
                    if g.index not in seen and g[part_l] == 0 and g[bone_l] == f[bone_l]:
                        seen.add(g.index); comp.append(g); st.append(g)
        if len(comp) >= 40: continue
        votes = {}
        cs = set(comp)
        for x in comp:
            for e in x.edges:
                for g in e.link_faces:
                    if g not in cs and g[part_l] == 0:
                        votes[g[bone_l]] = votes.get(g[bone_l], 0) + 1
        if votes:
            b = max(votes, key=votes.get)
            for x in comp:
                x[bone_l] = b
            changed += 1
    print('ISLANDS relabelled', it, changed)
# split between labels
cut = [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0][bone_l] != e.link_faces[1][bone_l]]
bmesh.ops.split_edges(bm, edges=cut)
print('CUT edges', len(cut))
# cut loops: boundary edges grouped by the bone of their face; cap them
loops = {}
for e in bm.edges:
    if e.is_boundary:
        loops.setdefault(e.link_faces[0][bone_l], []).append(e)
caps = 0
for b, es in loops.items():
    r = bmesh.ops.holes_fill(bm, edges=es, sides=0)
    tri = bmesh.ops.triangulate(bm, faces=r['faces'], quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in tri['faces']:
        f[bone_l] = b; f[part_l] = 3; caps += 1
print('CAP faces', caps, 'open edges left', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(ob.data); bm.free()
me = ob.data
# decimate per bone label and kind
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
t0 = len(me.polygons)
partv = [me.attributes['part'].data[i].value for i in range(len(me.polygons))]
bonev = [me.attributes['bone'].data[i].value for i in range(len(me.polygons))]
groups = {}
for i, (b, p) in enumerate(zip(bonev, partv)):
    k = {0: 'body', 3: 'body', 4: 'hand', 5: 'dome', 1: 'dome', 6: 'tube', 7: 'sole'}[p]
    groups.setdefault((b, k), []).append(i)
for (b, k), faces in groups.items():
    ratio = DECIMATE[k]
    if ratio >= 1.0: continue
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    pv = [me.attributes['part'].data[i].value for i in range(len(me.polygons))]
    bvv = [me.attributes['bone'].data[i].value for i in range(len(me.polygons))]
    for p in me.polygons:
        kk = {0: 'body', 3: 'body', 4: 'hand', 5: 'dome', 1: 'dome', 6: 'tube', 7: 'sole'}[pv[p.index]]
        p.select = bvv[p.index] == b and kk == k
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.decimate(ratio=ratio, use_symmetry=False)
    bpy.ops.object.mode_set(mode='OBJECT')
me = ob.data
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
me = ob.data
print('DECIMATED', t0, '->', len(me.polygons))
# joint spheres sized from the cut caps: centre at the joint, radius from the cap vertices around it
bm = bmesh.new(); bm.from_mesh(me)
bone_l = bm.faces.layers.int['bone']; part_l = bm.faces.layers.int['part']
capv = {}
for f in bm.faces:
    if f[part_l] == 3:
        capv.setdefault(f[bone_l], set()).update(v.co.copy().freeze() for v in f.verts)
JOINTS = [('waist_lo', 'spine', None, 'B_Pelvis', 'B_Spine', (1.0, 0.8, 0.45)),
          ('waist_hi', 'spine2', None, 'B_Spine', 'B_Spine2', (1.0, 0.8, 0.45))]
for s in SIDE:
    JOINTS += [(f'hip_{s}', 'hip', s, 'B_Pelvis', f'B_{s}_Thigh', (1, 1, 1)),
               (f'knee_{s}', 'knee', s, f'B_{s}_Thigh', f'B_{s}_Calf', (1, 1, 1)),
               (f'ankle_{s}', 'ankle', s, f'B_{s}_Calf', f'B_{s}_Foot', (1, 1, 1)),
               (f'elbow_{s}', 'elbow', s, f'B_{s}_UpperArm', f'B_{s}_Forearm', (1, 1, 1)),
               (f'shoulder_{s}', 'shoulder', s, f'B_{s}_Clavicle', f'B_{s}_UpperArm', (1, 1, 1))]
info = {}
for name, jn, s, parent, child, squash in JOINTS:
    if jn in ('spine', 'spine2'):
        cen = Vector(J[jn]); cen.z = J['cut_briefs_top_z'] if jn == 'spine' else J['cut_chest_bottom_z']
    else:
        cen = jp(jn, s)
    near = [v.co for v in bm.verts if (v.co - cen).length < 0.35 and any(f[part_l] != 3 for f in v.link_faces)]
    if not near:
        print('NOTHING near', name); continue
    if squash != (1, 1, 1):
        # waist: an ellipsoid inside the waist's cross-section (80 % of the inner half-widths at the cut height)
        ring = [p for p in near if abs(p.z - cen.z) < 0.03 and abs(p.x) < 0.35]
        xs = [abs(p.x - cen.x) for p in ring]; ys = [p.y for p in ring]
        cen.y = (max(ys) + min(ys)) / 2
        rad = (float(np.percentile(xs, 50)) * 0.8, (max(ys) - min(ys)) / 2 * 0.8, 0.06)
    else:
        r = min((p - cen).length for p in near) * 0.92
        rad = (r, r, r)
    m = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    for v in m['verts']:
        v.co = Vector((v.co.x * rad[0], v.co.y * rad[1], v.co.z * rad[2])) + cen
    for f in {f for v in m['verts'] for f in v.link_faces}:
        f[bone_l] = BI[parent]; f[part_l] = 2
    info[name] = {'centre': list(cen), 'radius': list(rad), 'bone': parent}
    print('SPHERE', name, [round(x, 3) for x in cen], [round(x, 3) for x in rad], parent)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
part = [me.attributes['part'].data[i].value for i in range(len(me.polygons))]
bone = [me.attributes['bone'].data[i].value for i in range(len(me.polygons))]
cnt = {}
for b in bone:
    cnt[BONES[b]] = cnt.get(BONES[b], 0) + 1
print('TRIS', len(me.polygons), 'per bone', cnt)
print('TRIS per part', {k: part.count(k) for k in range(8)})
json.dump({'bones': BONES, 'spheres': info}, open(os.path.join(HERE, 'work', 'seg_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'seg_v1.blend'))
# coloured views by bone
import colorsys
mats = []
for i, b in enumerate(BONES):
    m = bpy.data.materials.new(b)
    h = (i * 0.618) % 1.0
    m.diffuse_color = (*colorsys.hsv_to_rgb(h, 0.55, 0.95), 1)
    me.materials.append(m)
dark = bpy.data.materials.new('joint'); dark.diffuse_color = (0.08, 0.08, 0.1, 1); me.materials.append(dark)
for p in me.polygons:
    p.material_index = len(BONES) if part[p.index] in (2, 3) else bone[p.index]
C.MESH = 'Guard'
for name, (loc, tgt) in {'front': ((0, -5, 0.95), (0, 0, 0.95)), 'left': ((5, 0, 0.95), (0, 0, 0.95)),
                         'back': ((0, 5, 0.95), (0, 0, 0.95)), 'quarter': ((3.2, -3.8, 2.1), (0, 0, 0.95))}.items():
    C.render(loc, tgt, 2.1, os.path.join(HERE, 'review', f'seg_{name}.png'), res=(600, 600), floor=False,
             color='MATERIAL')
