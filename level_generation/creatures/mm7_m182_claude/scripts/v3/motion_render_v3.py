"""Renders of clips at the MM7 native frame times and directions, as v2's motion_render.py (same camera: orthographic,
elevation 1.1 deg, view k orbiting the dragon's right side by 45 deg per step, framed on the posed bounding-box
centre), for a v3 blend whose clips are the cdr1 clips. Each shot: silhouette (alpha) + textured workbench image.
Native time -> clip time per scripts/v3/clipmap.py (impact-aligned for Attack, proportional otherwise).
Usage: motion_render_v3.py -- <blend> <outdir> <native px per m> [clips comma list] [size]"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(P / 'scripts/v3'))
from clipmap import SHOTS, FRONT_ONLY, clip_time
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = Path(a[1]); out.mkdir(parents=True, exist_ok=True)
scale = float(a[2]); clips = a[3].split(',') if len(a) > 3 and a[3] else list(SHOTS)
S = int(a[4]) if len(a) > 4 else 576
NOWING = len(a) > 5 and a[5] == 'nowing'   # body-only silhouettes: wing material faces deleted
elev = math.radians(1.1196400942085156)
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene; fps = sc.render.fps
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
if NOWING:
    import bmesh
    wi = [i for i, m in enumerate(body.data.materials) if 'Wing' in m.name]
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in wi], context='FACES'); bm.to_mesh(body.data); bm.free()
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = S; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('MC', bpy.data.cameras.new('MC')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
cam.data.ortho_scale = S / (2 * scale); cam.data.clip_end = 100
index = []
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    for frame, tn in SHOTS[clip]:
        fr = clip_time(clip, tn) * fps
        sc.frame_set(int(fr), subframe=fr % 1)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
        pts = [body.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        target = (lo + hi) / 2
        for view in ([0] if (clip == 'Death' and frame in FRONT_ONLY) else range(5)):
            th = math.radians(45 * view); d = Vector((-math.sin(th) * math.cos(elev), -math.cos(th) * math.cos(elev), math.sin(elev)))
            cam.location = target + d * 20; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            for mode in (('sil',) if NOWING else ('sil', 'tex')):
                sc.display.shading.color_type = 'TEXTURE' if mode == 'tex' else 'SINGLE'
                sc.render.filepath = str(out / f'{clip}_{frame}{view}_{mode}.png'); bpy.ops.render.render(write_still=True)
            index.append({'clip': clip, 'frame': frame, 'view': view, 'clip_frame': fr, 'native_s': tn})
(out / 'index.json').write_text(json.dumps(index, indent=1) + '\n'); print('MOTION_RENDER', len(index))
