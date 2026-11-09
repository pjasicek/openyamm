"""Reduce the spider's LOD0 outside the head (CLAUDE_CREATURE_TEXTURES.md "Head detail": budget is a ceiling).

Region-limited collapse decimation on work/anim_v1.blend (backup work/anim_v1_full.blend is made once): each pass
restricts a Decimate modifier to one part through a temporary vertex group, ramped to 0 within 3 cm of the piece's
ends so the leg joints keep their shape. UVs, vertex weights and the rig are kept (the texture stays valid).
Fangs are not touched; the thorax (eyes, head) loses little. Prints triangles per part before and after."""
import bpy, os, shutil, collections
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
if not os.path.exists(os.path.join(WORK, 'anim_v1_full.blend')):
    shutil.copy2(bpy.data.filepath, os.path.join(WORK, 'anim_v1_full.blend'))
mesh = bpy.data.objects['Spider']
KEEP = {'Femur': 0.45, 'Tarsus': 0.50, 'Tibia': 0.70, 'Abdomen': 0.60, 'Thorax': 0.88}


def part_of(vertex):
    name = mesh.vertex_groups[max(vertex.groups, key=lambda g: g.weight).group].name
    return name.split('_')[0] if name.startswith(('Femur', 'Tibia', 'Tarsus')) else name


def counts():
    mesh.data.calc_loop_triangles()
    parts = [part_of(v) for v in mesh.data.vertices]
    return collections.Counter(parts[t.vertices[0]] for t in mesh.data.loop_triangles)


before = counts()
print('BEFORE', dict(before), sum(before.values()))
for part, keep in KEEP.items():
    co = np.array([tuple(v.co) for v in mesh.data.vertices])
    parts = [part_of(v) for v in mesh.data.vertices]
    bones = sorted({mesh.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name
                    for v, p in zip(mesh.data.vertices, parts) if p == part})
    group = mesh.vertex_groups.new(name='Dec')
    for bone_name in bones:
        bone = bpy.data.objects['Spider_Rig'].data.bones[bone_name]
        head, tail = np.array(bone.head_local), np.array(bone.tail_local)
        idx = [i for i, v in enumerate(mesh.data.vertices)
               if mesh.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name == bone_name]
        ends = np.minimum(np.linalg.norm(co[idx] - head, axis=1), np.linalg.norm(co[idx] - tail, axis=1))
        weights = np.clip(ends / 0.03, 0.0, 1.0) if part in ('Femur', 'Tibia', 'Tarsus') else np.ones(len(idx))
        for i, w in zip(idx, weights):
            group.add([i], float(w), 'REPLACE')
    total = sum(counts().values())
    target = total - counts()[part] * (1 - keep)
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
