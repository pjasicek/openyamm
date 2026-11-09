"""Workbench renders of chosen clip/frame/view poses. Usage: pose_shots.py -- <blend> <outdir> clip:frame:view[:scale] ...
views: front, side, quarter, rear, top, low (quarter from below the belly)."""
import bpy, sys
from pathlib import Path
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = Path(a[1]); out.mkdir(parents=True, exist_ok=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE' if any(n.type == 'TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes) else 'MATERIAL'
sc.display.shading.show_cavity = True; sc.render.resolution_x = 1000; sc.render.resolution_y = 800; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('ShotCam', bpy.data.cameras.new('ShotCam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
dirs = {'front': (0, -1, .08), 'side': (1, -.2, .12), 'quarter': (1, -1, .45), 'rear': (-.8, 1, .4), 'top': (0, -.05, 1), 'low': (.7, -1, -.35)}
for spec in a[2:]:
    parts = spec.split(':'); clip, frame, view = parts[0], int(parts[1]), parts[2]; scale = float(parts[3]) if len(parts) > 3 else 1.45
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(frame)
    target = Vector((0, -.05, .26 if clip != 'Dead' else .12)) if len(parts) < 5 else Vector(tuple(float(v) for v in parts[4].split(',')))
    cam.location = target + Vector(dirs[view]).normalized() * 3; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = scale
    sc.render.filepath = str(out / f'{clip}_{frame:02d}_{view}.png'); bpy.ops.render.render(write_still=True)
