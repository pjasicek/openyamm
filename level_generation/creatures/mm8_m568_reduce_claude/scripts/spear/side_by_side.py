"""Installed and new viewer GLBs (body + attached polearm) side by side at key poses, three-quarter and front views,
Eevee: review/spear/side_by_side.png. Usage: blender -b -P side_by_side.py"""
import bpy
from mathutils import Vector
from pathlib import Path
P = Path(__file__).resolve().parents[2]; out = P / 'review/spear'; out.mkdir(parents=True, exist_ok=True)
POSES = [('Standing', 0), ('Walk', .25), ('Attack', .3), ('Attack', .62), ('Attack', 1.0), ('Cast', 1.0), ('Hit', .25), ('Fidget', .31), ('Death', .5), ('Dead', 0)]
VIEWS = [('quarter', (4.2, -4.2, 1.6)), ('front', (0, -6, .8))]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; rigs = {}
for label, f, dx in (('installed', 'mm8_m568_a_r100.glb', -1.3), ('new', 'mm8_m568_a_spear.glb', 1.3)):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(P / 'review/viewer' / f))
    new = [o for o in bpy.data.objects if o not in before]; rig = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.parent is None:
            o.location.x += dx
    rigs[label] = (rig, {a.name.split('_')[0] if False else a.name: a for a in bpy.data.actions if a.name not in [x for r in rigs.values() for x in r[1]]})
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = 560; sc.render.resolution_y = 360; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .36, .39, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sun.rotation_euler = (0.8, 0, -0.6); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 6.2
files = []
for clip, t in POSES:
    for label, (rig, acts) in rigs.items():
        a = next(x for n, x in acts.items() if n.startswith(clip) and (n == clip or n.split('_')[0] == clip or n.startswith(clip + '.')) )
        rig.animation_data.action = a
        if a.slots:
            rig.animation_data.action_slot = a.slots[0]
    sc.frame_set(round(t * 24) + int(a.frame_range[0]))
    for v, d in VIEWS:
        target = Vector((0, -.2, 1.2)); cam.location = target + Vector(d); cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fp = out / f'sbs_{clip}_{int(t * 1000):04d}_{v}.png'; sc.render.filepath = str(fp); bpy.ops.render.render(write_still=True); files.append(fp)
print('SBS', len(files))
