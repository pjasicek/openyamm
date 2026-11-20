"""Turn a ground-item weapon model (assets_source/engine/world_items/models/item_<icon>.glb) into a held weapon in the
space the first-person rig expects: the grip (palm) at the origin, the head along +Y, the widest side along X, the
thinnest along Z, scaled to a length per weapon kind (Oblivion units, ~1.43 cm). A design probe for WEAPONS.md, not a
pipeline: the automatic grip (by kind, from the width profile) is what a per-model override table would correct.

Usage: blender -b --python align_held.py -- <in.glb> <out.glb> <kind> [flip 0|1]
kinds: sword, greatsword, dagger, axe, greataxe, mace, hammer, staff, spear, polearm"""
import bpy, sys, math
import mathutils

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, kind = argv[:3]
force_flip = len(argv) > 3 and argv[3] == '1'

# (length, grip as a fraction of the length from the butt; None: just below the guard)
KINDS = {
    'dagger': (32, None), 'sword': (79, None), 'greatsword': (96, None),
    'axe': (50, 0.30), 'greataxe': (64, 0.30), 'mace': (53, 0.30), 'hammer': (62, 0.30),
    'staff': (120, 0.5), 'spear': (140, 0.35), 'polearm': (150, 0.35),
}
length, grip = KINDS[kind]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pts = []
for o in meshes:
    for v in o.data.vertices:
        pts.append(o.matrix_world @ v.co)
ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
order = sorted(range(3), key=lambda i: -ext[i])
ax_long, ax_wide, ax_thin = order
lo = min(p[ax_long] for p in pts)
L = ext[ax_long]
center = [(max(p[i] for p in pts) + min(p[i] for p in pts)) / 2 for i in range(3)]

def width_at(t0, t1):
    s = [p[ax_wide] for p in pts if lo + t0 * L <= p[ax_long] <= lo + t1 * L]
    return (max(s) - min(s)) if s else 0.0

# The widest slice: a sword's or dagger's guard (the butt is its nearer end), any other weapon's head.
widest_t, widest_w = 0.5, -1.0
for k in range(100):
    w = width_at(k / 100.0, (k + 1) / 100.0)
    if w > widest_w:
        widest_t, widest_w = k / 100.0 + 0.005, w
bladed = kind in ('dagger', 'sword', 'greatsword')
head_high = (widest_t < 0.5) if bladed else (widest_t >= 0.5)
if force_flip:
    head_high = not head_high
def t_from_butt(t):  # fraction from the butt -> fraction along +long
    return t if head_high else 1.0 - t
if grip is None:
    guard_from_butt = widest_t if head_high else 1.0 - widest_t
    grip_t = max(0.04, guard_from_butt - 0.06)
else:
    grip_t = grip
g_long = lo + t_from_butt(grip_t) * L
scale = length / L
sign = 1.0 if head_high else -1.0
# Basis in Blender space (Z up = glTF +Y): new X = wide axis, new Y = thin axis, new Z = long axis toward the head.
R = mathutils.Matrix.Identity(4)
for row, (axis, s) in enumerate(((ax_wide, 1.0), (ax_thin, 1.0), (ax_long, sign))):
    for col in range(3):
        R[row][col] = 0.0
    R[row][axis] = s
if R.to_3x3().determinant() < 0:
    for col in range(3):
        R[0][col] = -R[0][col]
origin = mathutils.Vector(center)
origin[ax_long] = g_long
T = mathutils.Matrix.Scale(scale, 4) @ R @ mathutils.Matrix.Translation(-origin)
# glTF is Y-up; the rig's weapon space was exported with the same convention as w_*.glb (+Y along the blade).
for o in meshes:
    o.matrix_world = T @ o.matrix_world
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_apply=True)
print('aligned', src, '->', dst, 'kind', kind, 'L', round(L, 3), 'scale', round(scale, 2), 'head_high', head_high,
      'grip_t', round(grip_t, 2))
