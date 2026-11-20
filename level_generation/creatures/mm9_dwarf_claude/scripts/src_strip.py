"""MM9 strips: the true-handed source with the pick on RHand1, every clip at N times, two views. Args: <glb> <axe npz> <out dir> <cols> [clips comma]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 300
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.5, 0.52); sh.background_type = 'WORLD'
z = np.load(a[1]); V = z['V']; F = z['F']
me = bpy.data.meshes.new('axe'); me.from_pydata([(x, -zz, y) for x, y, zz in V], [], [tuple(f) for f in F]); me.update()
ax = bpy.data.objects.new('axe', me); sc.collection.objects.link(ax)
vg = ax.vertex_groups.new(name='RHand1'); vg.add(list(range(len(V))), 1.0, 'REPLACE')
m = ax.modifiers.new('a', 'ARMATURE'); m.object = rig
mat = bpy.data.materials.new('r'); mat.diffuse_color = (0.9, 0.1, 0.1, 1); me.materials.append(mat)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 2.0; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(a[2], exist_ok=True)
cols = int(a[3]); only = a[4].split(',') if len(a) > 4 else None
fps = sc.render.fps
rig.animation_data_create()
acts = [x for x in bpy.data.actions]
names = []
for act in acts:
    nm = act.name.split('_')[0] if False else act.name
    if only and nm not in only: continue
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for vn, d in (('q', Vector((-1, -0.9, 0.15))), ('r', Vector((1, -0.9, 0.15)))):
        d = d.normalized(); cam.location = d * 10 + Vector((0, 0, 0.0)); cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        for k in range(cols):
            f = f0 + (f1 - f0) * k / (cols - 1)
            sc.frame_set(int(f), subframe=f % 1.0)
            sc.render.filepath = f'{a[2]}/{nm}_{vn}_{k}.png'; bpy.ops.render.render(write_still=True)
    names.append(nm)
print('NAMES', names)
