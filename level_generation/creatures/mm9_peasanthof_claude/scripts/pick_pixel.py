"""Diagnostics (2026-11-04): what surface is under a pixel of a head_closeups.py view. Same camera as head_closeups (view name, HEAD_FWD,
HEAD_DZ), ray cast from the ortho camera through pixel (px, py) of a 360x360 tile; prints the hit material, location and the face's
dominant bones. Args: <glb> <view> <px,py;px,py...>"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): bpy.data.objects.remove(o)
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
VIEWS = {'front': (0, 0.03, 0.3), 'q34': (35, 0.03, 0.3), 'rside': (-90, 0.03, 0.3)}
ang, dz, scale = VIEWS[a[1]]
hb = next(b for b in rig.pose.bones if b.name.endswith('Head'))
m = rig.matrix_world @ hb.matrix
t = m.translation + Vector((0, -float(os.environ.get('HEAD_FWD', '0')), float(os.environ.get('HEAD_DZ', '-0.02')))) + Vector((0, 0, dz))
r = math.radians(ang); camloc = t + Vector((math.sin(r) * 2, -math.cos(r) * 2, 0))
fwd = (t - camloc).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
dg = bpy.context.evaluated_depsgraph_get()
for spec in a[2].split(';'):
    px, py = (float(v) for v in spec.split(','))
    o = camloc + right * ((px / 360 - 0.5) * scale) + up * ((0.5 - py / 360) * scale)
    hit, loc, nor, fi, ob, _ = bpy.context.scene.ray_cast(dg, o, fwd)
    if not hit: print('PICK', spec, 'nothing'); continue
    me = ob.data; poly = me.polygons[fi]; mat = me.materials[poly.material_index].name if me.materials else '-'
    vg = {}
    for vi in poly.vertices:
        for g in me.vertices[vi].groups: vg[ob.vertex_groups[g.group].name] = vg.get(ob.vertex_groups[g.group].name, 0) + g.weight
    top = sorted(vg.items(), key=lambda kv: -kv[1])[:3]
    print('PICK', spec, ob.name, 'face', fi, 'mat', mat, 'loc', [round(x, 3) for x in loc], 'normal', [round(x, 2) for x in nor], 'bones', [(k, round(v, 2)) for k, v in top])
