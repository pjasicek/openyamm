"""Own rig for the separate-bone Smart Topology mesh: joints from the pieces' principal-axis ends, mixamorig names
(Mixamo clips retarget by name), every piece 100 % on one bone. Old head pieces are dropped (skull-only model later).
Args: -- <parts blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_map import HEAD_OLD, BONE_OF, FINGERS
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
missing = sorted(set(P) - set(BONE_OF) - set(HEAD_OLD))
assert not missing, missing


def pts(n):
    o = P[n]
    return np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])


def ends(n, ref):
    """Principal-axis end points of piece n: (end nearer ref, far end)."""
    c = pts(n); m = c.mean(0)
    ax = np.linalg.svd(c - m, full_matrices=False)[2][0]
    t = (c - m) @ ax
    a, b = m + ax * t.min(), m + ax * t.max()
    return (a, b) if np.linalg.norm(a - ref) < np.linalg.norm(b - ref) else (b, a)


def cen(*ns):
    return np.mean([pts(n).mean(0) for n in ns], axis=0)


J = {}            # bone -> (head, tail)
fem_r, fem_l = cen('P53'), cen('P61')
hips = (fem_r + fem_l) / 2; hips[1] = cen('P02')[1]
J['Hips'] = (hips, hips + [0, 0, 0.08])
l5, l3, l1 = cen('P20'), cen('P22'), cen('P21')
neck = cen('P07'); atlas = cen('P14')
J['Spine'] = (l5, l3)
J['Spine1'] = (l3, l1 + [0, 0, 0.03])
J['Spine2'] = (l1 + [0, 0, 0.03], neck)
J['Neck'] = (neck, atlas)
J['Head'] = (atlas, atlas + [0, 0, 0.16])
for side, sg, clav, hum, fore, meta in (('Right', -1, 'P24', 'P16', ('P13', 'P23'), ('P57', 'P59', 'P48')),
                                        ('Left', 1, 'P28', 'P18', ('P12', 'P25'), ('P60', 'P56', 'P47'))):
    c_med, _ = ends(clav, np.array([0, 0, 1.3]))
    sh, el = ends(hum, c_med)
    wr = np.mean([ends(f, el)[1] for f in fore], axis=0)
    el = (el + np.mean([ends(f, el)[0] for f in fore], axis=0)) / 2
    knuck = np.mean([ends(m, wr)[1] for m in meta], axis=0)
    J[side + 'Shoulder'] = (c_med, sh)
    J[side + 'Arm'] = (sh, el)
    J[side + 'ForeArm'] = (el, wr)
    J[side + 'Hand'] = (wr, knuck)
    for finger, chain in FINGERS[side].items():
        tops = [ends(chain[0], wr)[0]]
        for n in chain[1:]:
            tops.append(ends(n, tops[-1])[0])
        tip = ends(chain[2], tops[-1])[1]
        if finger == 'Middle':          # proximal shared with the ring finger: shift its knuckle onto the middle lane
            ring2_top = ends(FINGERS[side]['Ring'][1], tops[0])[0]
            tops[0] = tops[0] + (tops[1] - ring2_top)
        heads = tops + [tip]
        for i in range(3):
            J[f'{side}Hand{finger}{i + 1}'] = (heads[i], heads[i + 1])
for side, fh, femur, shin, talus, foot in (('Right', fem_r, 'P08', ('P11', 'P17'), 'P40', 'P05'),
                                           ('Left', fem_l, 'P09', ('P10', 'P19'), 'P37', 'P04')):
    _, knee = ends(femur, fh)
    knee = (knee + ends(shin[0], knee)[0]) / 2
    ankle = (ends(shin[0], knee)[1] + cen(talus)) / 2
    f = pts(foot)
    ball = np.array([ankle[0], f[:, 1].min() + 0.06, 0.025])
    toe = np.array([ankle[0], f[:, 1].min(), 0.012])
    J[side + 'UpLeg'] = (fh, knee)
    J[side + 'Leg'] = (knee, ankle)
    J[side + 'Foot'] = (ankle, ball)
    J[side + 'ToeBase'] = (ball, toe)

PARENT = {'Spine': 'Hips', 'Spine1': 'Spine', 'Spine2': 'Spine1', 'Neck': 'Spine2', 'Head': 'Neck'}
for s in ('Left', 'Right'):
    PARENT.update({s + 'Shoulder': 'Spine2', s + 'Arm': s + 'Shoulder', s + 'ForeArm': s + 'Arm',
                   s + 'Hand': s + 'ForeArm', s + 'UpLeg': 'Hips', s + 'Leg': s + 'UpLeg', s + 'Foot': s + 'Leg',
                   s + 'ToeBase': s + 'Foot'})
    for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
        PARENT[f'{s}Hand{f}1'] = s + 'Hand'
        PARENT[f'{s}Hand{f}2'] = f'{s}Hand{f}1'
        PARENT[f'{s}Hand{f}3'] = f'{s}Hand{f}2'

# mesh: drop the old head, join the rest, rigid groups
for n in HEAD_OLD:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
for o in bpy.data.objects:
    o.select_set(False)
names = sorted(P)
for n in names:
    o = P[n]
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    g = o.vertex_groups.new(name='mixamorig:' + BONE_OF[n])
    g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    o.select_set(True)
body = P[names[0]]
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'Skeleton'
body.data.materials.clear()
mat = bpy.data.materials.get('Bone') or bpy.data.materials.new('Bone')
mat.diffuse_color = (0.85, 0.8, 0.68, 1)
body.data.materials.append(mat)

arm_data = bpy.data.armatures.new('Skeleton_Rig')
rig = bpy.data.objects.new('Skeleton_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
order = ['Hips'] + [b for b in J if b != 'Hips']
for b in order:
    eb = arm_data.edit_bones.new('mixamorig:' + b)
    eb.head, eb.tail = Vector(J[b][0]), Vector(J[b][1])
for b in order:
    eb = arm_data.edit_bones['mixamorig:' + b]
    if b in PARENT:
        eb.parent = arm_data.edit_bones['mixamorig:' + PARENT[b]]
    d = (eb.tail - eb.head).normalized()
    eb.align_roll(Vector((0, 0, 1)) if abs(d.y) > 0.7 else Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = rig
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
for b in order:
    h, t = J[b]
    print('JOINT', b, np.round(h, 3), 'len', round(float(np.linalg.norm(t - h)) * 100, 1), 'cm')
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons), 'VERTS', len(body.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
