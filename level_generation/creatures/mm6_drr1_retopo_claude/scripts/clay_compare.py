"""Untextured comparison of the a14 remesh and the final geometry (remodelled spikes, new teeth): spines, head,
tail, mouth, chest and back-right leg views -> review/final_geometry/<view>_{a14,final}.png"""
import os, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'spines': ((0.35, 0.05, 0.42), (0, 0.05, 0.25)), 'head': ((0.28, -0.70, 0.40), (0, -0.42, 0.33)),
         'tail': ((0.35, 0.55, 0.25), (0, 0.42, 0.08)), 'mouth': ((0.02, -0.62, 0.31), (0, -0.46, 0.30)),
         'chest': ((0.0, -0.62, 0.12), (0, -0.33, 0.16)), 'leg_br': ((-0.45, 0.05, 0.12), (0, -0.05, 0.10)),
         'three_quarter': ((1.1, -1.25, 0.45), (0, -0.05, 0.18))}
for label, blend, obj in (('a14', 'retopo_a14.blend', 'Wyrm_a14'), ('final', 'final_geometry.blend', 'Wyrm')):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
    scene = bpy.context.scene
    target = bpy.data.objects[obj]
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o is not target
    rig = bpy.data.objects['Wyrm_Rig']
    rig.animation_data.action = bpy.data.actions['Attack']; scene.frame_set(13)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.show_cavity = True
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = 50
    scene.render.resolution_x, scene.render.resolution_y = 640, 480
    for name, (loc, tgt) in VIEWS.items():
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(HERE, 'review', 'final_geometry', f'{name}_{label}.png')
        bpy.ops.render.render(write_still=True)
