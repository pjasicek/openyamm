"""PeasantM2d upper-tunic lining. Gate finding: the holes are not at an opening (PeasantM2's tunic is welded to the head shell at the
neck: no open rim) but where the chest/shoulder cloth folds in Death/Dead and the view meets the tunic's culled back faces with no body
under them; the lining's front faces close those views. Originally planned as a collar lining: (see-through gate on PeasantM2's geometry: through the tunic's neck opening the lying corpse and the
party-height views from behind/above showed the background through the tunic's culled back faces: torso 359 px in Death, the
'sleeve' slivers next to the collar). After finish_pm2.py, geometry added only (paints and UVs stay valid), as PeasantDM2's
rim_lining.py collar band (30 cm: at 12 cm DM2's corpse showed the unlined mid-back): every unlined tunic face (part 1) above
z ZMIN whose centre lies within DEPTH of the neck opening's rim (the open boundary of the tunic faces round the neck) and inside
|x| < XMAX (chest and back, not the sleeves, which finish_pm2.py lines from the cuffs) is copied OFFSET behind itself along the
area-weighted vertex normal, flipped, same weights, on the torso set's dark texel (work/dark_texel.json); lining faces get lining=4.
Args (Blender): <in blend> <out blend> [key=value: depth 0.30, offset 0.003, zmin 0.25, xmax 0.24]"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[:2]; opt = dict(x.split('=', 1) for x in a[2:])
DEPTH = float(opt.get('depth', 0.30)); OFF = float(opt.get('offset', 0.003)); ZMIN = float(opt.get('zmin', 0.25)); XMAX = float(opt.get('xmax', 0.24))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']; lin = bm.faces.layers.int['lining']
uvp = bm.loops.layers.uv['PartUV']
tun = [f for f in bm.faces if f[part] == 1 and not f[lin]]
tset = set(tun)
rim = set()
for f in tun:
    for e in f.edges:
        if sum(1 for g in e.link_faces if g in tset) == 1:
            c = (e.verts[0].co + e.verts[1].co) / 2
            if c.z > 0.50 and abs(c.x) < 0.15:
                rim.update(e.verts)
R = np.array([v.co[:] for v in rim])
print('COLLAR rim verts', len(R), '(none: PeasantM2\'s tunic is welded to the neck shell; the whole upper tunic in the box is lined)')
sel = []
for f in tun:
    c = np.array(f.calc_center_median()[:])
    if c[2] < ZMIN or abs(c[0]) > XMAX: continue
    if len(R) == 0 or np.min(np.linalg.norm(R - c, axis=1)) <= DEPTH: sel.append(f)
vn = {}
for f in sel:
    for v in f.verts: vn.setdefault(v, Vector()); vn[v] += f.normal * f.calc_area()
d = bmesh.ops.duplicate(bm, geom=sel)
vmap = d['vert_map']; newf = [x for x in d['geom'] if isinstance(x, bmesh.types.BMFace)]
for v, n_ in vn.items():
    nv = vmap.get(v)
    if nv is not None and n_.length > 1e-12: nv.co = v.co - n_.normalized() * OFF
bmesh.ops.reverse_faces(bm, faces=newf)
for f in newf:
    f[lin] = 4
    for l in f.loops: l[uvp].uv = (DT['torso']['u'], 1 - DT['torso']['v'])
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('COLLAR lining faces', len(newf), 'of', len(tun), 'tunic faces; total', len(me.polygons))
