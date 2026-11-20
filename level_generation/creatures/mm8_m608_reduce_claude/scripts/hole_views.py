"""Views of the source's one open loop (28 edges at the left shoulder's back, rest (0.134, 0.077, 0.768) in model
space): blender -b -P hole_views.py -- <label=glb,...>. Magenta background shows through any hole; arms shown and
masked, in Standing 0, Attack 12 and Hit 9. -> review/hole/<label>_<pose>_<arms>_<view>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(HERE, 'review', 'hole'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb)); rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bodies = [o for o in bpy.data.objects if o.type == 'MESH' and 'UpperArm_L' in o.vertex_groups]
    for o in bodies:
        arms = o.vertex_groups.new(name='ArmsAll'); idx = {g.index for g in o.vertex_groups if g.name.startswith(('UpperArm', 'Forearm', 'Hand'))}
        arms.add([v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in idx) > .5], 1.0, 'REPLACE')
        m = o.modifiers.new('NoArms', 'MASK'); m.vertex_group = 'ArmsAll'; m.invert_vertex_group = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .3; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 0, 1, 1)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.display.shading.background_type = 'WORLD'; w.color = (1, 0, 1); sc.display.shading.show_backface_culling = True  # the engine culls back faces
    sc.view_settings.view_transform = 'Standard'
    hole = Vector((0.134, 0.077, 0.768))
    for pose, (act, f) in {'stand': ('Standing', 0), 'attack': ('Attack', 12), 'hit': ('Hit', 9)}.items():
        rig.animation_data.action = bpy.data.actions[act]
        if bpy.data.actions[act].slots: rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
        sc.frame_set(f); pb = rig.pose.bones['Chest']; M = rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
        c = M @ hole
        for arms in ('arms', 'noarms'):
            for o in bodies: o.modifiers['NoArms'].show_render = arms == 'noarms'
            for vn, d in {'back': (0, 1, .2), 'backside': (.8, .6, .3), 'top': (.3, .4, 1)}.items():
                cam.location = c + Vector(d).normalized() * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = os.path.join(out, f'{label}_{pose}_{arms}_{vn}.png'); bpy.ops.render.render(write_still=True)
print('HOLES done')
