"""Eye caps get the real eyes (user review 1: "eyes are not good - should be eye + pupil, clearly good detail").
The caps (eye_caps.py) showed a painted disc. Now each cap's HeadUV is a planar front projection: the bounding box of
its lid opening (the cap's rim, shared with the face skin) is fitted onto the same eye's opening in the HD head
reference (references_head/00_front.png, measured: her right eye x 511-586 / y 441-466 px, her left 672-750 /
440-465; image left = her right), inside a crop box CROP x the opening; the crop is pasted by compose_dru1.py into a
free square of the head atlas (eye_disc.py). Writes work/eye_map.json. In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPEN = {'R': (511, 441, 586, 466), 'L': (672, 440, 750, 465)}       # reference opening boxes (x0, y0, x1, y1)
ZOOM = 0.85
CROP = (1.35, 1.9)                                                   # crop box = opening x (width, height) factors
sq = json.load(open(os.path.join(HERE, 'work', 'eye_disc.json')))
SIZE = sq['size']; SQ = {'R': sq['squares'][0], 'L': sq['squares'][1]}
N = 1024
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
ec = bm.faces.layers.int['eye_cap']; huv = bm.loops.layers.uv['HeadUV']
caps = [f for f in bm.faces if f[ec]]
cap_verts = {v for f in caps for v in f.verts}
rim = {v for v in cap_verts if any(not f[ec] for f in v.link_faces)}
emap = {}
for side in ('R', 'L'):
    sel = [f for f in caps if (sum(v.co.x for v in f.verts) / len(f.verts) < -0.006) == (side == 'R')]
    rv = [v for v in rim if any(v in f.verts for f in sel)]
    xs = [v.co.x for v in rv]; zs = [v.co.z for v in rv]
    lx0, lx1, lz0, lz1 = min(xs), max(xs), min(zs), max(zs)
    ox0, oy0, ox1, oy1 = OPEN[side]
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    cw, ch = (ox1 - ox0) * CROP[0], (oy1 - oy0) * CROP[1]
    crop = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    # zoom into the reference eye (review 1 follow-up: the full opening put a wide band of sclera round a small iris);
    # the crop stays on the full opening, only the mapped opening shrinks
    ox0, ox1 = cx + (ox0 - cx) * ZOOM, cx + (ox1 - cx) * ZOOM
    oy0, oy1 = cy + (oy0 - cy) * ZOOM, cy + (oy1 - cy) * ZOOM
    X0, Y0 = SQ[side]
    for f in sel:
        for l in f.loops:
            u = ox0 + (l.vert.co.x - lx0) / (lx1 - lx0) * (ox1 - ox0)
            v = oy0 + (lz1 - l.vert.co.z) / (lz1 - lz0) * (oy1 - oy0)
            px = X0 + (u - crop[0]) / cw * SIZE; py = Y0 + (v - crop[1]) / ch * SIZE
            l[huv].uv = (px / N, 1 - py / N)
    emap[side] = {'crop': crop, 'square': [X0, Y0], 'size': SIZE, 'loop_box_m': [lx0, lz0, lx1, lz1]}
    print('EYEUV', side, 'faces', len(sel), 'rim', len(rv), 'loop box cm', round((lx1 - lx0) * 100, 2), round((lz1 - lz0) * 100, 2))
bm.to_mesh(me); bm.free()
json.dump(emap, open(os.path.join(HERE, 'work', 'eye_map.json'), 'w'), indent=1)
bpy.ops.wm.save_mainfile()
