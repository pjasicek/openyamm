"""Reduce the cockatrice LOD0 from 15.7k triangles (Smart Topology) to about 8k: region-limited collapse decimation
on work/anim_v1.blend (backup work/anim_v1_full.blend is made once). Each pass restricts a Decimate modifier to one
part through a temporary vertex group (dominant bone). UVs, weights and the rig are kept, so the painted texture
stays valid; do not rerun uv_export.py afterwards. The head keeps most of its density (it is seen up close)."""
import bpy, os, shutil, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
if not os.path.exists(os.path.join(WORK, 'anim_v1_full.blend')):
    shutil.copy2(bpy.data.filepath, os.path.join(WORK, 'anim_v1_full.blend'))
mesh = bpy.data.objects['Cockatrice']
KEEP = {'Leg': 0.40, 'Wing': 0.50, 'Tail': 0.50, 'Body': 0.70, 'Neck': 0.60, 'Head': 0.85}


def part_of(vertex):
    name = mesh.vertex_groups[max(vertex.groups, key=lambda g: g.weight).group].name
    if name.startswith(('UpperArm', 'ForeArm', 'Finger')):
        return 'Wing'
    if name.startswith(('Thigh', 'Shin', 'Tarsus', 'Foot')):
        return 'Leg'
    if name.startswith('Tail'):
        return 'Tail'
    if name.startswith('Neck'):
        return 'Neck'
    return 'Head' if name == 'Head' else 'Body'


def counts():
    mesh.data.calc_loop_triangles()
    parts = [part_of(v) for v in mesh.data.vertices]
    return collections.Counter(parts[t.vertices[0]] for t in mesh.data.loop_triangles)


before = counts()
print('BEFORE', dict(before), sum(before.values()))
import bmesh
for part, keep in KEEP.items():
    # Edit-mode decimate on the part's faces (a vertex-group Decimate modifier barely reduced this mesh).
    bpy.context.view_layer.objects.active = mesh
    for o in bpy.data.objects:
        o.select_set(o == mesh)
    parts = [part_of(v) for v in mesh.data.vertices]
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh.data)
    for f in bm.faces:
        f.select_set(all(parts[v.index] == part for v in f.verts))
    bmesh.update_edit_mesh(mesh.data)
    bpy.ops.mesh.decimate(ratio=keep, use_vertex_group=False, use_symmetry=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    print('PASS', part, dict(counts()))
after = counts()
print('AFTER', dict(after), sum(after.values()), 'unweighted', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_mainfile()
