"""Clean the selected Meshy hound, measure its leg slices and save a metric rigging input."""
import bpy
import bmesh
import json
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT / 'work/mesh_v1.blend'))
mesh = bpy.data.objects['Hound']
bm = bmesh.new()
bm.from_mesh(mesh.data)
# The return has long stray faces between its chin and paws; normal body edges are much shorter.
bad = [f for f in bm.faces if max(e.calc_length() for e in f.edges) > .10]
removed = len(bad)
print('Stray faces', removed, flush=True)
assert 0 < removed < 100, 'Reinspect changed geometry before applying this revision-specific repair'
cut_vertices = {v for f in bad for v in f.verts}
bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
boundary = [e for e in bm.edges if e.is_boundary and any(v in cut_vertices for v in e.verts)]
if boundary:
    bmesh.ops.holes_fill(bm, edges=boundary, sides=12)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh.data)
bm.free()
co = np.array([v.co[:] for v in mesh.data.vertices])
# Tier A's shoulder is 0.95 m; the concept fixes the ratios, not an inherited native sprite scale.
shoulder = co[(abs(co[:, 1] + .20) < .055) & (abs(co[:, 0]) < .055)]
assert len(shoulder) > 10
ground = co[:, 2].min()
height = np.percentile(shoulder[:, 2], 98) - ground
factor = .95 / height
center_x = (np.percentile(co[:, 0], 1) + np.percentile(co[:, 0], 99)) / 2
for v in mesh.data.vertices:
    v.co = (v.co - Vector((center_x, 0, ground))) * factor
# Trim the short ends of those same bridges, below the chin and inside the front paw gap.
bm = bmesh.new()
bm.from_mesh(mesh.data)
ends = [v for v in bm.verts if (v.co.y < -1.05 and v.co.z < .65) or
        (v.co.y < -.70 and v.co.z < .12 and abs(v.co.x) < .18)]
print('Bridge end vertices', len(ends), flush=True)
assert len(ends) < 80
bmesh.ops.delete(bm, geom=ends, context='VERTS')
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary and
    ((e.verts[0].co.y < -1.05 and e.verts[0].co.z < .72) or e.verts[0].co.z < .13)], sides=12)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh.data)
bm.free()
co = np.array([v.co[:] for v in mesh.data.vertices])
for f in mesh.data.polygons:
    f.use_smooth = True
mesh.data.materials.clear()
mesh.data.calc_loop_triangles()
np.save(PROJECT / 'work/body_vertices.npy', co)
report = {'removed_stray_faces': removed, 'scale_to_meters': factor,
          'bounds': [co.min(0).tolist(), co.max(0).tolist()],
          'triangles': len(mesh.data.loop_triangles), 'leg_slices': {}}
for side, sign in [('L', 1), ('R', -1)]:
    for kind, y0, y1 in [('Front', -.37 * factor, -.08 * factor), ('Hind', .04 * factor, .35 * factor)]:
        rows = []
        for z in np.arange(.025, .85, .05):
            slab = co[(co[:, 0] * sign > .08 * factor) & (co[:, 1] > y0) &
                      (co[:, 1] < y1) & (abs(co[:, 2] - z) < .025)]
            if len(slab) > 3:
                rows.append({'z': round(float(z), 3), 'median': np.median(slab, 0).round(4).tolist(),
                             'width': np.ptp(slab, 0).round(4).tolist()})
        report['leg_slices'][kind + '_' + side] = rows
(PROJECT / 'work/body_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'work/body.blend'))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.62, .63, .65)
sc.render.resolution_x = 1200
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
center = Vector((co.min(0) + co.max(0)) / 2)
extent = float(np.max(np.ptp(co, axis=0)))
cam = bpy.data.objects.new('ReviewCamera', bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = extent * 1.5
for name, direction in [('side', (1, 0, 0)), ('front', (0, -1, 0)),
                        ('top', (0, 0, 1)), ('quarter', (1, -1, .5))]:
    cam.location = center + Vector(direction).normalized() * extent * 3
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(PROJECT / f'review/body_{name}.png')
    bpy.ops.render.render(write_still=True)
print(json.dumps(report), flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
