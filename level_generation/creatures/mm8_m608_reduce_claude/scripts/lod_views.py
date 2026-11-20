"""Per-LOD renders of the GLBs written by lod_check.py (work/lodcheck_<label>_<node>_<level>.glb): the body in Standing
frame 0 (three-quarter) and the rubble in Dead (three-quarter, from above) -> review/lods/<label>_<node>_<level>.png and
review/lods/sheet.png (rows installed/reduced per node, columns LOD0-3). Usage: blender -b -P lod_views.py -- <label,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(HERE, 'review', 'lods'); os.makedirs(out, exist_ok=True)
labels = sys.argv[sys.argv.index('--') + 1].split(',')
VIEW = {'Juggernaut': ('Standing', (.7, -.8, .35), Vector((0, 0, .5)), 1.15), 'Rubble': ('Dead', (.5, -.7, .9), Vector((0, 0, .1)), 1.1)}
for label in labels:
    for node, (act, d, c, size) in VIEW.items():
        for level in range(4):
            bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
            bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{node}_{level}.glb'))
            rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data.action = bpy.data.actions[act]
            if bpy.data.actions[act].slots: rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
            sc.frame_set(0)
            cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
            cam.data.type = 'ORTHO'; cam.data.ortho_scale = size; cam.location = c + Vector(d).normalized() * 3
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
            sc.render.resolution_x = sc.render.resolution_y = 360; sc.view_settings.view_transform = 'Standard'
            sc.render.filepath = os.path.join(out, f'{label}_{node}_{level}.png'); bpy.ops.render.render(write_still=True)
print('LODVIEWS done')
