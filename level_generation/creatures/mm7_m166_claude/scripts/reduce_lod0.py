"""LOD0 reduction after weighting (edit-mode collapse per region of work/uv_master.blend, UVs and weights
interpolated): head flesh HEAD (faces within EYE_KEEP of the painted iris are kept: an eye texture tears under
collapse, mm6_bh_reduce_claude), tentacles TENT; eye stalks with their painted eyeballs, tongue and teeth kept.
Args: head tent out_blend."""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EYE_KEEP = 0.075
rh, rt, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Beholder']; rig = bpy.data.objects['Beholder_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
piece = np.load(os.path.join(P, 'work/piece_master.npy'))   # piece_map.py (the eyeball split reordered vertices)
attr = mesh.data.attributes.new('piece', 'INT', 'POINT'); attr.data.foreach_set('value', piece.astype(np.int32))
iris = Vector(json.load(open(os.path.join(P, 'work/iris.json')))['iris_centre'])
TENT = {1, 2, 3, 4, 5, 6, 9, 10, 14}
n0 = len(mesh.data.polygons)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
def region(p, pc):
    k = pc[p.vertices[0]]
    if k in TENT: return 'tent'
    if k == 0:
        c = sum((mesh.data.vertices[i].co for i in p.vertices), Vector()) / len(p.vertices)
        return 'keep' if (c - iris).length < EYE_KEEP else 'head'
    return 'keep'
for name, ratio in (('head', float(rh)), ('tent', float(rt))):
    if ratio >= 0.999: continue
    pc = [d.value for d in mesh.data.attributes['piece'].data]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in mesh.data.polygons: p.select = region(p, pc) == name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.decimate(ratio=ratio); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
for v in mesh.data.vertices:
    tot = sum(g.weight for g in v.groups)
    if tot > 0:
        for g in v.groups: g.weight /= tot
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, out))
print('REDUCED', n0, '->', len(mesh.data.polygons))
