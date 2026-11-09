"""Place Socket_Palm_Left/Right at the palm (after refit_hands.py): centre of the palm skin between the wrist and the
knuckles, 2 cm out from the palm surface. Spell glows and hand effects attach here."""
import bpy, sys, os
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import author_clips as A
import posing as P

rig = A.rig; mesh = bpy.data.objects['Peasant']
P.reset(rig)
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
for side in ('Left', 'Right'):
    f, p = A.HAND_REST[side]
    wrist = P.bone_world(rig, side + 'Hand')
    knuckle = P.bone_world(rig, side + 'HandMiddle1')
    span = (knuckle - wrist).dot(f)
    d = co - np.array(wrist)
    along = d @ np.array(f); normal = d @ np.array(p)
    lateral = np.linalg.norm(d - np.outer(along, f) - np.outer(normal, p), axis=1)
    palm = (along > 0.35 * span) & (along < 0.75 * span) & (lateral < 0.035) & (np.abs(normal) < 0.06)
    centre = Vector(co[palm].mean(0))
    surface = float(normal[palm].max())
    target = centre + p * (surface - (centre - wrist).dot(p) + 0.02)
    sock = bpy.data.objects[f'Socket_Palm_{side}']
    sock.matrix_world = Matrix.Translation(target)
    print('SOCKET', side, 'palm verts', int(palm.sum()), 'at', tuple(round(x, 3) for x in target),
          'along', round((target - wrist).dot(f), 3), 'out of palm', round(surface + 0.02, 3))
bpy.ops.wm.save_mainfile()
