"""Bow, string and arrow on the Medusa rig: work/rig_v1.blend + work/props.blend -> work/rig_v2.blend.
Bones (after mm7_m154_claude/scripts/bow_tracks.py):
- Bow (child of Hand_L, deforming the bow mesh and the string ends). Rest frame in the hand: origin at the handle
  centre GRIP (just in front of the palm at the finger roots: palm surface + handle half-depth), +Y up the bow = the
  hand's index side (-hand X: the left hand's local X is its pinky side), +X toward the string = back toward the
  wrist (-hand Y), +Z = -palm normal.
- StringNock (child of Bow) at the string's nocking point.
- Socket_Arrow_Release (child of Bow, non-deforming): the arrow rest just above the grip on the archer's side,
  +Y pointing out of the bow toward the target (-X of the bow).
- Arrow (no parent, deforming the arrow mesh; keyed in armature space; scale 0 = hidden).
Writes work/bow_rig.json (frames in hand space). Args: none"""
import bpy, os, json
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, 'work', *p)
bpy.ops.wm.open_mainfile(filepath=W('rig_v1.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
GEO = json.load(open(os.path.join(HERE, 'textures', 'props', 'bow_geometry.json')))
HS = json.load(open(W('hands.json')))['L']
with bpy.data.libraries.load(W('props.blend')) as (src, dst):
    dst.objects = ['BowMesh', 'StringMesh', 'ArrowMesh']
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
bow, string, arrow = (bpy.data.objects[n] for n in ('BowMesh', 'StringMesh', 'ArrowMesh'))
Hm = rig.data.bones['Hand_L'].matrix_local.copy()               # armature space (rig has identity transform)
L = rig.data.bones['Hand_L'].length
# palm surface at the finger roots (hand-local), from the hand piece
co = np.array([tuple(v.co) for v in body.data.vertices]); pv = np.zeros(len(co), np.int32)
body.data.attributes['piece'].data.foreach_get('value', pv)
hl = np.array([tuple(Hm.inverted() @ Vector(p)) for p in co[pv == 5]])
band = hl[(hl[:, 1] > 0.75 * L) & (hl[:, 1] < 0.95 * L) & (np.abs(hl[:, 0]) < 0.03)]
palm_z = float(np.percentile(band[:, 2], 95))
HANDLE_R = GEO['grip_half_depth']
GRIP = Vector((0.0, 0.86 * L, palm_z + HANDLE_R + 0.004))
B_hand = Matrix((Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((0, 0, -1)))).transposed().to_4x4()   # cols: bowX=-hY, bowY=-hX (left hand X = pinky side, so the bow's top is at the index), bowZ=-hZ
B_hand.translation = GRIP
B_rest = Hm @ B_hand
NOCK = Vector((GEO['string_x'], 0.0, 0.0))
REST = Vector((-0.012, 0.035, 0.012))                    # arrow rest above the grip (bow frame)
print('PROP grip hand-local', [round(x, 4) for x in GRIP], 'palm z', round(palm_z, 4), 'handle r', round(HANDLE_R, 4))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones


def add(name, parent, M, length, deform=True):
    b = eb.get(name) or eb.new(name)
    b.head = M.translation; b.tail = M.translation + M.col[1].xyz.normalized() * length; b.align_roll(M.col[2].xyz)
    b.parent = eb[parent] if parent else None; b.use_deform = deform


add('Bow', 'Hand_L', B_rest, 0.2)
Mn = B_rest.copy(); Mn.translation = B_rest @ NOCK; add('StringNock', 'Bow', Mn, 0.05)
d = -B_rest.col[0].xyz.normalized(); up = B_rest.col[1].xyz.normalized(); xx = d.cross(up).normalized()
Ms = Matrix((xx, d, xx.cross(d))).transposed().to_4x4(); Ms.translation = B_rest @ REST
add('Socket_Arrow_Release', 'Bow', Ms, 0.05, deform=False)
add('StringTips', 'Bow', B_rest, 0.1)                      # string ends: rigid with the bow, but not on the Bow joint
                                                            # itself, so split_attachment leaves the whole string in the body
Ma = Ms.copy(); Ma.translation = B_rest @ NOCK
add('Arrow', None, Ma, 0.3)
bpy.ops.object.mode_set(mode='OBJECT')
# props into armature space, skinned
gs = string.vertex_groups['Bow']; gs.name = 'StringTips'
for o, M, groups in ((bow, B_rest, {'Bow': None}), (string, B_rest, None), (arrow, Ma, {'Arrow': None})):
    o.data.transform(M); o.matrix_world = Matrix()
    if groups:
        g = o.vertex_groups.new(name=list(groups)[0]); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    o.parent = rig
    m = o.modifiers.new('Armature', 'ARMATURE'); m.object = rig
json.dump({'bow_hand': [list(r) for r in B_hand], 'nock_bow': list(NOCK), 'rest_bow': list(REST), 'grip_hand': list(GRIP),
           'handle_r': HANDLE_R, 'arrow_len': GEO['arrow_len']}, open(W('bow_rig.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=W('rig_v2.blend'))
print('SAVED rig_v2 bones', len(rig.data.bones))
