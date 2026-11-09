"""Rig dimensions of a quadruped blend (read only): object names, world matrix, leg chains, shoulder/hip heights,
paw positions and trunk length. Args: -- <blend> <rig object> <mesh object>"""
import bpy, sys
from mathutils import Vector
blend, rig_name, mesh_name = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=blend)
print('OBJECTS', [(o.name, o.type) for o in bpy.data.objects])
print('ACTIONS', [a.name for a in bpy.data.actions])
rig = bpy.data.objects[rig_name]; mesh = bpy.data.objects[mesh_name]
rig.animation_data_clear() if rig.animation_data else None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = rig.matrix_world
print('RIG WORLD', [list(r) for r in W])
for b in rig.pose.bones:
    h, t = W @ b.head, W @ b.tail
    print(f'BONE {b.name:12} head {tuple(round(x, 3) for x in h)} tail {tuple(round(x, 3) for x in t)} len {b.length:.3f}')
co = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
print('MESH', len(co), 'bounds', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
