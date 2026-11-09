"""LOD0 reduction after weighting (rigid hard-surface budget, Patrol Unit ~5k): edit-mode collapse decimation of
work/uv_master.blend with UVs and weights interpolated: Head faces HEAD (the painted eye lives there), everything
else BODY; the thin tail tip (Tail6-8) and neck vertebrae are kept. Args: body head out_blend."""
import bpy, os, sys
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rb, rh, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Robot']; rig = bpy.data.objects['Robot_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
n0 = len(mesh.data.polygons)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
hg = mesh.vertex_groups['Head'].index
keep = {mesh.vertex_groups[n].index for n in ('Tail6', 'Tail7', 'Tail8', 'Neck1', 'Neck2')}
for is_head, ratio in ((False, float(rb)), (True, float(rh))):
    if ratio >= 0.999: continue
    hw = [sum(g.weight for g in v.groups if g.group == hg) for v in mesh.data.vertices]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    kw = [sum(g.weight for g in v.groups if g.group in keep) for v in mesh.data.vertices]
    for p in mesh.data.polygons:
        p.select = (sum(hw[i] for i in p.vertices) / len(p.vertices) >= 0.5) == is_head and max(kw[i] for i in p.vertices) < 0.5
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.decimate(ratio=ratio); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
for v in mesh.data.vertices:
    tot = sum(g.weight for g in v.groups)
    if tot > 0:
        for g in v.groups: g.weight /= tot
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, out))
print('REDUCED', n0, '->', len(mesh.data.polygons))
