"""Import a GLB as is (own normals, no weld) into a blend with the names the production gate scripts expect (Body,
Rig), for ../mm8_m420_claude/scripts/g5_hand_stretch.py. Usage: blender -b -P glb_to_blend.py -- <glb> <out.blend>"""
import os, sys, bpy
glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'PirateMage').name = 'Body'
next(o for o in bpy.data.objects if o.type == 'ARMATURE').name = 'Rig'
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
