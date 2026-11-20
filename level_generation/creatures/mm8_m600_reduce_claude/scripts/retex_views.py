"""Retexture check, part 3: textured close-ups of a GLB with each tier bake (mm8_m600_claude/work/tier_nightmare_<t>_
Nightmare.png, the engine ramp rule) as base colour: mouths open at the Attack gape, eyes, lumps, base from below and
the stalk/body junctions. Usage: [RETEX_TIER=<png pattern with {t}>] [RETEX_SPOTS=a,b] blender -b -P retex_views.py -- <glb> <label>  -> review/retex/<label>_<tier>_<spot>.png"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects['Nightmare']
img_node = next(n for m in body.data.materials for n in m.node_tree.nodes
                if n.type == 'TEX_IMAGE' and n.outputs['Color'].links
                and n.outputs['Color'].links[0].to_socket.name == 'Base Color')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 20
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.36, .36, .4, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 420
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
SPOTS = {'mouthL': ('Attack', 12, 'NeckL_Tip', .3, (.4, -1, .25)), 'mouthR': ('Attack', 12, 'NeckR_Tip', .3, (-.4, -1, .25)),
         'mouthF': ('Attack', 12, 'JawFront', .3, (.3, -1, .3)), 'eye_close': ('Standing', 0, 'Eye0_Tip', .16, (.2, -1, .2)),
         'embedded': ('Standing', 0, 'EmbeddedEye0', .2, (.2, -1, .1)), 'front': ('Standing', 0, 'Core', .9, (0, -1, .2)),
         'side': ('Standing', 0, 'Core', .9, (1, 0, .15)), 'back': ('Standing', 0, 'Core', .9, (.3, 1, .3)),
         'below': ('Standing', 0, 'Core', .9, (.2, -.3, -1)), 'junctionL': ('Standing', 0, 'NeckL_01', .35, (.8, -.6, .3)),
         'junctionR': ('Standing', 0, 'NeckR_01', .35, (-.8, -.6, .3))}
if os.environ.get('RETEX_SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['RETEX_SPOTS'].split(',')}
out = os.path.join(HERE, 'review', 'retex'); os.makedirs(out, exist_ok=True)
for t in 'abc':
    pattern = os.environ.get('RETEX_TIER', os.path.join(HERE, '..', 'mm8_m600_claude', 'work', 'tier_nightmare_{t}_Nightmare.png'))
    img_node.image = bpy.data.images.load(pattern.format(t=t))
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        c = bone(b); cam.location = c + Vector(d).normalized() * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(out, f'{label}_{t}_{spot}.png'); bpy.ops.render.render(write_still=True)
print('RETEX views', label)
