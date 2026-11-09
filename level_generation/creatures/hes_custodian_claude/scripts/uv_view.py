"""Review of work/uv.blend: shaded clay views (front three-quarter, left, back) and the UV layout with per-face area
distortion (texel density relative to the median: blue under, red over). Args: -- <out prefix>"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
prefix = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=cc.path('work/uv.blend'))
obj = bpy.data.objects['Custodian']
me = obj.data
uv = me.uv_layers.active.data
ratios = []
for p in me.polygons:
    a3 = p.area
    pts = [uv[li].uv for li in p.loop_indices]
    a2 = 0.0
    for i in range(1, len(pts) - 1):
        a2 += abs((pts[i] - pts[0]).cross(pts[i + 1] - pts[0])) / 2
    ratios.append(a2 / a3 if a3 > 1e-9 else 0)
r = np.array(ratios); med = np.median(r[r > 0])
print('UV density: median', med, 'p5/p95 rel', np.percentile(r / med, 5).round(2), np.percentile(r / med, 95).round(2),
      'used area', sum(r * np.array([p.area for p in me.polygons])))
polys = [[tuple(uv[li].uv) for li in p.loop_indices] for p in me.polygons]
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
np.save(cc.path(prefix + '_uvpolys.npy'), np.array([(i, j, x, y) for i, pl in enumerate(polys) for j, (x, y) in enumerate(pl)]))
np.save(cc.path(prefix + '_uvratio.npy'), np.c_[r / med, part])
area3 = np.array([p.area for p in me.polygons])
print('DEGENERATE_3D faces', int((area3 < 1e-9).sum()), 'ZERO_UV faces (non-degenerate)', int(((r < 1e-6) & (area3 >= 1e-9)).sum()), 'of', len(r))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 800, 800
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 4.2
centre = Vector((0, -0.3, 1.65))
for k, az in (('34', -35), ('left', 90), ('back', 180)):
    a = math.radians(az); dvec = Vector((math.sin(a), -math.cos(a), 0.15)).normalized()
    cam.location = centre + dvec * 8; cam.rotation_euler = (-dvec).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = cc.path(f'{prefix}_{k}.png'); bpy.ops.render.render(write_still=True)
