"""Render a creature model with held items on their sockets, a few frames of each clip, two views (Blender, headless).

blender -b -P render_held.py -- --model <creature.glb> --item <item.glb>:<Socket_node> [--item ...]
        --clips Standing,Hammer --out <dir> [--frames 3]

Writes <out>/<clip>_<frame>_<view>.png and <out>/sheet.png (rows: clips; columns: frames x views). Reads the GLBs only.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
args = {"item": [], "frames": "3", "clips": ""}
key = None
for token in argv:
    if token.startswith("--"):
        key = token[2:]
        continue
    if key == "item":
        args["item"].append(token)
    else:
        args[key] = token
out = args["out"]
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


creature = import_glb(args["model"])
armature = next(o for o in creature if o.type == "ARMATURE")
actions = {a.name: a for a in bpy.data.actions}

for spec in args["item"]:
    path, socket = spec.rsplit(":", 1)
    socket_obj = next((o for o in creature if o.name == socket), None)
    parent_bone = None
    if socket_obj is None:
        # The importer may keep a socket that is a joint's child as a bone of its own.
        if socket in armature.data.bones:
            parent_bone = socket
        else:
            print("NO SOCKET", socket, sorted(o.name for o in creature)[:50], file=sys.stderr)
            sys.exit(1)
    item_objs = import_glb(path)
    roots = [o for o in item_objs if o.parent is None]
    for root in roots:
        if parent_bone:
            root.parent = armature
            root.parent_type = "BONE"
            root.parent_bone = parent_bone
            # A bone parent attaches at the bone's tail; move it back to the head (the node's own frame).
            root.matrix_parent_inverse.identity()
            root.location = (0.0, -armature.data.bones[parent_bone].length, 0.0)
        else:
            root.parent = socket_obj
            root.matrix_parent_inverse.identity()
        for o in [root] + list(root.children_recursive):
            if o.type == "MESH":
                for slot in o.material_slots:
                    if slot.material:
                        slot.material.diffuse_color = (1.0, 0.15, 0.1, 1.0)

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x = 360
scene.render.resolution_y = 480
scene.render.film_transparent = False
world = bpy.data.worlds.new("w")
scene.world = world

camera_data = bpy.data.cameras.new("cam")
camera_data.type = "ORTHO"
camera = bpy.data.objects.new("cam", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

clips = [c for c in args["clips"].split(",") if c]
frames_per_clip = int(args["frames"])
images = []


def bounds():
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(depsgraph)
        for corner in ev.bound_box:
            p = ev.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return lo, hi


for clip in clips:
    action = actions.get(clip) or next((a for n, a in actions.items() if n.lower().startswith(clip.lower())), None)
    if action is None:
        print("NO CLIP", clip, sorted(actions), file=sys.stderr)
        continue
    armature.animation_data_create()
    armature.animation_data.action = action
    start, end = action.frame_range
    row = []
    for i in range(frames_per_clip):
        frame = start + (end - start) * (i + 0.5) / frames_per_clip
        scene.frame_set(int(frame), subframe=frame - int(frame))
        lo, hi = bounds()
        centre = (lo + hi) / 2
        size = max(hi - lo)
        for view, angle in (("front", 0.0), ("side", 90.0)):
            a = math.radians(angle)
            # glTF +Z forward becomes Blender -Y; look at the model's front and its right side.
            direction = Vector((math.sin(a), -math.cos(a), 0.15)).normalized()
            camera.location = centre + direction * size * 3
            camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera_data.ortho_scale = size * 1.15
            path = os.path.join(out, f"{clip}_{i}_{view}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            row.append(path)
    images.append((clip, row))

with open(os.path.join(out, "rows.txt"), "w") as handle:
    for clip, row in images:
        handle.write(clip + "\t" + "\t".join(row) + "\n")
