"""Blender (headless) renders of the MM6 peasant walking in place for the Water Walk indicator.

blender -b --python render_man.py -- <glb> <basecolor.png> <jobs.txt> <size>
jobs.txt: one "yaw_degrees walk_phase(0..1) output.png" per line. Orthographic camera at 23 degrees elevation (the
original disc's height/width ratio), sun from the front left, transparent film.
"""
import math
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
glb, basecolor, jobs_path, size = args[0], args[1], args[2], int(args[3])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for obj in bpy.data.objects:
    if obj.type == "MESH" and obj.name != "Peasant":
        obj.hide_render = True
peasant = bpy.data.objects["Peasant"]
rig = bpy.data.objects["Rig"]
material = peasant.material_slots[0].material
for node in material.node_tree.nodes:
    if node.type == "TEX_IMAGE" and node.image and "basecolor" in node.image.name:
        node.image = bpy.data.images.load(basecolor)
action = bpy.data.actions["Walking"]
rig.animation_data.action = action
start, end = action.frame_range
rig.rotation_mode = "XYZ"

scene = bpy.context.scene
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
scene.render.film_transparent = True
scene.render.resolution_x = size
scene.render.resolution_y = size
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"

camera_data = bpy.data.cameras.new("cam")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 2.4
camera = bpy.data.objects.new("cam", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
elevation = math.radians(23)
distance = 10
camera.location = (0, -distance * math.cos(elevation), 0.85 + distance * math.sin(elevation))
camera.rotation_euler = (math.pi / 2 - elevation, 0, 0)

sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = 3.2
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(-40))
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.55

for line in open(jobs_path):
    if not line.strip():
        continue
    yaw, phase, out = line.split()
    rig.rotation_euler[2] = math.radians(float(yaw))
    frame = start + (end - start) * (float(phase) % 1.0)
    scene.frame_set(int(math.floor(frame)), subframe=frame - math.floor(frame))
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
