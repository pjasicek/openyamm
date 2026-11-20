"""Binding scale by front silhouette area (quadruped playbook, flyers): mean alpha area of the native front frames
(tier A frame scale 1 game unit per native px times the frame scale) against the mean front orthographic area of the
model over one clip. Args: <blend> <mesh> <rig> <clip> <native glob relative to repo> <frame scale> <out json>."""
import bpy, json, sys, glob, os
import numpy as np
from mathutils import Vector
from pathlib import Path
P = Path(__file__).resolve().parents[1]; REPO = P.parents[2]
blend, mesh_name, rig_name, clip, native, fscale, out = sys.argv[sys.argv.index('--') + 1:][:7]
bpy.ops.wm.open_mainfile(filepath=str(P / blend))
sc = bpy.context.scene; rig = bpy.data.objects[rig_name]; mesh = bpy.data.objects[mesh_name]
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o is not mesh
rig.animation_data.action = bpy.data.actions[clip]
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
R = 1024; sc.render.resolution_x = sc.render.resolution_y = R; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('ScaleCamera', bpy.data.cameras.new('ScaleCamera')); sc.collection.objects.link(cam); sc.camera = cam
f0, f1 = (int(x) for x in bpy.data.actions[clip].frame_range)
co = []
for f in range(f0, f1):
    sc.frame_set(f); ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    a = np.empty(len(ev.vertices) * 3); ev.vertices.foreach_get('co', a); co.append(a.reshape(-1, 3))
allco = np.concatenate(co); lo, hi = allco.min(0), allco.max(0)
span = float(max(hi[0] - lo[0], hi[2] - lo[2]) * 1.1); center = Vector(((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2))
cam.data.type = 'ORTHO'; cam.data.ortho_scale = span
cam.location = center + Vector((0, -3, 0)); cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
areas = []
tmp = P / 'work/scale_tmp.png'
for f in range(f0, f1, max(1, (f1 - f0) // 8)):
    sc.frame_set(f); sc.render.filepath = str(tmp); bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(str(tmp)); px = np.array(img.pixels[:]).reshape(R, R, 4)
    areas.append(float((px[..., 3] > .5).sum()) * (span / R) ** 2); bpy.data.images.remove(img)
tmp.unlink()
import struct, zlib
def png_alpha_area(path):
    img = bpy.data.images.load(path); w, h = img.size; px = np.array(img.pixels[:]).reshape(h, w, 4)
    n = float((px[..., 3] > .5).sum()); bpy.data.images.remove(img); return n
files = sorted(glob.glob(str(REPO / native)))
native_px = [png_alpha_area(f) for f in files]
fs = float(fscale)
scale = float(np.sqrt(np.mean(native_px) * fs * fs / np.mean(areas)))
res = dict(clip=clip, model_front_area_m2=areas, native_files=[os.path.relpath(f, REPO) for f in files], native_area_px=native_px,
           frame_scale=fs, scale=scale, model_max_z_m=float(hi[2]), model_min_z_m=float(lo[2]),
           max_z_units=float(hi[2] * scale), min_z_units=float(lo[2] * scale), span_x_units=float((hi[0] - lo[0]) * scale))
(P / out).write_text(json.dumps(res, indent=1))
print('SCALE', round(scale, 2), 'max_z_units', round(hi[2] * scale, 1), 'min_z_units', round(lo[2] * scale, 1), 'span', round((hi[0] - lo[0]) * scale, 1))
