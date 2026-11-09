"""Weight-only stage after the UVs (topology, UVs and the paint stay valid):
- hooves rigid: below FOOT_TOP above the foot joint every vertex follows its foot bone, blended over FOOT_BLEND above
  (surface diffusion had smeared the ankle into the hoof, so the hoof did not take MM9's foot orientation);
- limb roots fade to the spine bones above the mid thigh/shoulder (rigcfg.LIMB_FADE);
- udder and teats (cow): the udder box follows the pelvis bone, so it no longer swings with either hind leg;
- pieces other than eyes keep being rigid.
Args: <in blend> <out blend> <report json>   Env: FOOT_TOP, FOOT_BLEND, UDDER 'y0,y1,z1,xabs,bone'"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
FOOT_R = float(os.environ.get('FOOT_R', '0.14'))
TOP = float(os.environ.get('FOOT_TOP', '0.03')); BL = float(os.environ.get('FOOT_BLEND', '0.04'))
arm = bpy.data.objects['MM9_Rig']; ob = bpy.data.objects['Body']; me = ob.data
for b in arm.pose.bones:
    b.matrix_basis.identity()
gi = {g.name: g.index for g in ob.vertex_groups}
rep = {}
feet = {'Xffoot': 'fr', 'Xffoot01': 'fl', 'Xbfoot': 'hr', 'Xbfoot01': 'hl'}


def setw(v, table, a):
    """blend vertex v toward {group: weight} by a"""
    cur = {g.group: g.weight for g in v.groups}
    new = {k: w * (1 - a) for k, w in cur.items()}
    for k, w in table.items():
        new[k] = new.get(k, 0.0) + w * a
    tot = sum(new.values())
    for k in cur:
        if k not in new or new[k] <= 0:
            ob.vertex_groups[k].remove([v.index])
    for k, w in sorted(new.items(), key=lambda x: -x[1])[:4]:
        ob.vertex_groups[k].add([v.index], w / tot, 'REPLACE')


# tail: only the tube itself follows the tail bones. MM9's tail lies along the rump, so the nearest-MM9-vertex labels
# gave the rear of the rump to the tail chain, and the gallop's tail flick lifted it as a sheet. The tube: from the
# tail tip along the surface while the cross-section stays thin.
import heapq
tcfg = rigcfg.TAIL_TUBE
tb = [gi[b] for b in tcfg['bones'] if b in gi]
tk = gi[tcfg['core']]
pc = me.attributes['piece']
nb = [[] for _ in me.vertices]
for e in me.edges:
    a, b = e.vertices
    if pc.data[a].value == 0 and pc.data[b].value == 0:
        L = (me.vertices[a].co - me.vertices[b].co).length
        nb[a].append((b, L)); nb[b].append((a, L))
cand = [v for v in me.vertices if pc.data[v.index].value == 0 and eval(tcfg['tip_filter'], {'x': v.co.x, 'y': v.co.y, 'z': v.co.z})]
tip = max(cand, key=lambda v: eval(tcfg['tip_key'], {'x': v.co.x, 'y': v.co.y, 'z': v.co.z})).index
dist = {tip: 0.0}; pq = [(0.0, tip)]
while pq:
    d, i = heapq.heappop(pq)
    if d > dist[i]:
        continue
    for j, L in nb[i]:
        if d + L < dist.get(j, 1e9):
            dist[j] = d + L; heapq.heappush(pq, (d + L, j))
bins = {}
for i, d in dist.items():
    bins.setdefault(int(d / tcfg['bin']), []).append(i)
end = None
seen_thin = False
for k in sorted(bins):
    pts = np.array([tuple(me.vertices[i].co) for i in bins[k]])
    if os.environ.get('TDBG'):
        print('TDBG', k, len(pts), np.ptp(pts, axis=0).round(3).tolist(), pts.mean(0).round(3).tolist())
    wide = np.ptp(pts, axis=0).max() > tcfg['thin']
    seen_thin = seen_thin or not wide
    if wide and seen_thin:      # the tassel's cone below the tube is wide too: start counting on the tube
        end = k * tcfg['bin']; break
root_len = tcfg['root_blend']
moved = 0
for v in me.vertices:
    if pc.data[v.index].value != 0:
        continue
    d = dist.get(v.index, 1e9)
    keep = min(1.0, max(0.0, (end - d) / root_len))          # 1 on the tube, 0 on the body
    keep = keep * keep * (3 - 2 * keep)
    cur = {g.group: g.weight for g in v.groups}
    mv = sum(cur.get(b, 0.0) for b in tb) * (1 - keep)
    if mv <= 1e-4:
        continue
    for b in tb:
        if b in cur:
            ob.vertex_groups[b].add([v.index], cur[b] * keep, 'REPLACE')
    ob.vertex_groups[tk].add([v.index], cur.get(tk, 0.0) + mv, 'REPLACE')
    moved += 1
rep['tail_tube_end'] = end; rep['tail_tip'] = [round(c, 3) for c in me.vertices[tip].co]
rep['tail_moved_to_core'] = moved
# limb roots: MM9 swings the whole leg about a hip/shoulder pivot high in the body (70 deg in the gallop), its rigid
# thigh block juts out. Skin above the mid thigh stays on the spine bone, the swing spreads over the height range.
pcs0 = me.attributes['piece']
for bones_, core, zhi, zlo in rigcfg.LIMB_FADE:
    sub = [gi[b] for b in bones_ if b in gi]
    k = gi[core]
    n = 0
    for v in me.vertices:
        if pcs0.data[v.index].value != 0 or v.co.z < zlo:
            continue
        t = min(1.0, (v.co.z - zlo) / (zhi - zlo)); t = t * t * (3 - 2 * t)
        cur = {g.group: g.weight for g in v.groups}
        mv = sum(cur.get(b, 0.0) for b in sub) * t
        if mv <= 1e-4:
            continue
        for b in sub:
            if b in cur:
                ob.vertex_groups[b].add([v.index], cur[b] * (1 - t), 'REPLACE')
        ob.vertex_groups[k].add([v.index], cur.get(k, 0.0) + mv, 'REPLACE')
        n += 1
    rep['fade_' + core + '_' + bones_[0]] = n
# belly between the legs: no limb share at all (the smoothed leg borders tore a hem along it in the gallop)
ya, yb, yc, yd = rigcfg.BELLY['y']
sub = [gi[b] for b in rigcfg.BELLY['bones'] if b in gi]
k = gi[rigcfg.BELLY['core']]
n = 0
for v in me.vertices:
    if pcs0.data[v.index].value != 0 or not (ya < v.co.y < yd):
        continue
    t = min(1.0, (v.co.y - ya) / (yb - ya), (yd - v.co.y) / (yd - yc))
    t = t * t * (3 - 2 * t)
    cur = {g.group: g.weight for g in v.groups}
    mv = sum(cur.get(b, 0.0) for b in sub) * t
    if mv <= 1e-4:
        continue
    for b in sub:
        if b in cur:
            ob.vertex_groups[b].add([v.index], cur[b] * (1 - t), 'REPLACE')
    ob.vertex_groups[k].add([v.index], cur.get(k, 0.0) + mv, 'REPLACE')
    n += 1
rep['belly'] = n
for name in feet:
    if name not in gi:
        ob.vertex_groups.new(name=name); gi = {g.name: g.index for g in ob.vertex_groups}
    j = arm.data.bones[name].head_local
    n = 0
    for v in me.vertices:
        if (v.co.x - j.x) ** 2 + (v.co.y - j.y) ** 2 > FOOT_R ** 2:
            continue
        a = (j.z + TOP + BL - v.co.z) / BL
        a = max(0.0, min(1.0, a)); a = a * a * (3 - 2 * a)
        if a > 0:
            setw(v, {gi[name]: 1.0}, a); n += 1
    rep[name] = n
if os.environ.get('UDDER'):
    y0, y1, z1, xa, bone = os.environ['UDDER'].split(',')
    y0, y1, z1, xa = float(y0), float(y1), float(z1), float(xa)
    k = gi[bone]; n = 0
    pcs = me.attributes['piece']
    for v in me.vertices:
        if y0 < v.co.y < y1 and v.co.z < z1 and abs(v.co.x) < xa:
            a = min(1.0, (z1 - v.co.z) / 0.06) * min(1.0, (xa - abs(v.co.x)) / 0.04) * min(1.0, (v.co.y - y0) / 0.12)
            setw(v, {k: 1.0}, a); n += 1
    rep['udder'] = n
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = ob
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
json.dump(rep, open(argv[2], 'w'))
print('WEIGHTS2', rep)
