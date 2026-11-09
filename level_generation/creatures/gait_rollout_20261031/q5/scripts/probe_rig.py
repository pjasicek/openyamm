"""Print the MM9 wolf rig of mm9_wolf_claude/work/anim_v3.blend (read only): bones with parent, world head/tail and
length at rest, the mesh's lowest vertices per paw bone, and the actions with their frame ranges.

    blender -b --factory-startup -P probe_rig.py
"""
import bpy, os
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm9_wolf_claude', 'work', 'anim_v3.blend'))
print('OBJECTS', [(o.name, o.type) for o in bpy.data.objects])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == rig and o.name == 'Wolf')
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = rig.matrix_world
for b in rig.pose.bones:
    h = W @ b.head; t = W @ b.tail
    print(f'BONE {b.name:8} parent {b.parent.name if b.parent else "-":8} head {h.x:+.3f} {h.y:+.3f} {h.z:+.3f} '
          f'tail {t.x:+.3f} {t.y:+.3f} {t.z:+.3f} len {b.length:.3f}')
names = [g.name for g in mesh.vertex_groups]
co = np.array([mesh.matrix_world @ v.co for v in mesh.data.vertices])
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
print('MESH', mesh.name, len(co), 'z', co[:, 2].min(), co[:, 2].max(), 'y', co[:, 1].min(), co[:, 1].max())
for paw in ('Bone19', 'Bone05', 'Bone09', 'Bone42', 'Bone13', 'Bone18', 'Bone03', 'Bone08'):
    c = co[dom == paw]
    if len(c):
        i = np.argmin(c[:, 2])
        print(f'PAW {paw}: n {len(c)} lowest {c[i]} y range {c[:, 1].min():+.3f}..{c[:, 1].max():+.3f}')
for a in bpy.data.actions:
    print('ACTION', a.name, tuple(a.frame_range), 'fps', bpy.context.scene.render.fps)
print('OTHER MESHES', [(o.name, o.parent.name if o.parent else None) for o in bpy.data.objects if o.type == 'MESH'])
