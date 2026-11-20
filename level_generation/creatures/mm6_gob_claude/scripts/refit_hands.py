"""Refit the finger chains to the actual goblin fingers (thumb + three clawed fingers) and rebuild finger weights.

The MPFB proxy fit bunched all finger chains onto one or two real fingers, so curling produced a crumpled lump and
the fist could not close around the sword grip. Per hand:
  1. surface (geodesic) distance from the wrist ring over the Body shell; fingertips = local maxima,
  2. each vertex is assigned to its nearest tip (multi-source geodesic); a finger region starts at its web (crotch),
  3. joints are placed on the region's centre curve; the knuckle sits a quarter finger-length back inside the palm,
  4. bone rolls make local +X curl toward the palm (Z axis = palm direction),
  5. finger weights are rebuilt along each chain with cross-fades at the joints; palm keeps its hand/forearm weights.
Unused Mixamo finger chains (a fourth finger) are parked inside the palm with no weights.
Args: mode ('analyze' renders only, 'apply' edits and saves the blend).
"""
import bpy, bmesh, sys, os, json, heapq, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

mode = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']; me = mesh.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
body_v = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if part[p.index] == PARTS.index('Body'):
        body_v[list(p.vertices)] = True
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
adj = [[] for _ in me.vertices]
for e in me.edges:
    a, b = e.vertices
    if body_v[a] and body_v[b]:
        d = float(np.linalg.norm(co[a] - co[b])); adj[a].append((b, d)); adj[b].append((a, d))
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')


def dijkstra(mask, seeds):
    dist = {i: 0.0 for i in seeds}; owner = {i: i for i in seeds}
    pq = [(0.0, i) for i in seeds]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist.get(i, 1e9):
            continue
        for j, w in adj[i]:
            if mask[j] and d + w < dist.get(j, 1e9):
                dist[j] = d + w; owner[j] = owner[i]; heapq.heappush(pq, (d + w, j))
    return dist, owner


def analyse(side):
    fa = rig.data.bones[f'mixamorig:{side}ForeArm']
    wrist = np.array(rig.matrix_world @ fa.tail_local)
    axis = np.array((rig.matrix_world @ fa.tail_local) - (rig.matrix_world @ fa.head_local)); axis /= np.linalg.norm(axis)
    proj = (co - wrist) @ axis
    H = body_v & (proj > -0.03) & (np.linalg.norm(co - wrist, axis=1) < 0.30)
    lo = proj[H].min()
    seeds = [i for i in np.nonzero(H)[0] if proj[i] < lo + 0.012]
    dist, _ = dijkstra(H, seeds)
    D = np.full(len(co), -1.0)
    for i, d in dist.items():
        D[i] = d
    reach = D > 0
    tips = []
    for i in np.argsort(-D):
        if D[i] < 0.10:
            break
        if all(np.linalg.norm(co[i] - co[t]) > 0.045 for t in tips):
            near = np.nonzero(reach & (np.linalg.norm(co - co[i], axis=1) < 0.045))[0]
            if D[i] >= D[near].max() - 1e-9:
                tips.append(int(i))
    tips = tips[:5]
    tdist, owner = dijkstra(H & reach, tips)
    own = np.full(len(co), -1)
    for i, t in owner.items():
        own[i] = t
    fingers = []
    for t in tips:
        region = np.nonzero(own == t)[0]
        rs = set(region.tolist())
        border = [i for i in region if any(own[j] not in (t, -1) for j, _ in adj[i])]
        web = max(D[i] for i in border) if border else D[region].min()
        fingers.append({'tip': t, 'region': region, 'web': float(web), 'length': float(D[t] - web)})
    # thumb = deepest web (separates nearest to the wrist)
    fingers.sort(key=lambda f: f['web'])
    thumb = fingers[0]
    centre = co[np.array([f['tip'] for f in fingers])].mean(0)
    f_dir = centre - wrist; f_dir /= np.linalg.norm(f_dir)
    t_side = co[thumb['tip']] - wrist; t_side -= f_dir * t_side.dot(f_dir); t_side /= np.linalg.norm(t_side)
    # palm normal: thumb side = f x p for a right hand, p x f for a left hand
    p_dir = np.cross(t_side, f_dir) if side == 'Right' else np.cross(f_dir, t_side)
    p_dir /= np.linalg.norm(p_dir)
    others = sorted(fingers[1:], key=lambda f: -((co[f['tip']] - wrist) @ t_side))
    names = ['Thumb'] + ['Index', 'Middle', 'Ring', 'Pinky'][:len(others)]
    out = {}
    for name, f in zip(names, [thumb] + others):
        r = f['region']; dd = D[r]
        inside = r[dd >= f['web']]
        span = D[f['tip']] - f['web']
        cents = []
        for k in range(6):
            a = f['web'] + span * k / 6; b = f['web'] + span * (k + 1) / 6
            sel = inside[(D[inside] >= a) & (D[inside] <= b)]
            if len(sel):
                cents.append(co[sel].mean(0))
        cents.append(co[f['tip']] * 0.6 + cents[-1] * 0.4)
        cents = np.array(cents)
        first = cents[1] - cents[0]; first /= np.linalg.norm(first)
        back = 0.35 if name == 'Thumb' else 0.25
        mcp = cents[0] - first * span * back
        poly = np.vstack([mcp, cents])
        seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); arc = np.concatenate([[0], np.cumsum(seg)])
        total = arc[-1]

        def at(u):
            s = u * total; k = min(np.searchsorted(arc, s) - 1, len(seg) - 1); k = max(k, 0)
            w = (s - arc[k]) / max(seg[k], 1e-9)
            return poly[k] * (1 - w) + poly[k + 1] * w
        joints = [at(u) for u in (0.0, 0.42, 0.70, 1.0)]
        for k in (2, 3):                            # no joint bends more than 35 degrees at rest (tip/claw kinks)
            a = joints[k - 1] - joints[k - 2]; b = joints[k] - joints[k - 1]
            a_n = a / np.linalg.norm(a); L = np.linalg.norm(b); b_n = b / L
            ang = math.acos(np.clip(a_n @ b_n, -1, 1))
            if ang > math.radians(35):
                perp = b_n - a_n * (a_n @ b_n); perp /= max(np.linalg.norm(perp), 1e-9)
                c = math.radians(35)
                joints[k] = joints[k - 1] + (a_n * math.cos(c) + perp * math.sin(c)) * L
        out[name] = {'joints': joints, 'region': f['region'], 'web': f['web'], 'D': D, 'span': span, 'tip': f['tip'],
                     'mcp_D': f['web'] - span * back}
    return {'fingers': out, 'p': p_dir, 'f': f_dir, 't': t_side, 'D': D, 'H': H, 'names': names}


fits = {side: analyse(side) for side in ('Right', 'Left')}
for side, fit in fits.items():
    print('FIT', side, fit['names'], {n: round(v['span'], 3) for n, v in fit['fingers'].items()})

if mode == 'analyze':
    bm = bmesh.new()
    for side, fit in fits.items():
        for name, v in fit['fingers'].items():
            j = v['joints']
            for a, b in zip(j[:-1], j[1:]):
                a = Vector(a); b = Vector(b); d = b - a
                m = Matrix.Translation((a + b) / 2) @ d.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
                bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.004, radius2=0.002, depth=d.length, matrix=m)
    rods = bpy.data.meshes.new('rods'); bm.to_mesh(rods); o = bpy.data.objects.new('rods', rods)
    bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.new('r'); mat.diffuse_color = (1, 0.1, 0.1, 1); rods.materials.append(mat)
    # hand-only copy of the mesh so the thigh/skirt do not hide the fingers
    keep = fits['Right']['H'] | fits['Left']['H']
    hm = mesh.data.copy(); hb = bmesh.new(); hb.from_mesh(hm)
    hb.verts.ensure_lookup_table()
    bmesh.ops.delete(hb, geom=[v for v in hb.verts if not keep[v.index]], context='VERTS')
    hb.to_mesh(hm); ho = bpy.data.objects.new('HandOnly', hm); ho.matrix_world = mesh.matrix_world
    bpy.context.scene.collection.objects.link(ho)
    mesh.hide_render = True
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.6
    for ob in bpy.data.objects:
        if ob.type == 'MESH': ob.hide_render = ob.name not in ('HandOnly', 'rods')
    scene.render.resolution_x = scene.render.resolution_y = 520
    out_dir = sys.argv[sys.argv.index('--') + 2]
    for side, fit in fits.items():
        c = Vector(np.mean([v['joints'][1] for v in fit['fingers'].values()], axis=0))
        for name, d in (('palm', fit['p']), ('back', -fit['p'])):
            cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.26
            cam = bpy.data.objects.new('c', cd); scene.collection.objects.link(cam)
            dv = Vector(d)
            cam.matrix_world = Matrix.Translation(c + dv * 1.0) @ (-dv).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
            scene.camera = cam; scene.render.filepath = f'{out_dir}/fit_{side}_{name}.png'
            bpy.ops.render.render(write_still=True)
    sys.exit(0)

# ---------------------------------------------------------------- apply
inv = rig.matrix_world.inverted()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for side, fit in fits.items():
    p = Vector(fit['p']); t = Vector(fit['t'])
    hand = eb[f'mixamorig:{side}Hand']
    used = set(fit['fingers'])
    for name in FINGERS:
        bones = [eb[f'mixamorig:{side}Hand{name}{k}'] for k in (1, 2, 3)]
        if name in used:
            j = [inv @ Vector(x) for x in fit['fingers'][name]['joints']]
            toward = (p * 0.55 - t * 0.85).normalized() if name == 'Thumb' else p
        else:
            # parked: a tiny chain inside the palm, no weights
            base = hand.head + (hand.tail - hand.head) * 0.6
            j = [base + (hand.tail - hand.head).normalized() * 0.004 * k for k in range(4)]
            toward = p
        for k, b in enumerate(bones):
            b.use_connect = False
            b.head = j[k]; b.tail = j[k + 1]
            d = (b.tail - b.head).normalized()
            b.align_roll(inv.to_3x3() @ (toward - d * toward.dot(d)).normalized())
            b.parent = hand if k == 0 else bones[k - 1]
        for k in (1, 2):
            bones[k].use_connect = True
bpy.ops.object.mode_set(mode='OBJECT')

groups = {g.name: g for g in mesh.vertex_groups}


def group(name):
    return groups.get(name) or mesh.vertex_groups.new(name=name)


for side, fit in fits.items():
    finger_groups = [group(f'mixamorig:{side}Hand{n}{k}') for n in FINGERS for k in (1, 2, 3)]
    fg_index = {g.index for g in finger_groups}
    hand_g = group(f'mixamorig:{side}Hand')
    D = fit['D']; H = fit['H']
    idx = [int(i) for i in np.nonzero(H)[0]]
    # strip old finger weights from every hand vertex, folding them into the hand bone
    for i in idx:
        v = me.vertices[i]
        moved = sum(g.weight for g in v.groups if g.group in fg_index)
        if moved > 0:
            for g in finger_groups:
                g.remove([i])
            hw = next((g.weight for g in v.groups if g.group == hand_g.index), 0.0)
            hand_g.add([i], hw + moved, 'REPLACE')
    for name, fd in fit['fingers'].items():
        joints = [np.array(x) for x in fd['joints']]
        segs = [(joints[k], joints[k + 1]) for k in range(3)]
        lengths = [np.linalg.norm(b - a) for a, b in segs]
        total = sum(lengths)
        bounds = np.concatenate([[0], np.cumsum(lengths)]) / total
        bones = [group(f'mixamorig:{side}Hand{name}{k}') for k in (1, 2, 3)]
        for i in (int(x) for x in fd['region']):
            if D[i] < fd['mcp_D']:
                continue
            # position along the chain: project onto the nearest segment
            best = None
            for k, (a, b) in enumerate(segs):
                ab = b - a; s = np.clip((co[i] - a) @ ab / (ab @ ab), 0, 1)
                d = np.linalg.norm(co[i] - (a + ab * s))
                if best is None or d < best[0]:
                    best = (d, bounds[k] + s * (bounds[k + 1] - bounds[k]))
            u = best[1]
            w = np.zeros(4)                        # hand, bone1, bone2, bone3
            fade = 0.07
            w[0] = np.clip((bounds[0] + 0.12 - u) / 0.12, 0, 1) if name != 'Thumb' else np.clip((0.10 - u) / 0.10, 0, 1)
            for k in range(3):
                lo_, hi_ = bounds[k], bounds[k + 1]
                w[k + 1] = np.clip(min(u - lo_ + fade, hi_ - u + fade) / (2 * fade), 0, 1) if k else \
                    np.clip((hi_ - u + fade) / (2 * fade), 0, 1)
            if u >= bounds[3] - fade:
                w[3] = 1.0
            w[1] *= 1 - w[0]
            w = w / w.sum()
            v = me.vertices[i]
            keep = {g.group: g.weight for g in v.groups if g.group not in fg_index}
            scale = w[0]
            for gi, gw in keep.items():
                mesh.vertex_groups[gi].add([i], gw * scale, 'REPLACE')
            for k in range(3):
                if w[k + 1] > 1e-4:
                    bones[k].add([int(i)], float(w[k + 1]), 'REPLACE')
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.001)
json.dump({side: {n: {'joints': [list(map(float, j)) for j in v['joints']], 'tip': list(map(float, co[v['tip']]))}
                  for n, v in fit['fingers'].items()}
           for side, fit in fits.items()}, open(os.path.join(common.WORK, 'hand_fit.json'), 'w'), indent=1)
bpy.ops.wm.save_mainfile()
print('APPLIED hand refit')
