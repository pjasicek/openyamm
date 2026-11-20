"""A GLB as a gate blend for the production gate scripts (mm8_m428_claude/scripts/g4_weights.py, g5_hand_stretch.py):
mesh node M428 -> 'Body', armature -> 'Rig'. Usage: blender -b -P gate_blend.py -- <glb> <out.blend>"""
import sys, bpy
glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
bpy.data.objects['M428'].name = 'Body'
next(o for o in bpy.data.objects if o.type == 'ARMATURE').name = 'Rig'
bpy.ops.wm.save_as_mainfile(filepath=out)
print('GATEBLEND', glb, '->', out)
