"""Faces of one LOD that stretch over 20x their rest area (lod_check.py) at their worst frame: rest/posed area, rest
centre, material, dominant bones. Usage: blender -b -P stretch_probe.py -- <lodcheck glb> <clip,...>"""
import sys, bpy, bmesh, numpy as np
glb, clips = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.import_scene.gltf(filepath=glb); o = bpy.data.objects['Dwarf']; sc = bpy.context.scene
rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE'); rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
def st():
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.faces.ensure_lookup_table()
    r = np.array([f.calc_area() for f in b.faces]), [f.calc_center_median().copy() for f in b.faces]; b.free(); return r
a0, c0 = st(); vg = {g.index: g.name for g in o.vertex_groups}
for clip in clips.split(','):
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); a1, _ = st(); bad = np.where((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9)))[0]
        for i in bad:
            p = o.data.polygons[int(i)]
            bones = sorted({vg[max(o.data.vertices[v].groups, key=lambda g: g.weight).group] for v in p.vertices})
            print('STRETCH', clip, f, int(i), 'rest mm2', round(a0[i] * 1e6, 3), 'posed mm2', round(a1[i] * 1e6, 2), 'centre', [round(x, 3) for x in c0[i]], o.data.materials[p.material_index].name, bones)
        if len(bad): break
