"""LOD0 reduction after weighting: edit-mode collapse decimation per region of work/uv_master.blend (UVs and weights
interpolated): abdomen/claw body BODY, head and neck HEAD, wings WING, the small separate pieces (spine crest,
bristles, mandibles, claw prongs) SMALL. Args: body head wing small out_blend."""
import bpy, os, sys
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rb, rh, rw, rk, out = sys.argv[sys.argv.index('--') + 1:][:5]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Dragonfly']; rig = bpy.data.objects['Dragonfly_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
piece = np.load(os.path.join(P, 'work/raw_st1.npz'))['part']
mesh['piece'] = 0
attr = mesh.data.attributes.new('piece', 'INT', 'POINT'); attr.data.foreach_set('value', piece.astype(np.int32))
head = {mesh.vertex_groups[n].index for n in ('Head', 'Neck')}
n0 = len(mesh.data.polygons)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
def region(p, pc, hw):
    k = pc[p.vertices[0]]
    if k in (1, 2, 4, 5): return 'wing'
    if k != 0: return 'keep'
    return 'head' if sum(hw[i] for i in p.vertices) / len(p.vertices) >= 0.5 else 'body'
for name, ratio in (('body', float(rb)), ('head', float(rh)), ('wing', float(rw)), ('keep', float(rk))):
    if ratio >= 0.999: continue
    pc = [d.value for d in mesh.data.attributes['piece'].data]
    hw = [sum(g.weight for g in v.groups if g.group in head) for v in mesh.data.vertices]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in mesh.data.polygons: p.select = region(p, pc, hw) == name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.decimate(ratio=ratio); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
for v in mesh.data.vertices:
    tot = sum(g.weight for g in v.groups)
    if tot > 0:
        for g in v.groups: g.weight /= tot
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, out))
print('REDUCED', n0, '->', len(mesh.data.polygons))
