"""Reduce the Flying Eye's LOD0 (CLAUDE_CREATURE_TEXTURES.md "Head detail": budget is a ceiling) on
work/anim_v1.blend (backup work/anim_v1_full.blend is made once). Region-limited collapse decimation keeps UVs,
weights and the painted texture: horns 40 %, lumpy back skin 50 %, face side (cheeks, chin, tendrils) 80 %; the
separate pieces (eyeball, teeth, gum, brow ring, crest) are untouched. Regions are on the main head piece
(work/component_labels.npy): horns |x| > 0.17 above z 0.33, back y > -0.12, the rest is face.
Do not rerun uv_export.py afterwards (it would re-UV the reduced mesh and break the painted texture)."""
import bpy, os, shutil, collections
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
if not os.path.exists(os.path.join(WORK, 'anim_v1_full.blend')):
    shutil.copy2(bpy.data.filepath, os.path.join(WORK, 'anim_v1_full.blend'))
mesh = bpy.data.objects['Eye']
KEEP = {'horns': 0.40, 'back': 0.50, 'face': 0.80}
MAIN_PIECE = 1
# Piece labels follow the original vertex order; carry them as an attribute so they survive decimation.
if 'piece' not in mesh.data.attributes:
    labels = np.load(os.path.join(WORK, 'component_labels.npy'))
    mesh.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', labels.astype(int).tolist())


def regions():
    piece = [d.value for d in mesh.data.attributes['piece'].data]
    out = []
    for v, k in zip(mesh.data.vertices, piece):
        x, y, z = v.co
        if k != MAIN_PIECE:
            out.append('pieces')
        elif abs(x) > 0.17 and z > 0.33:
            out.append('horns')
        elif y > -0.12:
            out.append('back')
        else:
            out.append('face')
    return out


def counts():
    mesh.data.calc_loop_triangles()
    r = regions()
    return collections.Counter(r[t.vertices[0]] for t in mesh.data.loop_triangles)


print('BEFORE', dict(counts()))
for region, keep in KEEP.items():
    r = regions()
    group = mesh.vertex_groups.new(name='Dec')
    group.add([i for i, name in enumerate(r) if name == region], 1.0, 'REPLACE')
    c = counts(); total = sum(c.values())
    mod = mesh.modifiers.new('Dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'; mod.ratio = (total - c[region] * (1 - keep)) / total
    mod.vertex_group = 'Dec'; mod.vertex_group_factor = 1.0; mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = mesh
    while mesh.modifiers[0].name != 'Dec':
        bpy.ops.object.modifier_move_up(modifier='Dec')
    bpy.ops.object.modifier_apply(modifier='Dec')
    mesh.vertex_groups.remove(mesh.vertex_groups['Dec'])
    print('PASS', region, dict(counts()))
after = counts()
mesh.data.attributes.remove(mesh.data.attributes['piece'])
print('AFTER', dict(after), sum(after.values()), 'unweighted', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_mainfile()
