"""Review fix (2026-10-13, lost definition): the first body layout gave each arm ~18k texels (installed: ~170k).
Keeps the Meshy body layout as UVMeshy and re-packs the same charts into UVMap without rotation (tangent-space normals
stay valid): arm/hand charts (pieces 4, 5) x2.6 linear, head charts (unused in the body set) x0.15. Idempotent."""
import bpy, bmesh, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM, HEAD = float(os.environ.get('REA_ARM_SCALE', '2.6')), .15
path = os.path.join(HERE, 'work', 'master_r45.blend'); bpy.ops.wm.open_mainfile(filepath=path)
b = bpy.data.objects['Body']; me = b.data
if 'UVMeshy' not in me.uv_layers:
    m = me.uv_layers.new(name='UVMeshy')
    for i, l in enumerate(me.uv_layers['UVMap'].data): m.data[i].uv = l.uv
src = me.uv_layers['UVMeshy'].data; dst = me.uv_layers['UVMap'].data
piece = [a.value for a in me.attributes['piece'].data]; head = [a.value for a in me.attributes['head'].data]
arm = [piece[p.vertices[0]] in (4, 5) for p in me.polygons]
for p in me.polygons:
    s = HEAD if head[p.index] else 1.0
    for li in p.loop_indices: dst[li].uv = src[li].uv * s
me.uv_layers.active = me.uv_layers['UVMap']
for o in bpy.data.objects: o.select_set(o == b)
bpy.context.view_layer.objects.active = b
k = ARM   # the Meshy arm charts, scaled (a fresh arm unwrap shattered into small folded charts: worse)
for p in me.polygons:
    if arm[p.index]:
        for li in p.loop_indices: dst[li].uv = src[li].uv * k
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=False, scale=True, margin=.004, margin_method='FRACTION', shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=path); print('RELAYOUT arm x', ARM, 'head x', HEAD, 'arm charts rescaled x', round(k, 3))
