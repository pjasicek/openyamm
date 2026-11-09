import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

stage = Path(__file__).resolve().parent if '__file__' in globals() else Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation')
stage.mkdir(exist_ok=True)
source_scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
source_rig = source_scene.objects['Demon_Rig_Review']
source_mesh = source_scene.objects['Demon_Rigged_Review']
scene = bpy.data.scenes.get('MM6_Demon_Attack')
if scene is None:
    scene = bpy.data.scenes.new('MM6_Demon_Attack')
    rig = source_rig.copy()
    rig.data = source_rig.data.copy()
    rig.name = 'Demon_Attack_Rig'
    rig.animation_data_clear()
    mesh = source_mesh.copy()
    mesh.data = source_mesh.data.copy()
    mesh.name = 'Demon_Attack_Mesh'
    mesh.animation_data_clear()
    mesh.parent = rig
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    scene.collection.objects.link(rig)
    scene.collection.objects.link(mesh)
    camera = bpy.data.objects.new('DemonAttackCamera', bpy.data.cameras.new('DemonAttackCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
else:
    rig = scene.objects['Demon_Attack_Rig']
    mesh = scene.objects['Demon_Attack_Mesh']
bpy.context.window.scene = scene
rig.hide_set(False)
mesh.hide_set(False)
rig.hide_render = mesh.hide_render = False
rig.data.pose_position = 'POSE'
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.fps = 48
scene.frame_start = 0
scene.frame_end = 36
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.62, .66, .7)
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.world = bpy.data.worlds.new('DemonAttackWorld') if scene.world is None else scene.world
scene.world.color = (.055, .065, .08)
camera = scene.camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.15
center = Vector((0, -.03, .85))
camera.location = center + Vector((0, -6, .1))
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
vertices = np.array([tuple(vertex.co) for vertex in mesh.data.vertices])
faces = np.array([tuple(face.vertices) for face in mesh.data.polygons])
groups = [group.name for group in mesh.vertex_groups]
weights = np.zeros((len(vertices), len(groups)))
for vertex in mesh.data.vertices:
    for entry in vertex.groups:
        weights[vertex.index, entry.group] = entry.weight
np.savez_compressed(stage / 'source_geometry.npz', vertices=vertices, faces=faces, weights=weights,
                    group_names=np.array(groups), bone_names=np.array([b.name for b in rig.data.bones]),
                    bone_matrices=np.array([np.array(b.matrix_local) for b in rig.data.bones]))
(stage / 'source_scene_audit.json').write_text(json.dumps({
    'source_scene': source_scene.name, 'scene': scene.name,
    'vertices': len(vertices), 'triangles': len(faces), 'bones': len(rig.data.bones),
    'actions_preserved': [a.name for a in bpy.data.actions],
    'source_objects_unchanged': True,
}, indent=2) + '\n')
for item in scene.objects:
    item.select_set(False)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.shading.type = 'SOLID'
print('Initialized isolated attack scene:', scene.name, len(vertices), len(rig.data.bones))
