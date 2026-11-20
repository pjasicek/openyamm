"""Lit EEVEE front / three-quarter renders of work/rock_step0.blend with its own glTF material (base colour, normal,
roughness), to tell texture faults from Workbench preview artefacts. Writes review/rock_lit_<view>.png."""
import bpy, sys, math
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rock_step0.blend'))
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
world = bpy.data.worlds.new('w') if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[1].default_value = 0.6
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.collection.objects.link(sun)
common.render_views(str(P / 'review' / 'rock_lit'), 3.2, 11.0, views=('front', 'three_quarter'), resolution=(1000, 1000),
                    distance=25)
