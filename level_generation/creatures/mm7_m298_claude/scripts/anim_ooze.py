"""Ooze clips (24 fps): work/rig_uv.blend -> work/anim_v1.blend, plus work/clip_report.json (floor and stretch gates).

No limbs: each clip is a function of time giving, per bone, a world-space offset, rotation and scale about the
bone's rest head (mm6_ooz_claude route). Lump heads lie on the floor, so their scales and horizontal offsets never
lift or sink the underside. The pod is hidden (PodRoot scale 0.02 inside the blob) except in Attack and Cast; the
globules are hidden (scale 0.001 in the blob's middle) except in Death, Dead and Fidget.
Native timing (mm7_m298 manifest, 125 ms per frame):
  Standing  24 f  1.0 s  slow pulse (native: one still frame)
  Walking   18 f  0.75 s native wa..wf: the middle heaves up into a hump and settles while the outline draws in a
                  little; a peristaltic wave runs front -> back and the lumps push forward
  Running   12 f  0.5 s  the same, larger and faster
  Attack    30 f  1.25 s native a b c d e f e d c b: a knobbed pseudopod rises from the middle (b, c), curls back
                  into a hook (d), stands tallest (e, 3.7x the blob height), lashes forward and down at the party (f,
                  impact 0.68 s), then retracts through the same poses
  Cast      30 f  1.25 s Toxic Cloud (B/C): the pod rises straight, the knob swells, then spits (sharp contraction
                  and forward nod at 0.68 s; Socket_Spit on the knob's tip) and the pod sinks back
  Hit       21 f  0.875 s native na..ng: the outline draws in and the middle heaves into a cone, then relaxes
  Death     15 f  0.625 s native da..de: contracts, gathers into a column and hops, bursts into globules that rain
                  down and splash onto the floor around a small remnant puddle
  Dead       1 f  the corpse (native xa: scattered globules) held
  Fidget    15 f  0.625 s native fa..fe: two bubbles swell out of the top and pop one after the other
Pose: world matrices set with no action attached, keyed afterwards. Args: none"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_uv.blend'))
arm, mesh = bpy.data.objects['Ooze_Rig'], bpy.data.objects['Ooze']
scene = bpy.context.scene
scene.render.fps = 24
FPS = 24
DIMS = json.loads(scene['ooze_dims'])
AW = arm.matrix_world
LUMPS = [f'Lump_{i}' for i in range(8)]
PODS = [f'Pod{i + 1}' for i in range(5)] + ['Knob']
GLOBS = [g[0] for g in DIMS['globs']]
GLOB_C = {g[0]: Vector(g[1]) for g in DIMS['globs']}
GLOB_R = {g[0]: g[2] for g in DIMS['globs']}
ORDER = ['Root', 'Body', 'Lump_C'] + LUMPS + ['PodRoot'] + PODS + ['Socket_Spit'] + GLOBS
REST = {n: AW @ arm.data.bones[n].matrix_local for n in ORDER}
HEAD = {n: REST[n].translation.copy() for n in ORDER}
F = Vector((0, -1, 0))                                  # forward
CENTRE = Vector((0, 0, 0.08))                           # hidden parts sit here, inside the blob
ss = lambda x: x * x * (3 - 2 * x)

# rest-pose blob surface (for placing the fidget bubbles on top of it)
part = np.zeros(len(mesh.data.polygons), int)
mesh.data.attributes['part'].data.foreach_get('value', part)
verts = [v.co.copy() for v in mesh.data.vertices]
blob_faces = [tuple(p.vertices) for p in mesh.data.polygons if part[p.index] == 0]
tree = BVHTree.FromPolygons(verts, blob_faces)


def surface_z(x, y):
    hit = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 5.0)
    return hit[0].z if hit[0] is not None else 0.0


def lump_xy(n):
    h = HEAD[n]
    return Vector((h.x, h.y, 0))


def keyed(t, keys):
    """Smoothstep between (time, value) keys; values are floats or tuples."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ss((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(a, tuple):
                return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return keys[-1][1]


def base_pose():
    p = {n: {'off': Vector(), 'scale': Vector((1, 1, 1)), 'rot': Quaternion()} for n in ORDER}
    p['PodRoot']['scale'] = Vector((0.02, 0.02, 0.02))
    for g in GLOBS:
        hide_glob(p, g)
    return p


def hide_glob(p, g):
    p[g]['off'] = CENTRE - GLOB_C[g]
    p[g]['scale'] = Vector((0.001, 0.001, 0.001))


def body_squash(p, sx, sy, sz, dx=0.0, dy=0.0):
    """Whole-body squash about the floor centre: lump heads move with the xy scale, their own scales follow."""
    # Body itself keeps unit scale: a non-uniformly scaled parent would shear the rotated pod chain, which glTF
    # TRS channels cannot carry
    for n in ['Lump_C'] + LUMPS:
        xy = lump_xy(n)
        p[n]['off'] += Vector((xy.x * (sx - 1) + dx, xy.y * (sy - 1) + dy, 0))
        p[n]['scale'] = Vector((p[n]['scale'].x * sx, p[n]['scale'].y * sy, p[n]['scale'].z * sz))


def standing(t, amp=1.0):
    p = base_pose()
    w = 2 * math.pi * t
    for i, n in enumerate(LUMPS):
        p[n]['scale'].z *= 1 + 0.06 * amp * math.sin(w + i * math.pi / 4)
    p['Lump_C']['scale'].z *= 1 + 0.05 * amp * math.sin(w + 1.0)
    body_squash(p, 1 - 0.012 * amp * math.sin(w), 1 - 0.012 * amp * math.sin(w), 1 + 0.035 * amp * math.sin(w))
    return p


def crawl(t, amp):
    """Native walk: the middle heaves up (wc, +50 % height) and settles; the outline draws in a little at the heave;
    a peristaltic wave runs front -> back and the lumps push forward in turn."""
    p = base_pose()
    w = 2 * math.pi * t
    heave = 0.5 - 0.5 * math.cos(w)                      # 0 at the loop seam, 1 at mid cycle (native wc/wd)
    for n in LUMPS:
        y = lump_xy(n).y / max(DIMS['ry'], 1e-3)          # -1 front .. +1 back
        ph = w + 2.2 * y
        p[n]['scale'].z *= 1 + 0.16 * amp * math.sin(ph)
        p[n]['scale'].x *= 1 - 0.05 * amp * math.sin(ph)
        p[n]['off'] += F * (0.03 * amp * math.cos(ph))
    p['Lump_C']['scale'] *= Vector((1 - 0.1 * heave * amp, 1 - 0.1 * heave * amp, 1 + 0.36 * heave * amp))
    p['Lump_C']['off'] += F * (0.02 * amp * math.sin(w))
    body_squash(p, 1 - 0.05 * heave * amp, 1 - 0.03 * heave * amp + 0.03 * amp * math.sin(2 * w),
                1 + 0.04 * heave * amp)
    return p


def pod_pose(p, grow, lean, bends, knob_scale=1.0, knob_rot=0.0, yaw=0.0):
    """grow: PodRoot uniform scale; lean: PodRoot pitch (deg, + forward toward the party); bends: per stalk segment
    pitch (deg); knob_rot: the knob's own pitch."""
    p['PodRoot']['scale'] = Vector((grow, grow, grow))
    p['PodRoot']['rot'] = Quaternion(Vector((0, 0, 1)), math.radians(yaw)) @ \
        Quaternion(Vector((1, 0, 0)), math.radians(lean))
    for n, ang in zip(PODS[:5], bends):
        p[n]['rot'] = Quaternion(Vector((1, 0, 0)), math.radians(ang))
    p['Knob']['rot'] = Quaternion(Vector((1, 0, 0)), math.radians(knob_rot))
    p['Knob']['scale'] = Vector((knob_scale,) * 3)
    p['Lump_C']['scale'] *= 1 + 0.3 * min(grow, 1.0)    # the base swells where the pod emerges


# native attack keys (front view m298a?0 and side view m298a?2, 125 ms each): time, grow, lean, stalk bends, knob
ATTACK_KEYS = [
    (0.000, 0.02, 0.0, (0, 0, 0, 0, 0), 0.0),            # a: a low bump
    (0.125, 0.72, -4.0, (2, -3, 3, -2, 0), 0.0),          # b: stalk with knob rises
    (0.250, 0.92, -14.0, (-6, -6, 4, 10, 10), 6.0),       # c: taller, leaning back
    (0.375, 1.00, -24.0, (-8, 6, 18, 22, 18), 14.0),      # d: curled back into a hook, knob over the base
    (0.500, 1.00, -12.0, (2, -4, 6, 4, 2), 0.0),          # e: tallest, upright
    (0.625, 1.00, 20.0, (5, 6, 6, 4, 2), 8.0),            # f: lashes forward and down at the party
    (0.700, 1.00, 27.0, (6, 8, 8, 6, 4), 12.0),           #    impact 0.68 s (knob still about 0.55 m high)
    (0.800, 1.00, -10.0, (2, -4, 6, 4, 2), 0.0),          # e
    (0.900, 1.00, -22.0, (-8, 6, 18, 22, 18), 14.0),      # d
    (1.000, 0.92, -14.0, (-6, -6, 4, 10, 10), 6.0),       # c
    (1.125, 0.72, -4.0, (2, -3, 3, -2, 0), 0.0),          # b
    (1.250, 0.02, 0.0, (0, 0, 0, 0, 0), 0.0),             # a
]


def attack(t):
    T = t * 1.25
    p = standing(T / 1.25, 0.3)
    grow = keyed(T, [(k[0], k[1]) for k in ATTACK_KEYS])
    lean = keyed(T, [(k[0], k[2]) for k in ATTACK_KEYS])
    bends = keyed(T, [(k[0], tuple(float(x) for x in k[3])) for k in ATTACK_KEYS])
    knob = keyed(T, [(k[0], k[4]) for k in ATTACK_KEYS])
    pod_pose(p, grow, lean, bends, knob_rot=knob)
    sq = keyed(T, [(0.0, 1.0), (0.12, 1.05), (0.375, 0.94), (0.68, 0.9), (0.9, 0.96), (1.25, 1.0)])
    body_squash(p, 1 + (1 - sq) * 0.45, 1 + (1 - sq) * 0.45, sq)
    return p


def cast(t):
    """Toxic Cloud: the pod rises straight, the knob swells, spits at 0.68 s (contracts, nods forward), sinks."""
    T = t * 1.25
    p = standing(T / 1.25, 0.3)
    grow = keyed(T, [(0.0, 0.02), (0.2, 0.8), (0.4, 1.0), (0.9, 1.0), (1.1, 0.6), (1.25, 0.02)])
    lean = keyed(T, [(0.0, 0.0), (0.4, -8.0), (0.6, -12.0), (0.7, 14.0), (0.85, 4.0), (1.25, 0.0)])
    knob = keyed(T, [(0.0, 1.0), (0.4, 1.0), (0.62, 1.45), (0.70, 0.8), (0.8, 1.05), (1.25, 1.0)])
    nod = keyed(T, [(0.0, 0.0), (0.6, -10.0), (0.7, 30.0), (0.85, 8.0), (1.25, 0.0)])
    pod_pose(p, grow, lean, (0, 0, 0, 2, 4), knob_scale=knob, knob_rot=nod)
    sq = keyed(T, [(0.0, 1.0), (0.4, 0.95), (0.66, 0.9), (0.72, 1.04), (0.9, 0.97), (1.25, 1.0)])
    body_squash(p, 1 + (1 - sq) * 0.45, 1 + (1 - sq) * 0.45, sq)
    return p


def hit(t):
    """Native na..ng: the outline draws in (178 -> 135 px) while the middle heaves into a cone (41 -> 59 px), then
    relaxes with a little jiggle."""
    p = base_pose()
    T = t * 0.875
    c = keyed(T, [(0.0, 0.0), (0.2, 1.0), (0.375, 0.9), (0.625, 0.3), (0.875, 0.0)])
    p['Lump_C']['scale'] *= Vector((1 - 0.15 * c, 1 - 0.15 * c, 1 + 0.42 * c))
    for i, n in enumerate(LUMPS):
        p[n]['scale'].z *= 1 + 0.12 * c * (1 if i % 2 else 0.6)
    j = math.exp(-5 * T) * math.sin(2 * math.pi * 4 * T)
    body_squash(p, 1 - 0.2 * c + 0.03 * j, 1 - 0.2 * c - 0.03 * j, 1 + 0.05 * c)
    return p


# death: per glob a launch delay, an arc height and a spin, all reproducible
RNG = np.random.default_rng(2981)
GLOB_FLIGHT = {g: (0.25 + 0.05 * RNG.random(), 0.18 + 0.32 * RNG.random(), RNG.random() * 2 * math.pi,
                  Vector((0.12 * (RNG.random() - 0.5), 0.12 * (RNG.random() - 0.5), 0.1 + 0.25 * RNG.random())))
               for g in GLOBS}


def death(t):
    p = base_pose()
    T = t * 0.625
    # body: contract (da), gather into a column and hop (db), burst into a small remnant puddle (dc..de)
    sxy = keyed(T, [(0.0, 1.0), (0.11, 0.68), (0.22, 0.44), (0.27, 0.42), (0.34, 0.42), (0.5, 0.44), (0.625, 0.42)])
    sz = keyed(T, [(0.0, 1.0), (0.11, 1.1), (0.22, 1.6), (0.27, 1.55), (0.34, 0.4), (0.5, 0.3), (0.625, 0.3)])
    hop = keyed(T, [(0.0, 0.0), (0.16, 0.0), (0.24, 0.07), (0.3, 0.05), (0.38, 0.0), (0.625, 0.0)])
    body_squash(p, sxy, sxy, sz)
    for n in ['Lump_C'] + LUMPS:
        p[n]['off'].z += hop
    # globules fly out of the burst on ballistic arcs and land at their corpse places (their bind-pose spots)
    for g in GLOBS:
        t0, h, spin, start = GLOB_FLIGHT[g]           # each leaves from inside the bursting column
        t1 = t0 + 0.22
        r = GLOB_R[g]
        if T < t0:
            hide_glob(p, g)
            continue
        u = min((T - t0) / (t1 - t0), 1.0)
        end = GLOB_C[g]
        pos = start.lerp(end, u)
        pos.z = start.z + (end.z - start.z) * u + 4 * h * u * (1 - u)
        grow = ss(min(u / 0.2, 1.0))
        land = keyed(T, [(t1, 0.0), (t1 + 0.03, 1.0), (t1 + 0.08, 0.0)]) if T >= t1 else 0.0
        if u < 1.0:                                       # round in the air (the bind shape is a flattened drop)
            sc = Vector((grow, grow, grow / 0.62 * 0.9))
        else:
            sc = Vector((1 + 0.18 * land, 1 + 0.18 * land, 1 - 0.3 * land))
        p[g]['off'] = pos - end
        p[g]['scale'] = sc
        p[g]['rot'] = Quaternion(Vector((0, 0, 1)), spin * (1 - u))
    return p


def fidget(t):
    """Two bubbles (Glob_00, Glob_01) swell out of the top and pop, the second a little later."""
    T = t * 0.625
    p = standing(T / 0.625, 0.6)
    for g, (x, y), (t0, t1) in (('Glob_00', (-0.16, -0.04), (0.06, 0.30)), ('Glob_01', (0.17, 0.05), (0.14, 0.44))):
        if T < t0 or T > t1:
            continue
        u = (T - t0) / (t1 - t0)
        b = ss(min(u / 0.85, 1.0)) * 1.25 if u < 0.92 else 0.0      # swells, then pops within one frame
        z = surface_z(x, y) + 0.005
        k = 0.085 / GLOB_R[g] * b                                     # bubble radius about 10.5 cm at full size
        p[g]['off'] = Vector((x, y, z)) - GLOB_C[g]
        p[g]['scale'] = Vector((k, k, k / 0.62))
    return p


CLIPS = {'Standing': (24, lambda t: standing(t)), 'Walking': (18, lambda t: crawl(t, 1.0)),
         'Running': (12, lambda t: crawl(t, 1.35)), 'Attack': (30, attack), 'Cast': (30, cast),
         'Hit': (21, hit), 'Death': (15, death), 'Dead': (1, lambda t: death(1.0)), 'Fidget': (15, fidget)}
CHAIN = set(PODS) | {'Socket_Spit'}


def apply(p):
    for n in ORDER:
        d = p[n]
        R = REST[n]
        head = HEAD[n]
        rot = d['rot'].to_matrix().to_4x4()
        S = Matrix.Diagonal((d['scale'].x, d['scale'].y, d['scale'].z, 1.0))
        if n in CHAIN:
            # chain segments: rotate (and scale) about their own head, carried by the parent's current pose
            parent = arm.pose.bones[n].parent
            P = AW @ parent.matrix
            Pr = AW @ arm.data.bones[parent.name].matrix_local
            M = P @ Pr.inverted() @ R
            M = Matrix.Translation(M.translation) @ rot @ S @ Matrix.Translation(-M.translation) @ M
        else:
            M = Matrix.Translation(head + d['off']) @ rot @ S @ Matrix.Translation(-head) @ R
        arm.pose.bones[n].matrix = AW.inverted() @ M
        bpy.context.view_layer.update()


# gates: floor (lowest vertex) and edge stretch (blob edges, pod edges while the pod is out)
me = mesh.data
edges = np.array([tuple(e.vertices) for e in me.edges])
vpart = np.zeros(len(me.vertices), int)
for poly in me.polygons:
    for v in poly.vertices:
        vpart[v] = part[poly.index]
rest_co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
rest_len = np.linalg.norm(rest_co[edges[:, 0]] - rest_co[edges[:, 1]], axis=1)
blob_e = (vpart[edges[:, 0]] == 0) & (rest_len > 1e-5)
pod_e = (vpart[edges[:, 0]] == 1) & (rest_len > 1e-5)

arm.animation_data_create()
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
report = {}
for name, (n, fn) in CLIPS.items():
    arm.animation_data.action = None
    poses, rows = [], []
    for f in range(n + 1):
        t = f / n if n > 0 else 0.0
        pose = fn(t)
        apply(pose)
        poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy())
                      for pb in arm.pose.bones})
        dg = bpy.context.evaluated_depsgraph_get()
        em = mesh.evaluated_get(dg).to_mesh()
        co = np.array([tuple(mesh.matrix_world @ v.co) for v in em.vertices])
        mesh.evaluated_get(dg).to_mesh_clear()
        ln = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1) / np.maximum(rest_len, 1e-9)
        pod_out = pose['PodRoot']['scale'].x > 0.9
        stretch_b = float(ln[blob_e].max())
        stretch_p = float(ln[pod_e].max()) if pod_out else 0.0
        vis = (vpart == 0) | ((vpart == 1) & pod_out) | (vpart == 2)
        top_blob = float(co[vpart == 0][:, 2].max())
        rows.append({'f': f, 'min_z': round(float(co[vis][:, 2].min()), 4),
                     'min_z_blob': round(float(co[vpart == 0][:, 2].min()), 4),
                     'max_z': round(float(co[vis][:, 2].max()), 3), 'blob_top': round(top_blob, 3),
                     'stretch_blob': round(stretch_b, 2), 'stretch_pod': round(stretch_p, 2)})
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for f, pose in enumerate(poses):
        for pb in arm.pose.bones:
            pb.location, pb.rotation_quaternion, pb.scale = pose[pb.name]
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('scale', frame=f)
    report[name] = {'frames': n + 1, 'seconds': n / FPS, 'min_z': min(r['min_z'] for r in rows),
                    'min_z_blob': min(r['min_z_blob'] for r in rows), 'max_z': max(r['max_z'] for r in rows),
                    'stretch_blob': max(r['stretch_blob'] for r in rows),
                    'stretch_pod': max(r['stretch_pod'] for r in rows), 'per_frame': rows}
    print('CLIP', name, json.dumps({k: v for k, v in report[name].items() if k != 'per_frame'}))
arm.animation_data.action = bpy.data.actions['Standing']
json.dump(report, open(os.path.join(common.WORK, 'clip_report.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
