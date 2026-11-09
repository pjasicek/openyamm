"""Author all requested native clips in the isolated MCP scene and save a checkpoint."""
import bpy
import importlib.util
import json
from pathlib import Path

stage = Path(__file__).resolve().parent
def load(name):
    spec = importlib.util.spec_from_file_location('demon_native_' + name, stage / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
motion = load('motion')
scene, rig, mesh = motion.objects()
def finalize():
    load('effects').build()
    motion.activate('Walk_Native', 15)
    from mathutils import Vector
    scene.camera.location = (0, -6, 1.1)
    scene.camera.rotation_euler = (Vector((0, 0, .90))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera.data.ortho_scale = 2.8
    bpy.data.libraries.write(str(stage / 'authored_checkpoint.blend'), {scene}, path_remap='RELATIVE')
    (stage / 'authoring_controls.json').write_text(json.dumps(dict(
        clips=motion.ENDS, controls=motion.CONTROLS,
        walk_review='Native hands change claw silhouettes; small head tilts are visible. Exact yaw is inferred.',
        tail_local_x_bends_degrees=[50, -45, -25, -25, 10],
        tail_root='Bone_020 unchanged locally; distributed curved tail with 2-degree distal lag in Walk',
        support='Fixed-length leg solve; whole-foot pitch from native strides, rigid talons, 6 mm sole target',
        baseline='../attack_animation_v3/mm6_demon_attack.blend'), indent=2)+'\n')
    print('Saved complete isolated animation checkpoint.', flush=True)

if __name__ == '__main__':
    for clip in motion.ENDS:
        motion.bake_action(clip)
    finalize()
