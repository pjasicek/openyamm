"""Pivots on the frozen mesh: joints translated, rest rotations and weights unchanged; each half helper moves with its joint. Args: <in blend> <out blend> <pivots json>"""
import bpy, sys, json
from mathutils import Vector
IN, OUT, JS = sys.argv[sys.argv.index('--') + 1:]
PIV = json.load(open(JS))
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.to_3x3().inverted()
for k, d in PIV.items():
    for nm in ('Bip01 ' + k, 'Bip01 ' + k + '_h'):
        e = eb[nm]; dv = Mi @ Vector(d); e.head += dv; e.tail += dv
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOVED', list(PIV))
