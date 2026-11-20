"""Runtime export (goblin): work/rig_v6.blend (gated rig, timed clips, Meshy UVs, head split) -> export/mm6_gob2_lod0.glb.
One skinned mesh 'Goblin': material Goblin_A (body set 1K, UVMap) and GoblinHead_A (head set 1K; head faces get their
HeadUV as TEXCOORD_0). The scimitar (native gobsta/gobat frames and the Corsair icon 7item220: curved pale steel blade
widening toward a clipped point with two back notches, gold crossguard, knuckle bow and scroll quillon, leather grip,
red jewels; geometry ported from mm6_gob_claude/scripts/replace_sword.py at 1.35x so its grip is the solved 1.8 cm
handle) is built on a 'Sword' bone (child of B_R_Hand, at the solved handle, along the source grip axis;
work/grip_pose.json), UVs into body atlas swatches; split into an attachment later by tools/split_attachment.py.
Clips Standing, Walking, Running, Attack, Cast, Hit, Death, Fidget and Dead (last Death frame held 1 s); keys at
30 fps, quaternions sign-continuous. Env BLADE_ROLL_DEG (default 45): edge roll about the blade from the knuckle line.
Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'gob2_head_basecolor_1k.png'))

# ---------------------------------------------------------------- head UVs into the single UV layer
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
if HEAD:
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])

# ---------------------------------------------------------------- sword bone and mesh
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
SW = json.load(open(os.path.join(T, 'gob2_sword_swatches.json')))
Hm = rig.data.bones['B_R_Hand'].matrix_local
c = Hm @ Vector(G['handle_centre_hand_local']); ax = (Hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Sword'); eb.head = c; eb.tail = c + ax * 0.15; eb.parent = rig.data.edit_bones['B_R_Hand']
_kn = rig.data.bones['B_R_Finger2'].head_local; eb.align_roll((_kn - c) - ax * (_kn - c).dot(ax))
# left-palm socket for the Shaman/King cast (glow and spell launch): on the palm surface, 3 cm off the palm centre
# along the palm normal (the goblin's rest palms face forward, -Y)
wl = rig.data.bones['B_L_Hand'].head_local; k2 = rig.data.bones['B_L_Finger2'].head_local
across = rig.data.bones['B_L_Finger1'].head_local - rig.data.bones['B_L_Finger4'].head_local
pn = (k2 - wl).cross(across).normalized()
if pn.y > 0:
    pn = -pn
sp = wl + (k2 - wl) * 0.45 + pn * 0.03
sk = rig.data.edit_bones.new('Socket_Palm_Left'); sk.head = sp; sk.tail = sp + pn * 0.05
sk.parent = rig.data.edit_bones['B_L_Hand']; sk.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
# blade plane: perpendicular to the palm (edge forward/back) - flat side faces sideways like the sprite
# blade orientation from the fist: the cutting edge points from the handle toward the middle-finger knuckle (edge
# aligned with the knuckles, as in a real grip); 'side' = edge direction, 'flat' = the blade's flat normal.
# (First version used an arbitrary hand-bone axis: the flat faced forward while walking - user review 2026-10-10.)
kn = rig.data.bones['B_R_Finger2'].head_local
side = (kn - c); side = (side - ax * side.dot(ax)).normalized()
# + BLADE_ROLL about the blade axis: the roll at which the clips cut with the edge (blade_edge_gate.py ROLL_SWEEP:
# attack 0.78, walk 0.99, fidget 0.85 edge-leading share at 45 deg; the knuckle line itself 0.67 / 0.68 / 0.55)
# goblin scimitar, sweep over 0..315 with blade_edge_gate.py (signed lead at the blow) and g6_sword_mesh.py:
# attack R6 (review 1): 45 deg - no contact in any clip, the cutting edge leads at the blow (+0.56) and in the walk
# (0.91); the earlier R4 attack needed 225 (45 put the curved blade 19 cm into the torso at R4's cross-body coil)
BLADE_ROLL = math.radians(float(os.environ.get('BLADE_ROLL_DEG', '45')))
side = (side * math.cos(BLADE_ROLL) + ax.cross(side) * math.sin(BLADE_ROLL)).normalized(); flat = ax.cross(side)
assert side.length > 0.99 and flat.length > 0.99
verts, faces, cls = [], [], []


def P(a, s_, f_):
    return tuple(c + ax * a + side * s_ + flat * f_)


def add(ps):
    verts.extend(ps); return len(verts) - len(ps)


def ring_tube(path, radii, k, n=8):
    idx = []
    for (a, s0), r in zip(path, radii):
        idx.append(add([P(a, s0 + r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]))
    for i0, i1 in zip(idx[:-1], idx[1:]):
        for i in range(n):
            faces.append((i0 + i, i1 + i, i1 + (i + 1) % n, i0 + (i + 1) % n)); cls.append(k)
    faces.append(tuple(idx[0] + i for i in range(n))[::-1]); cls.append(k)
    faces.append(tuple(idx[-1] + i for i in range(n))); cls.append(k)


K = 1.35                                                       # replace_sword.py sizes (1.578 m pfem scale) -> ours


def Q(a, e, f):                                                # replace_sword.py frame: a along the blade, e edge, f flat
    return P(a * K, e * K, f * K)


def quad(i0, i1, i2, i3, k):
    faces.append((i0, i1, i2, i3)); cls.append(k)


def tri(i0, i1, i2, k):
    faces.append((i0, i1, i2)); cls.append(k)


def smooth01(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


L, ROOT = 0.60, 0.072
NOTCHES = ((0.575, 0.018), (0.645, 0.018))


def profile(t):
    edge = 0.024 + 0.050 * smooth01(t, 0.20, 0.82)
    spine = 0.016
    for c0, r in NOTCHES:
        if abs(t - c0) < r:
            spine = 0.016 - 0.014 * math.sqrt(max(0.0, 1 - ((t - c0) / r) ** 2))
    if t > 0.84:                                               # clipped point: the edge sweeps up onto the back line
        u = (t - 0.84) / 0.16
        edge *= max(0.0, 1 - u ** 1.35); spine *= max(0.0, 1 - u ** 3)
    return -0.17 * t ** 1.6, edge, spine, 0.0042 - 0.0026 * t


rings = []
for t in [0.0, 0.08, 0.18, 0.28, 0.38, 0.47, 0.54, 0.555, 0.575, 0.595, 0.61, 0.625, 0.645, 0.665, 0.68, 0.73, 0.79,
          0.85, 0.90, 0.95]:
    c0, we, ws, th = profile(t)
    a = ROOT + L * t
    rings.append(add([Q(a, c0 + we, 0), Q(a, c0 + we * 0.40, th), Q(a, c0 - ws, th * 0.75), Q(a, c0 - ws, -th * 0.75),
                      Q(a, c0 + we * 0.40, -th)]))
tip_c = profile(1.0)[0]
tip_i = add([Q(ROOT + L, tip_c - 0.004, 0)])
EDGE_K = {0: 'edge', 1: 'blade', 2: 'blade', 3: 'blade', 4: 'edge'}
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(5):
        quad(r0 + k, r1 + k, r1 + (k + 1) % 5, r0 + (k + 1) % 5, EDGE_K[k])
for k in range(5):
    tri(rings[-1] + k, tip_i, rings[-1] + (k + 1) % 5, EDGE_K[k])
faces.append(tuple(rings[0] + k for k in range(5))[::-1]); cls.append('blade')
AX, SD, FL = Vector(ax), Vector(side), Vector(flat)


def tube(points, radius, k, sides=6):
    idx = []
    for i, p_ in enumerate(points):
        d = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        u = FL - d * FL.dot(d); u.normalize(); v = d.cross(u)
        idx.append(add([tuple(p_ + (u * math.cos(2 * math.pi * s_ / sides + math.pi / 4) +
                                    v * math.sin(2 * math.pi * s_ / sides + math.pi / 4)) * radius * K) for s_ in range(sides)]))
    for a0, a1 in zip(idx[:-1], idx[1:]):
        for s_ in range(sides):
            quad(a0 + s_, a1 + s_, a1 + (s_ + 1) % sides, a0 + (s_ + 1) % sides, k)
    faces.append(tuple(idx[0] + s_ for s_ in range(sides))[::-1]); cls.append(k)
    faces.append(tuple(idx[-1] + s_ for s_ in range(sides))); cls.append(k)


def gem(centre, r, k):
    base = [AX, -AX, SD, -SD, FL, -FL]
    for a_ in (0, 1):
        for e_ in (2, 3):
            for f_ in (4, 5):
                t3 = (a_, e_, f_) if (a_ + e_ + f_) % 2 else (a_, f_, e_)
                p3 = [base[i] for i in t3]
                m3 = [(p3[0] + p3[1]).normalized(), (p3[1] + p3[2]).normalized(), (p3[2] + p3[0]).normalized()]
                for q3 in ((p3[0], m3[0], m3[2]), (m3[0], p3[1], m3[1]), (m3[2], m3[1], p3[2]), (m3[0], m3[1], m3[2])):
                    i = add([tuple(centre + v * r * K) for v in q3]); tri(i, i + 1, i + 2, k)


V = lambda a, e, f: Vector(Q(a, e, f))
tube([V(a, 0, 0) for a in (-0.058, -0.02, 0.02, 0.058)], 0.0135, 'grip', sides=8)
tube([V(0.065, e, 0) for e in (-0.040, -0.020, 0.0, 0.020, 0.036)], 0.0075, 'gold')
tube([V(0.065 - 0.130 * (k / 12), 0.036 + 0.026 * math.sin(math.pi * k / 12) - 0.022 * (k / 12), 0) for k in range(13)],
     0.0065, 'gold')
tube([V(0.065, -0.040, 0), V(0.074, -0.050, 0), V(0.087, -0.054, 0), V(0.098, -0.047, 0), V(0.100, -0.036, 0),
      V(0.093, -0.031, 0)], 0.0058, 'gold')
gem(V(0.066, 0.004, 0.0), 0.0115, 'gem')
tube([V(-0.058, 0.0, 0), V(-0.064, 0.004, 0), V(-0.070, 0.008, 0)], 0.0155, 'gold', sides=8)
gem(V(-0.078, 0.010, 0), 0.0105, 'gem')
sm = bpy.data.meshes.new('SwordMesh'); sm.from_pydata(verts, [], faces); sm.update()
so = bpy.data.objects.new('SwordTmp', sm); scene.collection.objects.link(so)
uvl = sm.uv_layers.new(name='UVMap').data
for p, k in zip(sm.polygons, cls):
    u, v, r = SW[k]
    for j, li in enumerate(p.loop_indices):
        ang = 2 * math.pi * j / len(p.loop_indices); uvl[li].uv = (u + r * math.cos(ang), v + r * math.sin(ang))
    p.use_smooth = k in ('grip', 'gold')
so.vertex_groups.new(name='Sword').add(list(range(len(verts))), 1.0, 'REPLACE')
print('SWORD tris', sum(len(f) - 2 for f in faces), 'min face area mm2', round(min(p.area for p in sm.polygons) * 1e6, 3))

# ---------------------------------------------------------------- materials


def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


mats = [material('Goblin_A', 'gob2_basecolor_1k.png', 'gob2_normal_1k.png', 'gob2_metal_rough_1k.png')]
if HEAD:
    mats.append(material('GoblinHead_A', 'gob2_head_basecolor_1k.png', 'gob2_head_normal_1k.png', 'gob2_head_metal_rough_1k.png'))
me.materials.clear(); sm.materials.clear()
for m in mats:
    me.materials.append(m); sm.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
for p in sm.polygons:
    p.material_index = 0
for o in bpy.data.objects:
    o.select_set(o in (body, so))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'Goblin'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'finger', 'head', 'orig_co')]:
    body.data.attributes.remove(body.data.attributes[at])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm6_gob2_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
