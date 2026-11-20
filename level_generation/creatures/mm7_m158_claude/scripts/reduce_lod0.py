"""LOD0 reduction after weighting (game asset guidelines): collapse-decimate the body and wings to BODY_RATIO and the
head/ears to HEAD_RATIO in edit mode (UVs and weights interpolated), on a copy of work/uv_master.blend.
Args: body_ratio head_ratio out_blend."""
import bpy, bmesh, os, sys
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
body_ratio, head_ratio, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Bat']; rig = bpy.data.objects['Bat_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
head = {mesh.vertex_groups[n].index for n in ('Head', 'Ear_L', 'Ear_R', 'Neck1')}
hw = [sum(g.weight for g in v.groups if g.group in head) for v in mesh.data.vertices]
n0 = len(mesh.data.polygons)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
for sel_head, ratio in ((False, float(body_ratio)), (True, float(head_ratio))):
    if ratio >= 0.999: continue
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    hw = [sum(g.weight for g in v.groups if g.group in head) for v in mesh.data.vertices]
    for p in mesh.data.polygons:
        is_head = sum(hw[i] for i in p.vertices) / len(p.vertices) >= 0.5
        p.select = is_head == sel_head
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.decimate(ratio=ratio)
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
for v in mesh.data.vertices:   # renormalise weights
    tot = sum(g.weight for g in v.groups)
    if tot > 0:
        for g in v.groups: g.weight /= tot
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, out))
print('REDUCED', n0, '->', len(mesh.data.polygons))
