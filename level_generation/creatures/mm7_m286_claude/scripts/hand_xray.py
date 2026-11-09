"""G5 X-ray of one hand at rest: ghost mesh + the rig's hand/finger joint heads (thumb red, index orange, middle
yellow, ring green, pinky blue; darker = more distal) and chain rods; four views around the hand.
Args: -- <rig blend> <side R|L> <out prefix>"""
import bpy, bmesh, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, side, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mat = bpy.data.materials.new('ghost'); mat.diffuse_color = (0.85, 0.85, 0.85, 0.3)
body.data.materials.clear(); body.data.materials.append(mat)
COL = [(0.9, 0.1, 0.1), (1.0, 0.5, 0.0), (0.95, 0.85, 0.1), (0.1, 0.8, 0.2), (0.1, 0.4, 0.95)]


def ball(p, r, c):
    me = bpy.data.meshes.new('b'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('b', me); bpy.context.scene.collection.objects.link(o)
    o.location = p; m = bpy.data.materials.new('c'); m.diffuse_color = c + (1,); me.materials.append(m)


def chain(f):
    a = f'B_{side}_Finger{f}'
    kids = [a]
    while True:
        k = [b.name for b in rig.data.bones if b.parent and b.parent.name == kids[-1]]
        if not k:
            return kids
        kids.append(k[0])


W = rig.matrix_world
hand = W @ rig.data.bones[f'B_{side}_Hand'].head_local
ball(hand, 0.006, (0.2, 0.2, 0.2))
for f in (0,) + tuple(int(x) for x in os.environ.get('FINGERS', '1,2,3,4').split(',')):
    for j, n in enumerate(chain(f)):
        c = tuple(x * (1 - 0.3 * j) for x in COL[f])
        ball(W @ rig.data.bones[n].head_local, 0.0045, c)
import json
FIT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'fingers_fit.json')
if os.environ.get('SHOW_FIT') and os.path.exists(FIT):
    fit = json.load(open(FIT))[side]
    order = ['thumb', 'index', 'middle', 'ring', 'pinky']
    for n, pts in fit.items():
        for k, p in enumerate(pts):
            if k % 2 == 0:
                ball(Vector(p), 0.0025, tuple(0.5 * x for x in COL[order.index(n)]))
# frame check: the source fingers carried by our hand's rest swing (scaled by the hand length ratio) as small black
# balls; with a right hand frame they lie along our fingers, thumb on the thumb side
from mathutils import Quaternion
SRC = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'source_rest.json')))
off = json.loads(bpy.context.scene['rig_offsets'])
qh = Quaternion(off[f'B_{side}_Hand']['q']); h0 = Vector(SRC[f'B_{side}_Hand']['head'])
ours = [rig.data.bones[f'B_{side}_Finger{f}'].head_local for f in (1, 2, 3)]
srcs = [qh @ (Vector(SRC[f'B_{side}_Finger{f}']['head']) - h0) for f in (1, 2, 3)]
k = sum(((o - hand) @ (s_.normalized())) for o, s_ in zip(ours, srcs)) / sum(s_.length for s_ in srcs)
for f in range(5):
    for n in chain(f):
        ball(hand + qh @ ((Vector(SRC[n]['head']) - h0) * k), 0.003, (0.02, 0.02, 0.02))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.6
tip = hand + (W @ rig.data.bones[f'B_{side}_Finger2'].head_local - hand) * 1.6
for v in ('front', 'left', 'right', 'back'):
    common.render_views(f'{out}_{v}', tip.z, 0.34, views=(v,), resolution=(400, 400), target=(tip.x, tip.y))
