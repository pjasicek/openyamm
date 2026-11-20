"""Small isolated capability check; this is not goblin model generation."""
import bpy
import json
from pathlib import Path

out = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/preflight')
original = bpy.context.window.scene
assert bpy.data.scenes.get('Goblin permission preflight') is None
bpy.ops.scene.new(type='FULL_COPY')
scene = bpy.context.window.scene
scene.name = 'Goblin permission preflight'
try:
    mesh = next(o for o in scene.objects if o.type == 'MESH')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.armature_add()
    rig = bpy.context.object
    rig.name = 'Preflight rig'
    group = mesh.vertex_groups.new(name=rig.data.bones[0].name)
    group.add(list(range(len(mesh.data.vertices))), 1.0, 'REPLACE')
    modifier = mesh.modifiers.new('Preflight skin', 'ARMATURE')
    modifier.object = rig
    bone = rig.pose.bones[0]
    bone.rotation_mode = 'XYZ'
    for frame, angle in [(1, 0.0), (5, 0.2), (10, 0.0)]:
        bone.rotation_euler.z = angle
        bone.keyframe_insert(data_path='rotation_euler', frame=frame)
    rig.animation_data.action.name = 'Preflight bend'
    mesh.shape_key_add(name='Basis')
    shape = mesh.shape_key_add(name='Preflight corrective')
    shape.data[0].co.z += 0.1
    for frame, value in [(1, 0.0), (5, 1.0), (10, 0.0)]:
        shape.value = value
        shape.keyframe_insert(data_path='value', frame=frame)
    material = bpy.data.materials.new('Preflight material')
    material.use_nodes = True
    image = bpy.data.images.new('Preflight packed texture', width=8, height=8)
    image.generated_color = (0.15, 0.35, 0.1, 1)
    image.pack()
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    material.node_tree.links.new(node.outputs['Color'],
        material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    mesh.data.materials.clear()
    mesh.data.materials.append(material)
    scene.frame_end = 10
    scene.frame_set(5)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 4
    scene.render.resolution_x = 128
    scene.render.resolution_y = 128
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = str(out / 'render.png')
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(out / 'rig_export.glb'),
        export_format='GLB', use_selection=True, use_active_scene=True, export_animations=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'checkpoint.blend'), copy=True)
    report = {'blender': bpy.app.version_string, 'scene_edits': 'PASS', 'rig_and_animation': 'PASS',
        'shape_keys': 'PASS', 'packed_texture': 'PASS', 'cycles_render': 'PASS',
        'glb_export': 'PASS', 'blend_save_copy': 'PASS'}
    (out / 'blender_results.json').write_text(json.dumps(report, indent=2) + '\n')
    def timer_check():
        (out / 'timer_check.txt').write_text('Blender timer executed and wrote progress successfully.\n')
        return None
    bpy.app.timers.register(timer_check, first_interval=0.1)
    print(json.dumps(report))
finally:
    bpy.context.window.scene = original
