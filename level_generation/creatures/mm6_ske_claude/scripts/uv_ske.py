"""UV atlas for the reduced skeleton (before the sword is added).
Body (every piece except the skull set): one Smart UV Project over all body faces (66 degrees, uniform texel
density; each bone piece unwraps into a few large islands). Head (pieces 2000-2003: cranium, mandible, teeth): its own
Smart UV Project filling 0..1 and material slot 'Head' for the separate 1K head set. Reports overlap and density.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
ANGLE = float(os.environ.get('UV_ANGLE', '78'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Skeleton']; me = body.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
pv = np.zeros(len(me.vertices), dtype=np.int32); me.attributes['piece'].data.foreach_get('value', pv)
face_piece = np.array([pv[p.vertices[0]] for p in me.polygons])
is_head = face_piece >= 2000
head_mat = bpy.data.materials.get('Head') or bpy.data.materials.new('Head')
head_mat.diffuse_color = (0.9, 0.85, 0.7, 1)
if 'Head' not in me.materials:
    me.materials.append(head_mat)
hi = list(me.materials).index(me.materials['Head'])
for p, h in zip(me.polygons, is_head):
    p.material_index = hi if h else 0

bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)


def unwrap(mask, margin):
    for p, m in zip(me.polygons, mask):
        p.select = bool(m)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for p, m in zip(me.polygons, mask):
        p.select = bool(m)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(ANGLE), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')


unwrap(~is_head, 0.004)
unwrap(is_head, 0.006)

# report: overlap raster per layout, texel density per piece class
uv = np.zeros(len(me.loops) * 2); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.array([tuple(v.co) for v in me.vertices])
S = 1024
for name, mask in (('body', ~is_head), ('head', is_head)):
    occ = np.zeros((S, S), np.int16)
    dens = {}
    for p, m, pid in zip(me.polygons, mask, face_piece):
        if not m:
            continue
        li = list(p.loop_indices)
        t = uv[li] * S
        area_uv = 0.5 * abs(np.cross(t[1] - t[0], t[2] - t[0])) if len(li) >= 3 else 0
        v = co[list(p.vertices)]
        area_3d = 0.5 * np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0])) if len(li) >= 3 else 0
        if area_3d > 1e-9:
            dens.setdefault(int(pid), []).append((area_uv, area_3d))
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        if x1 - x0 <= 1 or y1 - y0 <= 1:
            continue
    tot_uv = sum(a for l in dens.values() for a, _ in l); tot_3d = sum(b for l in dens.values() for _, b in l)
    print('LAYOUT', name, 'texels per m (1K):', round(math.sqrt(tot_uv / tot_3d), 1),
          'uv fill', round(tot_uv / S / S, 3))
    vals = {pid: math.sqrt(sum(a for a, _ in l) / sum(b for _, b in l)) for pid, l in dens.items()}
    med = float(np.median(list(vals.values())))
    bad = {pid: round(v / med, 2) for pid, v in vals.items() if abs(v / med - 1) > 0.5}
    print('DENSITY', name, 'median', round(med, 1), 'outliers (ratio)', bad)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
