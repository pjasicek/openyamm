"""Staff/palm sockets and staff texture: work/rig_v6.blend -> work/rig_v7.blend, textures/staff_basecolor.png.
 - 'Socket_Palm_Left/Right': non-deform bones at each fist shell's centre, children of the hand bones.
 - 'Socket_Staff_Head': non-deform bone (glTF node) at the centre of the club head, child of the 'Staff' bone, for the
   engine's ranged_hand_sockets (fire effect at the staff head) and the palm_* cast-glow sockets.
 - UVs: cylindrical in the staff's own frame (u = angle round the shaft, v = position along it), caps squeezed into the
   ends; per-face unwrapping keeps the seam faces continuous.
 - Base colour 256 x 1024: native pmn2sta0 staff colours (head ~ RGB 135/108/73 weathered light brown, shaft
   114/84/55; the sprite's darker foot is mostly its top lighting, so only a slight darkening is baked) with seeded
   lengthwise grain, knots and a worn grip band."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v6.blend'))
arm = bpy.data.objects['Mage_Rig']; staff = bpy.data.objects['Staff']; scene = bpy.context.scene
ST = json.loads(scene['pmn2_staff']); L = ST['length']; d = Vector(ST['axis']).normalized(); grip = Vector(ST['grip'])
GRIP_FROM_FOOT = L * 0.71
foot = grip - d * GRIP_FROM_FOOT

# socket bone at the head centre (widest part of the club head, 0.11 m below the top)
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
if 'Socket_Staff_Head' in eb:
    eb.remove(eb['Socket_Staff_Head'])
sb = eb.new('Socket_Staff_Head'); centre = foot + d * (L - 0.11)
sb.head = inv @ centre; sb.tail = inv @ (centre + d * 0.05); sb.parent = eb['Staff']; sb.use_deform = False
# palm sockets at the centre of each fist shell (cast glow forms between the palms, like the other casters)
mesh = bpy.data.objects['Mage']; mme = mesh.data
PARTS = json.loads(scene['pmn2_parts'])
part = np.zeros(len(mme.polygons), dtype=np.int32); mme.attributes['part'].data.foreach_get('value', part)
for side, shell in (('Left', 'HandLeft'), ('Right', 'HandRight')):
    vs = {vi for p in mme.polygons if PARTS[part[p.index]] == shell for vi in p.vertices}
    c = sum((mesh.matrix_world @ mme.vertices[i].co for i in vs), Vector()) / len(vs)
    name = 'Socket_Palm_' + side
    if name in eb:
        eb.remove(eb[name])
    pb_ = eb.new(name); pb_.head = inv @ c; pb_.tail = inv @ (c + Vector((0, 0, 0.04))); pb_.parent = eb['mixamorig:%sHand' % side]
    pb_.use_deform = False
    print('SOCKET', name, [round(x, 3) for x in c])
bpy.ops.object.mode_set(mode='OBJECT')
print('SOCKET Socket_Staff_Head at', [round(x, 3) for x in centre], 'm from the grip', round((centre - grip).length, 3))

# cylindrical UVs in the staff frame
u_ax = d.orthogonal().normalized(); w_ax = d.cross(u_ax)
me = staff.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.active
for f in bm.faces:
    pts = [staff.matrix_world @ l.vert.co for l in f.loops]
    t = [(p - foot).dot(d) / L for p in pts]
    ang = [math.atan2((p - foot).dot(w_ax), (p - foot).dot(u_ax)) / (2 * math.pi) + 0.5 for p in pts]
    for i in range(1, len(ang)):                      # keep the face on one side of the seam
        while ang[i] - ang[0] > 0.5: ang[i] -= 1
        while ang[i] - ang[0] < -0.5: ang[i] += 1
    for l, a_, t_ in zip(f.loops, ang, t):
        l[uv].uv = (a_ % 1.0 if min(ang) >= 0 else a_ + 1.0 if max(ang) < 1 else a_, min(max(t_, 0.0), 1.0))
bm.to_mesh(me); bm.free()

# base colour
W, H = 256, 1024
rng = np.random.default_rng(6)
v = np.linspace(0, 1, H)[:, None]; u = np.linspace(0, 1, W)[None, :]
shaft = np.array([114, 84, 55], float); head = np.array([140, 112, 76], float)
head_start = (L - 0.26) / L
blend = np.clip((v - head_start + 0.02) / 0.04, 0, 1)
base = shaft * (1 - blend) + head * blend
base = base * (0.90 + 0.10 * np.clip(v / 0.5, 0, 1))[..., None] if base.ndim == 3 else base
img = np.broadcast_to(base[:, None, :] if base.ndim == 2 else base, (H, W, 3)).astype(float).copy()
img *= (0.90 + 0.10 * np.clip(v / 0.5, 0, 1))[..., None]          # slight darkening toward the foot
grain = np.zeros((H, W))
for k in range(1, 7):                                  # lengthwise streaks: noisy across u, smooth along v
    phase = rng.uniform(0, 2 * np.pi, (1, W)); freq = rng.uniform(0.5, 3.0) * k
    grain += np.sin(2 * np.pi * freq * v + phase + 3 * np.sin(2 * np.pi * u * k)) / k
grain += 0.6 * np.repeat(rng.normal(0, 1, (1, W)), H, 0) * 0.5
grain = (grain - grain.mean()) / grain.std()
img *= (1 + 0.07 * grain)[..., None]
for _ in range(9):                                      # knots
    cy, cx = rng.uniform(0.05, 0.95) * H, rng.uniform(0, 1) * W
    yy, xx = np.ogrid[:H, :W]; dx = np.minimum(abs(xx - cx), W - abs(xx - cx))
    r = np.sqrt((dx / 9.0) ** 2 + ((yy - cy) / 5.0) ** 2)
    img *= (1 - 0.28 * np.exp(-r ** 2))[..., None]
gy = int(GRIP_FROM_FOOT / L * H)                        # worn, darker grip band (both hands' area)
band = np.exp(-(((np.arange(H) - gy) / (0.09 / L * H)) ** 2))[:, None]
img *= (1 - 0.12 * band)[..., None]
img = np.clip(img, 0, 255).astype(np.uint8)[::-1]       # image row 0 = v 1
os.makedirs(os.path.join(common.PROJECT, 'textures'), exist_ok=True)
path = os.path.join(common.PROJECT, 'textures', 'staff_basecolor.png')
bimg = bpy.data.images.new('staff_basecolor', W, H)
bimg.pixels = (np.concatenate([img[::-1], np.full((H, W, 1), 255, np.uint8)], 2).astype(np.float32) / 255).ravel()
bimg.filepath_raw = path; bimg.file_format = 'PNG'; bimg.save()
mat = bpy.data.materials.new('Staff'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bimg
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.8; bsdf.inputs['Metallic'].default_value = 0.0
me.materials.clear(); me.materials.append(mat)
print('STAFF texture', path, 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v7.blend'))
sc = scene; common.workbench_clay(sc, textured=True)
common.render_views(os.path.join(common.REVIEW, 'staff_tex'), float(centre.z) - 0.3, 0.9, views=('front', 'three_quarter'), resolution=(400, 400), target=(float(centre.x), float(centre.y)))
