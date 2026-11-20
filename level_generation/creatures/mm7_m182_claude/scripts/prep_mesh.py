"""Clean and align the Meshy return: drop loose shards (< 12 vertices, off the head), turn the trunk axis onto -Y,
centre the trunk on x = 0 and ground it (min z = 0). Writes work/static_v2.blend and work/rest_co_v2.npy."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/static_v1.blend'))
o = bpy.data.objects['Body']
for obj in list(bpy.data.objects):
    if obj.type == 'CAMERA':
        bpy.data.objects.remove(obj, do_unlink=True)
parts = json.loads((P / 'work/components.json').read_text())
head_box = (np.array([-.12, -.37, .38]), np.array([0., -.29, .49]))
drop = [p['part'] for p in parts if p['verts'] < 12 and not (np.all(np.array(p['min']) > head_box[0]) and np.all(np.array(p['max']) < head_box[1]))]
bm = bmesh.new(); bm.from_mesh(o.data); layer = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[layer] in drop], context='VERTS'); bm.to_mesh(o.data); bm.free()
co = np.array([v.co[:] for v in o.data.vertices]); x, y, z = co.T
m = (z > .10) & (z < .28) & (y > -.30) & (y < 0.) & (np.abs(x + .05) < .12)
pts = co[m][:, :2]; centre = pts.mean(0); axis = np.linalg.svd(pts - centre)[2][0]
if axis[1] > 0: axis = -axis
angle = math.atan2(axis[0], -axis[1])  # rotate so the trunk axis points to -Y
R = Matrix.Rotation(angle, 4, 'Z')
o.data.transform(Matrix.Translation((-centre[0], -centre[1], 0)))
o.data.transform(R)
o.data.transform(Matrix.Translation((0, centre[1], 0)))
co = np.array([v.co[:] for v in o.data.vertices])
o.data.transform(Matrix.Translation((0, 0, -co[:, 2].min())))
co = np.array([v.co[:] for v in o.data.vertices]); np.save(P / 'work/rest_co_v2.npy', co)
report = {'dropped_parts': drop, 'trunk_centre_xy': centre.tolist(), 'yaw_correction_deg': math.degrees(angle),
          'bounds': [co.min(0).tolist(), co.max(0).tolist()], 'vertices': len(co), 'triangles': len(o.data.polygons)}
(P / 'work/prep_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/static_v2.blend')); print('PREP', report)
