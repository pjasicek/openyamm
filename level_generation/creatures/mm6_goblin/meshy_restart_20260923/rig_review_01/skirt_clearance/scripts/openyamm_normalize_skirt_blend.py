import bpy
s=bpy.data.scenes['Goblin - Skirt Clearance v3'];bpy.context.window.scene=s
for other in list(bpy.data.scenes):
 if other!=s:bpy.data.scenes.remove(other)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
