"""Export the cleric's cloak side labels (../mm6_cle_claude/work/cloak_sides.json on rig_v4.blend) as rest-pose face
centroids: work/cloak_side_labels.npz (cen, cloak, inner). shell_cross_cand.py maps them onto any mesh by nearest
centroid. Usage: blender -b ../mm6_cle_claude/work/rig_v4.blend -P cloak_side_labels.py"""
import bpy, json, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLE = os.path.join(os.path.dirname(HERE), 'mm6_cle_claude', 'work')
arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data
REG = json.loads(bpy.context.scene['cle_uv_regions'])
ureg = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['uv_region'].data.foreach_get('value', ureg)
CLOAK = {'CloakB', 'CloakL', 'CloakR', 'Mantle', 'CloakBi', 'CloakLi', 'CloakRi', 'Mantlei'}
inner = set(json.load(open(os.path.join(CLE, 'cloak_sides.json')))['inner'])
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([(mesh.matrix_world @ v.co)[:] for v in m.vertices])
cen = np.array([P[list(p.vertices)].mean(0) for p in me.polygons])
np.savez(os.path.join(HERE, 'work', 'cloak_side_labels.npz'), cen=cen,
         cloak=np.array([REG[ureg[i]] in CLOAK for i in range(len(me.polygons))]),
         inner=np.array([i in inner for i in range(len(me.polygons))]))
print('LABELS', len(cen), 'cloak', sum(REG[ureg[i]] in CLOAK for i in range(len(me.polygons))), 'inner', len(inner))
