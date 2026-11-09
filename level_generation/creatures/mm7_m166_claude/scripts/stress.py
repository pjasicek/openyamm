"""Beholder stress poses on work/rig_v1.blend -> review/stress_sheet.png: rest (bones), tentacles curled in,
tentacles flung out, stalks bent and eyeball popped, body tipped forward."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rig_v1.blend'))
import common_render as C
rig = bpy.data.objects['Beholder_Rig']
def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()
def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()
def chains(prefix):
    out = {}
    for b in rig.pose.bones:
        if b.name.startswith(prefix): out.setdefault(b.name.split('_')[0], []).append(b.name)
    return {k: sorted(v) for k, v in out.items()}
def bend(prefix, deg):
    """Bend every chain about the horizontal axis perpendicular to its radial direction (+ = tips swing outward)."""
    head = rig.pose.bones['Head'].head
    for names in chains(prefix).values():
        b0 = rig.pose.bones[names[0]]; r = (b0.tail - head); r.z = 0
        axis = Vector((0, 0, 1)).cross(r.normalized() if r.length > 1e-4 else Vector((1, 0, 0)))
        for n in names: rot(n, -axis, deg)
POSES = {'rest': lambda: None, 'curl': lambda: bend('Tentacle', -14), 'fling': lambda: bend('Tentacle', 18),
         'stalks': lambda: (bend('Stalk', 30), rig.pose.bones['EyeBall'].location.__setitem__(1, 0.1)),
         'tip': lambda: (rot('Body', (1, 0, 0), 35), bend('Tentacle', 8))}
cells = []
os.makedirs(os.path.join(HERE, 'review/stress'), exist_ok=True)
for name, fn in POSES.items():
    reset(); fn(); bpy.context.view_layer.update()
    for view, loc in (('front', (0, -1.6, 0.5)), ('q', (-1.0, -1.1, 1.0))):
        p = os.path.join(HERE, f'review/stress/{name}_{view}.png')
        C.render_ortho(loc, (0, 0, 0.45), 1.15, p, bones=(name == 'rest'), mesh_name='Beholder', rig_name='Beholder_Rig'); cells.append(p)
C.sheet(os.path.join(HERE, 'review/stress_sheet.png'), cells, 4)
print('SHEET')
