"""Per-face labels of the Dwarf's final rest mesh (../mm9_dwarf_claude/work/final_v1.blend, object Body), before
export_dwarf.py strips them: part (1 voxel skin: tunic, sleeves, forearms, bracers; 4 glove; 5 pants; 6 boot; 7 skirt;
9 belt; 11 boot cuff; 12 shoulder plates/trims; 30 axe), mat, lining, weapon, hand, centroid (world) and the vertex
indices' world positions. -> work/final_faces.npz. Blender: -P dump_parts_blend.py"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_dwarf_claude', 'work', 'final_v1.blend'))
body = bpy.data.objects['Body']; rig = body.parent
if rig and rig.animation_data: rig.animation_data.action = None
if rig:
    for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; n = len(me.polygons)
out = {}
for a in ('part', 'mat', 'lining', 'weapon', 'hand'):
    v = np.zeros(n, np.int32)
    if a in me.attributes and me.attributes[a].domain == 'FACE':
        me.attributes[a].data.foreach_get('value', v)
    out[a] = v
    print('ATTR', a, a in me.attributes, np.unique(v, return_counts=True))
M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
tri = [p.vertices[:] for p in me.polygons]
print('POLY sizes', np.unique([len(t) for t in tri], return_counts=True))
cen = np.array([co[list(t)].mean(0) for t in tri])
out['cen'] = cen; out['matidx'] = np.array([p.material_index for p in me.polygons])
np.savez(os.path.join(HERE, 'work', 'final_faces.npz'), **out)
print('DUMPED', n, 'faces', len(co), 'verts', 'groups', len(body.vertex_groups))
