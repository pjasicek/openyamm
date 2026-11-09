"""MM9 side of the comparison sheets: the true-handed MM9 GLB at clip times, quarter view. Args: <glb> <out prefix> <clip:seconds>..."""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
import numpy as np
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Icosphere'): o.hide_render = True
z = np.load('work/axe_bind.npz'); V = z['V']; F = z['F']
me = bpy.data.meshes.new('axe'); me.from_pydata([(x, -zz, y) for x, y, zz in V], [], [tuple(int(i) for i in f) for f in F]); me.update()
ax = bpy.data.objects.new('axe', me); bpy.context.scene.collection.objects.link(ax)
vg = ax.vertex_groups.new(name='RHand1'); vg.add(list(range(len(V))), 1.0, 'REPLACE')
m_ = ax.modifiers.new('a', 'ARMATURE'); m_.object = rig
mt = bpy.data.materials.new('s'); mt.use_nodes = True; me.materials.append(mt)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 420
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.35, 0.36, 0.38); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 1.9; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
d = Vector((-0.75, -1.0, 0.25)).normalized(); cam.location = d * 10 + Vector((0, 0, 0.0)); cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
fps = sc.render.fps
for k, it in enumerate(a[2:]):
    c, t = it.split(':')
    act = bpy.data.actions[c]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f = float(t) * fps
    sc.frame_set(int(f), subframe=f % 1.0)
    sc.render.filepath = f'{a[1]}_{k}.png'; bpy.ops.render.render(write_still=True)
