"""Reduce the Patrol Unit's LOD0 from 14.3k triangles (user review 2026-10-08: far too many for a sphere).

Region-limited collapse decimation on work/anim_v1.blend (backup work/anim_v1_full.blend is made once): each pass
restricts a Decimate modifier to one rigid part through a temporary vertex group. UVs, vertex weights and the rig
are kept, so the Meshy texture stays valid; do not rerun uv_export.py afterwards. Prints triangles per part."""
import bpy, os, shutil, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
if not os.path.exists(os.path.join(WORK, 'anim_v1_full.blend')):
    shutil.copy2(bpy.data.filepath, os.path.join(WORK, 'anim_v1_full.blend'))
mesh = bpy.data.objects['Robot']
PART = {'CapTop': 'Core', 'CapBottom': 'Core', 'RingTop': 'RingTop', 'RingBottom': 'RingBottom', 'Eye': 'Eye',
        'Sensor': 'Sensor'}
KEEP = {'RingTop': 0.30, 'RingBottom': 0.30, 'Core': 0.40, 'Sensor': 0.30, 'Eye': 0.35}


def part_of(vertex):
    return PART[mesh.vertex_groups[max(vertex.groups, key=lambda g: g.weight).group].name]


def counts():
    mesh.data.calc_loop_triangles()
    parts = [part_of(v) for v in mesh.data.vertices]
    return collections.Counter(parts[t.vertices[0]] for t in mesh.data.loop_triangles)


before = counts()
print('BEFORE', dict(before), sum(before.values()))
for part, keep in KEEP.items():
    group = mesh.vertex_groups.new(name='Dec')
    group.add([v.index for v in mesh.data.vertices if part_of(v) == part], 1.0, 'REPLACE')
    current = counts()
    total = sum(current.values())
    target = total - current[part] * (1 - keep)
    mod = mesh.modifiers.new('Dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'; mod.ratio = target / total
    mod.vertex_group = 'Dec'; mod.vertex_group_factor = 1.0; mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = mesh
    while mesh.modifiers[0].name != 'Dec':
        bpy.ops.object.modifier_move_up(modifier='Dec')
    bpy.ops.object.modifier_apply(modifier='Dec')
    mesh.vertex_groups.remove(mesh.vertex_groups['Dec'])
    print('PASS', part, dict(counts()))
after = counts()
print('AFTER', dict(after), sum(after.values()), 'unweighted', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_mainfile()
