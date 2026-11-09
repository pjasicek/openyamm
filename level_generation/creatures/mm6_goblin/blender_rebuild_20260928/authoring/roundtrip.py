"""Compare sampled exported/reimported motion against the editable source in separate scenes."""
import json

import bpy
from mathutils.kdtree import KDTree
from mathutils import Vector

import motion
from mesh_tools import ROOT


def remove_import():
    source = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = source
    old = bpy.data.scenes.get('GB15 Export validation')
    if old is None:
        return
    assert old.get('gb_validation_owner') == str(ROOT), 'Validation scene ownership is not established'
    actions = {strip.action for obj in old.objects if obj.type == 'ARMATURE' and obj.animation_data
               for track in obj.animation_data.nla_tracks for strip in track.strips}
    for obj in list(old.objects):
        if obj.name not in source.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(old)
    for action in actions:
        bpy.data.actions.remove(action)


def import_latest(path=None, receipt=None):
    remove_import()
    scene = bpy.data.scenes.new('GB15 Export validation')
    scene['gb_validation_owner'] = str(ROOT)
    scene.render.fps = 48
    bpy.context.window.scene = scene
    path = path or ROOT / 'delivery/mm6_goblin_rigged.glb'
    scene['gb_validation_glb'] = str(path)
    bpy.ops.import_scene.gltf(filepath=str(path))
    check(receipt=receipt)


def activate_import(name, frame):
    scene = bpy.data.scenes['GB15 Export validation']
    bpy.context.window.scene = scene
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    for track in arm.animation_data.nla_tracks:
        track.mute = True
    strip = arm.animation_data.nla_tracks[name].strips[0]
    arm.animation_data.action = strip.action
    arm.animation_data.action_slot = strip.action_slot
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return arm


def check(receipt=None):
    source = bpy.data.scenes['MM6 Goblin - Authored 15K']
    target = bpy.data.scenes['GB15 Export validation']
    results = []
    for name, duration, spacing, function in motion.CLIPS:
        frames = [1, round(duration * 48 / 2) + 1, round(duration * 48) + 1]
        for frame in frames:
            bpy.context.window.scene = source
            motion.activate(name, frame)
            graph = bpy.context.evaluated_depsgraph_get()
            points = {}
            for objname in ['GB15 Skin body', 'GB15 Curved sword']:
                obj = bpy.data.objects[objname].evaluated_get(graph)
                tree = KDTree(len(obj.data.vertices))
                for i, vertex in enumerate(obj.data.vertices):
                    tree.insert(obj.matrix_world @ vertex.co, i)
                tree.balance()
                points[objname] = tree
            source_arm = bpy.data.objects['GB15 Goblin rig']
            joints = {bone.name: source_arm.matrix_world @ bone.head for bone in source_arm.pose.bones}
            imported = activate_import(name, frame)
            joint_error = max((imported.matrix_world @ imported.pose.bones[key].head - position).length
                              for key, position in joints.items())
            graph = bpy.context.evaluated_depsgraph_get()
            distances = []
            for objname, tree in points.items():
                obj = bpy.data.objects[objname + '.001'].evaluated_get(graph)
                distances.extend(tree.find(obj.matrix_world @ vertex.co)[2] for vertex in obj.data.vertices)
            record = {'clip': name, 'frame': frame, 'maximum_joint_error_m': joint_error,
                      'maximum_surface_error_m': max(distances)}
            results.append(record)
            assert joint_error < .00001 and max(distances) < .00001, record
    report = {'status': 'pass', 'samples': results, 'tolerance_m': .00001,
              'objects_checked': ['Skin body including face/fingers/feet', 'Curved sword'],
              'all_72_joint_positions_checked': True}
    receipt = receipt or ROOT / 'delivery/roundtrip_validation.json'
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    # Give the imported scene the same neutral studio, with its own camera for portable-asset previews.
    if not target.world:
        target.world = source.world
    target.render.engine = source.render.engine
    target.view_settings.view_transform = source.view_settings.view_transform
    target.view_settings.look = source.view_settings.look
    target.view_settings.exposure = source.view_settings.exposure
    for obj in bpy.data.collections['GB15 Studio'].objects:
        if obj.type != 'CAMERA' and obj.name not in target.objects:
            target.collection.objects.link(obj)
    if not target.camera:
        cam = source.camera.copy(); cam.data = source.camera.data.copy()
        target.collection.objects.link(cam); target.camera = cam
    target.render.image_settings.file_format = 'PNG'
    activate_import('standing', 1)
    print('Round trip pass;', len(results), 'samples; max surface error', max(r['maximum_surface_error_m'] for r in results))


if __name__ == '__main__':
    check()
