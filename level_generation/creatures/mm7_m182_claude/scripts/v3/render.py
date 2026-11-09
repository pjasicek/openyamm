"""Orthographic renders of a .blend (or .glb, imported) from a JSON spec.
Usage: blender -b -P render.py -- <blend|glb> <spec.json>
spec: {"out": dir, "engine": "WORKBENCH"|"EEVEE", "color": "TEXTURE"|"SINGLE", "res": [w, h], "variant": null,
       "shots": [{"name", "clip"?, "frame"?, "dir": [x,y,z], "target": [x,y,z], "scale": s, "res"?: [w,h]}]}"""
import bpy, json, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, spec = a[0], json.load(open(a[1]))
if src.endswith('.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
            o.hide_render = True
else:
    bpy.ops.wm.open_mainfile(filepath=src)
for n in spec.get('hide', []):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render = True
sc = bpy.context.scene
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if spec.get('engine', 'WORKBENCH') == 'WORKBENCH':
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = spec.get('color', 'TEXTURE'); sc.display.shading.show_cavity = spec.get('cavity', False)
    sc.display.shading.single_color = (.72, .72, .7)
else:
    sc.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('W') if not sc.world else sc.world; sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (.35, .35, .37, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    sun = bpy.data.objects.new('KeySun', bpy.data.lights.new('KeySun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.0; sun.rotation_euler = (0.7, 0.2, -0.6)
sc.render.film_transparent = spec.get('transparent', False)
cam = bpy.data.objects.new('RCam', bpy.data.cameras.new('RCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 100
os.makedirs(spec['out'], exist_ok=True)
for s in spec['shots']:
    if rig and rig.animation_data is None: rig.animation_data_create()
    if rig:
        if s.get('clip'):
            rig.animation_data.action = bpy.data.actions[s['clip']]
            sl = rig.animation_data.action_slots[0] if hasattr(rig.animation_data, 'action_slots') and len(rig.animation_data.action.slots) else None
            if sl is not None: rig.animation_data.action_slot = rig.animation_data.action.slots[0]
            sc.frame_set(int(s.get('frame', 0)))
        else:
            rig.animation_data.action = None
            for b in rig.pose.bones: b.matrix_basis.identity()
            sc.frame_set(0)
    res = s.get('res', spec.get('res', [1000, 800])); sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    if s.get('track') and rig:
        t = rig.matrix_world @ rig.pose.bones[s['track']].head + Vector(s.get('offset', [0, 0, 0]))
    else:
        t = Vector(s['target'])
    cam.location = t + Vector(s['dir']).normalized() * 20
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = s['scale']
    sc.render.filepath = os.path.join(spec['out'], s['name'] + '.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', len(spec['shots']))
