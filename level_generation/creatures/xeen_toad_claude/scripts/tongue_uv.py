"""D-126 tongue UV layout (the tongue of rig_toad.py: 24 rings of 10 vertices from the root at y -0.72 to the bulb,
then one tip vertex at y -1.50; a 10-gon closes the root).

The old cylinder unwrap (uv_toad.py, u = atan2 around a fixed axis height, v along) collapsed the tip's end cap, the
part the player sees head-on, into one texel row with a single u at the tip, and wrapped one face per ring backwards
across the whole texture at the u seam. This layout (Blender UV, v up; the texture is 512 x 1024):
  - the tube, rings 0..CAP_RING (root to the widest ring of the bulb): u = segment / 10 with the seam column at u 1.0,
    v from 0 to TUBE_TOP by arc length along the tongue;
  - the end cap, rings CAP_RING..tip: an azimuthal equidistant map around the tip (UV distance from CAP_CENTRE = the
    surface distance from the tip along the ring column, direction = the vertex's direction around the axis), at
    CAP_SCALE UV units per metre on both axes, so the cap's texels cover what is seen head-on at an even density;
  - the root 10-gon (inside the mouth): a small planar disc at ROOT_CENTRE.
Usage as a module: unwrap(tongue_object) (uv_toad.py, export_glb.py). As a Blender script: rewrites the tongue UVs
in the given blends under work/ and saves them, then dumps work/tongue_uv3d.npz for scripts/paint_tongue.py
(per triangle: the three loops' UVs and rest positions). Args: -- <blend> [<blend> ...]"""
import math
import os
import sys

import bpy
import numpy as np

TEX_W, TEX_H = 512, 1024
TUBE_TOP = 0.75
CAP_RING = 21                       # the widest ring (radius 0.1625 before the 1.25 / 0.7 ellipse)
CAP_CENTRE = (0.5, 0.88)
CAP_SCALE = 700.0                   # pixels per metre on the cap (both axes)
ROOT_CENTRE = (0.07, 0.95)
ROOT_SCALE = 300.0
SEGS = 10


def _rings(me):
    """Ring index per vertex (by y level, root first) and the tip vertex."""
    ys = np.array([v.co.y for v in me.vertices])
    levels = np.unique(np.round(ys, 4))[::-1]          # root at -0.72 first, the tip (-1.50) last
    ring = np.searchsorted(-levels, -np.round(ys, 4))
    tip = int(np.argmin(ys))
    return ring, tip, len(levels) - 1


def unwrap(tongue):
    me = tongue.data
    co = np.array([v.co[:] for v in me.vertices])
    ring, tip, last = _rings(me)
    assert last == 24 and (ring == last).sum() == 1, ('unexpected tongue topology', last, (ring == last).sum())
    # angle around each ring's own centre -> segment index 0..9
    seg = np.zeros(len(co), int)
    ang = np.zeros(len(co))
    for k in range(last):
        idx = np.where(ring == k)[0]
        c = co[idx].mean(0)
        ang[idx] = np.arctan2(co[idx, 2] - c[2], co[idx, 0] - c[0])
        # rig_toad.py builds ring vertex j at 36 j degrees on the 1.25 x 0.7 ellipse: undo the ellipse and round
        # (a sort by angle put float noise at 0 degrees last on some rings and twisted those rings by one segment)
        circ = np.arctan2((co[idx, 2] - c[2]) / 0.7, (co[idx, 0] - c[0]) / 1.25)
        seg[idx] = np.round(circ / (2 * np.pi / SEGS)).astype(int) % SEGS
        assert len(set(seg[idx])) == len(idx) == SEGS, ('ring', k, sorted(seg[idx]))
    # tube v: mean arc length of the ring columns from the root
    centre = np.array([co[ring == k].mean(0) for k in range(last + 1)])
    step = np.linalg.norm(np.diff(centre[:CAP_RING + 1], axis=0), axis=1)
    s_tube = np.concatenate([[0.0], np.cumsum(step)])
    # cap: surface distance from the tip along each column
    s_cap = np.zeros(len(co))
    for k in range(last - 1, CAP_RING - 1, -1):
        for i in np.where(ring == k)[0]:
            if k == last - 1:
                s_cap[i] = np.linalg.norm(co[i] - co[tip])
            else:
                j = np.where((ring == k + 1) & (seg == seg[i]))[0][0]
                s_cap[i] = s_cap[j] + np.linalg.norm(co[i] - co[j])
    layer = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name='UVMap')
    root_c = centre[0]
    for p in me.polygons:
        vs = list(p.vertices)
        rk = [ring[v] for v in vs]
        is_root = len(vs) > 4
        is_cap = min(rk) >= CAP_RING
        wrap = not is_root and not is_cap and max(seg[v] for v in vs) == SEGS - 1 and min(seg[v] for v in vs) == 0
        for li, v in zip(p.loop_indices, vs):
            if is_root:
                d = (co[v] - root_c) * ROOT_SCALE
                uv = (ROOT_CENTRE[0] + d[0] / TEX_W, ROOT_CENTRE[1] + d[2] / TEX_H)
            elif is_cap:
                if v == tip:
                    uv = CAP_CENTRE
                else:
                    r = s_cap[v] * CAP_SCALE
                    uv = (CAP_CENTRE[0] + r * math.cos(ang[v]) / TEX_W, CAP_CENTRE[1] + r * math.sin(ang[v]) / TEX_H)
            else:
                j = seg[v] if not (wrap and seg[v] == 0) else SEGS
                uv = (j / SEGS, TUBE_TOP * s_tube[rk[vs.index(v)]] / s_tube[CAP_RING])
            layer.data[li].uv = uv
    return {'tip': tip, 'tube_length_m': float(s_tube[CAP_RING]), 'cap_radius_m': float(s_cap.max())}


def dump(tongue, path):
    me = tongue.data
    uv = me.uv_layers[0].data
    tri_uv, tri_xyz = [], []
    for p in me.polygons:
        li = list(p.loop_indices)
        for a in range(1, len(li) - 1):
            t = (li[0], li[a], li[a + 1])
            tri_uv.append([uv[i].uv[:] for i in t])
            tri_xyz.append([me.vertices[me.loops[i].vertex_index].co[:] for i in t])
    tip = me.vertices[int(np.argmin([v.co.y for v in me.vertices]))].co[:]
    np.savez(path, uv=np.array(tri_uv), xyz=np.array(tri_xyz), tip=np.array(tip))


if __name__ == '__main__':
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name in args:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', name))
        info = unwrap(bpy.data.objects['Tongue'])
        print('TONGUE_UV', name, info)
        dump(bpy.data.objects['Tongue'], os.path.join(HERE, 'work', 'tongue_uv3d.npz'))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', name))
    print('DONE', args)
