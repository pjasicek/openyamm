"""Bow, string and arrow on the m214 rig (after author_carry.py; before twist/weights):
- bones: Bow (child of B_L_Hand, rest frame = the solved fist handle: +Y up the bow along the grip axis, the string
  toward -X, i.e. toward the forearm, turned ROLL deg about the bow axis so the full-draw anchor lies in the bow plane),
  StringNock (child of Bow, at the string's nocking point), Arrow (child of B_Pelvis; keyed in world terms by
  author_bow.py; scale 0 = hidden) and Socket_Arrow_Release (child of Bow, the arrow rest in front of the grip; no
  deformation);
- meshes joined into Body: BowMesh (100 % Bow, material Bow), ArrowMesh (100 % Arrow, material Arrow) and a 6-sided
  string tube r 1.1 mm from the top string end to the nock and on to the bottom end (weights Bow -> StringNock
  linearly along each half, the ends 0.5 % StringNock so no string triangle is wholly on the bow: StringNock only
  translates in the Bow frame, so both halves stay straight), material
  String (later a swatch of the body texture).
Writes work/bow_rig.json (frames in hand space). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
ROLL = float(os.environ.get('BOW_ROLL', '0'))
NOCK_Y = 0.03                                                     # nocking point above the grip centre (bow space)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
G = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json')))
BW = json.load(open(os.path.join(common.WORK, 'bow.json')))
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
# bow frame in hand space
hy = Vector((0, 1, 0)); bx = (hy - AX * hy.dot(AX)).normalized()
bx = Quaternion(AX, math.radians(ROLL)) @ bx
bz = bx.cross(AX)
B_hand = Matrix((bx, AX, bz)).transposed().to_4x4(); B_hand.translation = GC
H = rig.data.bones['B_L_Hand'].matrix_local
B_rest = H @ B_hand
STR_TOP, STR_BOT = Vector(BW['string']['top']), Vector(BW['string']['bottom'])
NOCK = Vector((STR_TOP.x, NOCK_Y, 0.0))
REST = Vector((0.012, 0.05, 0.0))                                 # arrow rest: front of the grip, above the hand
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones


def add(name, parent, M, length=0.12, deform=True):
    b = eb.get(name) or eb.new(name)
    b.head = M.translation; b.tail = M.translation + M.col[1].xyz * length; b.align_roll(M.col[2].xyz)
    b.parent = eb[parent]; b.use_deform = deform
    return b


add('Bow', 'B_L_Hand', B_rest, 0.2)
Mn = B_rest.copy(); Mn.translation = B_rest @ NOCK
add('StringNock', 'Bow', Mn, 0.05)
Mr = B_rest.copy(); Mr.translation = B_rest @ REST
add('Socket_Arrow_Release', 'Bow', Mr, 0.05, deform=False)
Ma = Matrix.Translation(rig.data.bones['B_R_Hand'].head_local)
add('Arrow', 'B_Pelvis', Ma, 0.3)
bpy.ops.object.mode_set(mode='OBJECT')
# ---------------------------------------------------------------- meshes
with bpy.data.libraries.load(os.path.join(common.WORK, 'props.blend')) as (src_lib, dst):
    dst.objects = ['BowMesh', 'ArrowMesh']
bow, arrow = dst.objects
for o in (bow, arrow):
    bpy.context.scene.collection.objects.link(o)
bow.matrix_world = B_rest
arrow.matrix_world = rig.data.bones['Arrow'].matrix_local
# string tube
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SEG, SIDES, RAD = 8, 6, 0.0011
pts, wn = [], []
for i in range(SEG + 1):
    t = i / SEG; pts.append(STR_TOP.lerp(NOCK, t)); wn.append(t)
for i in range(1, SEG + 1):
    t = i / SEG; pts.append(NOCK.lerp(STR_BOT, t)); wn.append(1 - t)
rings = []
for k, p in enumerate(pts):
    ring = []
    for s in range(SIDES):
        a = 2 * math.pi * s / SIDES
        ring.append(bm.verts.new(B_rest @ (p + Vector((math.cos(a) * RAD, 0, math.sin(a) * RAD)))))
    rings.append(ring)
for a_, b_ in zip(rings[:-1], rings[1:]):
    for s in range(SIDES):
        f = bm.faces.new((a_[s], a_[(s + 1) % SIDES], b_[(s + 1) % SIDES], b_[s]))
        for lp in f.loops:
            lp[uvl].uv = (0.5, 0.5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
sme = bpy.data.meshes.new('StringMesh'); bm.to_mesh(sme); bm.free()
string = bpy.data.objects.new('StringMesh', sme); bpy.context.scene.collection.objects.link(string)
ms = bpy.data.materials.new('String'); ms.diffuse_color = (0.85, 0.8, 0.65, 1); sme.materials.append(ms)
# weights, piece ids and join (the body keeps material slot 0)
if not body.data.materials:
    body.data.materials.append(bpy.data.materials.get('Body') or bpy.data.materials.new('Body'))
nv0 = len(body.data.vertices)
pv = np.zeros(nv0, np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
PIECE = {'BowMesh': 100, 'ArrowMesh': 101, 'StringMesh': 102}
for o in (bow, arrow, string):
    o.vertex_groups.clear()
    for n in ('Bow', 'Arrow', 'StringNock'):
        o.vertex_groups.new(name=n)
    n = len(o.data.vertices)
    if o is bow:
        o.vertex_groups['Bow'].add(list(range(n)), 1.0, 'REPLACE')
    elif o is arrow:
        o.vertex_groups['Arrow'].add(list(range(n)), 1.0, 'REPLACE')
    else:
        for i in range(n):
            w = max(wn[i // SIDES], 0.005)    # never 100 % Bow: split_attachment.py refuses item/body mixed triangles
            if w < 1:
                o.vertex_groups['Bow'].add([i], 1 - w, 'REPLACE')
            if w > 0:
                o.vertex_groups['StringNock'].add([i], w, 'REPLACE')
    a = o.data.attributes.new('piece', 'INT', 'POINT'); a.data.foreach_set('value', [PIECE[o.name]] * n)
    oc = o.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT')
    oc.data.foreach_set('vector', np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]).ravel())
    if 'garment' in body.data.attributes:
        o.data.attributes.new('garment', 'INT', 'POINT').data.foreach_set('value', [9] * n)
    if 'finger' in body.data.attributes:
        o.data.attributes.new('finger', 'INT', 'POINT').data.foreach_set('value', [0] * n)
for g in ('Bow', 'Arrow', 'StringNock'):
    if g not in body.vertex_groups:
        body.vertex_groups.new(name=g)
for o in bpy.data.objects:
    o.select_set(o in (body, bow, arrow, string))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
json.dump({'roll_deg': ROLL, 'bow_hand': [list(r) for r in B_hand], 'nock_bow': list(NOCK), 'rest_bow': list(REST),
           'string_top': list(STR_TOP), 'string_bottom': list(STR_BOT)},
          open(os.path.join(common.WORK, 'bow_rig.json'), 'w'), indent=1)
print('BOWRIG roll', ROLL, 'bones Bow/StringNock/Arrow/Socket_Arrow_Release; body verts', nv0, '->', len(body.data.vertices),
      'materials', [m.name for m in body.data.materials])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
