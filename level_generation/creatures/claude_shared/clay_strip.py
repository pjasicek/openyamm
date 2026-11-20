"""Clay frame strips of chosen clips of a GLB: one row per clip and view, N evenly spaced times per row, a floor line
at model y = 0 (Blender z = 0), grey Workbench clay with cavity. For reading new or script clips without the viewer.

    blender --background --factory-startup --python clay_strip.py -- <glb> <out.png> <Clip1,Clip2,...> [N] [views]

views: comma list of front, side, q34, back, rside (default front,side). Env SIZE (tile pixels, default 300), ORTHO
(camera width in model units, default: fitted to the clip's whole motion), FOCUS (a bone to centre on). Tiles are rendered by Blender, then pasted
into <out.png> by this same file run with the system python (`python3 clay_strip.py --montage <out.png>`), which the
Blender run calls at the end."""
import json
import math
import os
import subprocess
import sys


def montage(out):
    from PIL import Image, ImageDraw
    spec = json.load(open(out + '.json'))
    size = spec['size']
    label = 150
    rows = spec['rows']
    n = max(len(r['tiles']) for r in rows)
    sheet = Image.new('RGB', (label + n * size, len(rows) * size), (30, 32, 36))
    draw = ImageDraw.Draw(sheet)
    for y, row in enumerate(rows):
        draw.text((6, y * size + 6), f"{row['clip']}\n{row['view']}\n{row['seconds']:.2f} s", fill=(230, 230, 230))
        for x, (path, t) in enumerate(row['tiles']):
            tile = Image.open(path).convert('RGB')
            sheet.paste(tile, (label + x * size, y * size))
            draw.text((label + x * size + 4, y * size + 4), f'{t:.2f}', fill=(255, 230, 120))
            os.remove(path)
    sheet.save(out)
    os.remove(out + '.json')
    print('STRIP', out, sheet.size)


def render(argv):
    import bpy
    import numpy as np
    from mathutils import Vector
    glb, out, clips = argv[0], argv[1], argv[2].split(',')
    count = int(argv[3]) if len(argv) > 3 else 7
    views = (argv[4] if len(argv) > 4 else 'front,side').split(',')
    size = int(os.environ.get('SIZE', 300))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    for obj in list(bpy.data.objects):     # LOD1-3 and shadow proxies would double the silhouette
        if obj.type == 'MESH' and any(k in obj.name.upper() for k in ('LOD1', 'LOD2', 'LOD3', 'SHADOW')):
            bpy.data.objects.remove(obj)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'SINGLE'
    shading.single_color = (.72, .7, .62)
    shading.show_cavity = True
    shading.background_type = 'WORLD'
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.world = bpy.data.worlds.new('W')
    scene.world.color = (0.2, 0.22, 0.26)
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.scale = (300, 300, 1)
    floor.location.z = -0.0005
    mat = bpy.data.materials.new('floor')
    mat.diffuse_color = (0.28, 0.33, 0.42, 1)
    floor.data.materials.append(mat)
    shading.color_type = 'MATERIAL'
    for o in meshes:
        for slot in o.material_slots:
            if slot.material:
                slot.material.diffuse_color = (.72, .7, .62, 1)
    camera_data = bpy.data.cameras.new('C')
    camera = bpy.data.objects.new('C', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    camera_data.clip_end = 60
    fps = scene.render.fps / scene.render.fps_base
    rows = []
    for clip in clips:
        action = bpy.data.actions.get(clip) or next(a for a in bpy.data.actions if a.name.split('_')[0] == clip)
        rig.animation_data_create()
        rig.animation_data.action = action
        if getattr(action, 'slots', None) is not None and len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
        seconds = (end - start) / fps
        times = [seconds * i / max(1, count - 1) for i in range(count)]
        pts = []
        for t in times:
            frame = start + t * fps
            scene.frame_set(int(frame), subframe=frame % 1.0)
            bpy.context.view_layer.update()
            pts.append(np.array([tuple(rig.matrix_world @ b.head) for b in rig.pose.bones]))
        allp = np.concatenate(pts)
        lo, hi = allp.min(0), allp.max(0)
        centre = (lo + hi) / 2
        centre[2] = max(centre[2], (hi[2] + 0.0) / 2)
        focus = os.environ.get('FOCUS')         # a bone name: centre on it (close-ups with a small ORTHO)
        if focus:
            index = [b.name for b in rig.pose.bones].index(focus)
            centre = np.mean([p[index] for p in pts], axis=0)
        extent = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - min(lo[2], 0.0)) + 0.6
        camera_data.ortho_scale = float(os.environ.get('ORTHO', extent))
        for view in views:
            angle = math.radians({'front': 0, 'side': 90, 'q34': -38, 'back': 180, 'rside': -90}[view])
            tiles = []
            for t in times:
                frame = start + t * fps
                scene.frame_set(int(frame), subframe=frame % 1.0)
                target = Vector(centre)
                camera.location = target + Vector((math.sin(angle) * 12, -math.cos(angle) * 12, 0.25))
                camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
                path = f'{out}.{len(rows)}_{len(tiles)}.png'
                scene.render.filepath = path
                bpy.ops.render.render(write_still=True)
                tiles.append((path, t))
            rows.append({'clip': clip, 'view': view, 'seconds': seconds, 'tiles': tiles})
    json.dump({'size': size, 'rows': rows}, open(out + '.json', 'w'))
    subprocess.run(['python3', os.path.abspath(__file__), '--montage', out], check=True)


if __name__ == '__main__':
    if '--montage' in sys.argv:
        montage(sys.argv[sys.argv.index('--montage') + 1])
    else:
        render(sys.argv[sys.argv.index('--') + 1:])
