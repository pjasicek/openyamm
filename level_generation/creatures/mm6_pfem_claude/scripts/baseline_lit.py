"""Lit renders of the Meshy-only baseline (remesh 10k + auto-rig walking) with the same cameras as ours."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/baseline_rig_v1/result_basic_animations_walking_glb_url.glb'))
for o in bpy.data.objects:
    if o.name == 'Icosphere': o.hide_render = True
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
lo, hi = common.world_bounds(meshes)
s = 1.578 / (hi.z - lo.z)
arm.scale = tuple(v * s for v in arm.scale); arm.location.z -= lo.z * s
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine; break
    except TypeError:
        pass
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1); bg.inputs[1].default_value = 0.8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.view_settings.view_transform = 'Standard'
a = arm.animation_data.action; f0, f1 = a.frame_range
for i in range(8):
    scene.frame_set(int(f0 + (f1 - f0) * i / 8))
    common.render_views(os.path.join(common.REVIEW, 'tmp', f'base_walk_{i:02d}'), 0.78, 1.75, views=('left', 'front'), resolution=(300, 300))
