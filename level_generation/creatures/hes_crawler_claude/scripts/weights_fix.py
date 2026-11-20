"""Weight repairs after the gates (review/gates_v1.json first pass): work/anim_base_uv.blend -> work/anim_base_w.blend.
1. Leg tubes: heat weights gave the distal end of each body-piece leg tube some Tibia weight, so folding a knee tore the
   tube end (edge stretch up to x8.9 in Death). The knee is the ankle-ring junction: body-piece vertices carry no
   Tibia weight; it moves onto that leg's Femur.
2. Throat sac: the sac weight stopped abruptly below the mouth (lip edges stretched x19 in the Attack's squeeze). Now
   a smooth radial falloff (full within 2.5 cm of the sac centre, zero at 5.5 cm) times a vertical fade that reaches
   zero 1 cm under the mouth line; the remainder goes back to Head. The spring motion was also reduced (anim_hcr.py).
3. Flanks: heat weights gave flank vertices up to 10 cm from a hip mostly to that leg's Femur, so a swinging leg tore
   the flank (x7 in Running). Femur weight is now faded by smoothstep(|x|, 9.5 cm, 13 cm) (inside the flank -> 0, the
   leg tube -> unchanged); the removed weight goes to the spine bone over that y (linear blend 3 cm across borders)."""
import bpy, bmesh, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base_uv.blend'))
mesh = bpy.data.objects['Crawler']; info = json.load(open(os.path.join(HERE, 'work', 'rig_info.json')))
G = {g.name: g for g in mesh.vertex_groups}; idx2name = {g.index: g.name for g in mesh.vertex_groups}
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); k = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = k; st.append(w)
    k += 1
body = int(np.argmax(np.bincount(label)))


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


sac_c = np.array(info['sac_centre']); zm = info['mouth'][2] - 0.02
moved = sac = flank = 0
SPINE = sorted(((min(a, b), max(a, b), n) for n, (a, b) in info['spine'].items()))


def spine_split(y):
    """Spine bones (and shares) over world y: the bone whose span holds y, blended linearly within 3 cm of a border."""
    for i, (lo, hi, n) in enumerate(SPINE):
        if lo <= y <= hi or (i == 0 and y < lo) or (i == len(SPINE) - 1 and y > hi):
            if i > 0 and y - lo < 0.03:
                t = 0.5 + (y - lo) / 0.06; return [(n, t), (SPINE[i - 1][2], 1 - t)]
            if i < len(SPINE) - 1 and hi - y < 0.03:
                t = 0.5 + (hi - y) / 0.06; return [(n, t), (SPINE[i + 1][2], 1 - t)]
            return [(n, 1.0)]
    return [('Body', 1.0)]
for v in mesh.data.vertices:
    if label[v.index] != body:
        continue
    ws = {idx2name[g.group]: g.weight for g in v.groups if g.weight > 0}
    for n in [n for n in ws if n.startswith('Tibia_')]:
        f = 'Femur_' + n[6:]
        ws[f] = ws.get(f, 0) + ws.pop(n); G[n].remove([v.index]); moved += 1
    if 'Sac' in ws:
        ws['Head'] = ws.get('Head', 0) + ws.pop('Sac')
    p = np.array(v.co)
    fade = float(ss(abs(p[0]), 0.095, 0.13))
    for n in [n for n in ws if n.startswith('Femur_')]:
        if fade < 1:
            removed = ws[n] * (1 - fade); ws[n] *= fade
            for sb, sw in spine_split(p[1]):
                ws[sb] = ws.get(sb, 0) + removed * sw
            flank += 1
    w = float((1 - ss(np.linalg.norm(p - sac_c), 0.025, 0.055)) * (1 - ss(p[2], zm - 0.03, zm - 0.01)))
    if w > 0:
        tot = sum(ws.values())
        ws = {n: x * (1 - w) / tot for n, x in ws.items()}; ws['Sac'] = w; sac += 1
    else:
        G['Sac'].remove([v.index]) if 'Sac' in [idx2name[g.group] for g in v.groups] else None
    tot = sum(ws.values())
    for n, x in ws.items():
        G[n].add([v.index], x / tot, 'REPLACE')
print('WEIGHTS tibia->femur vertices', moved, 'sac vertices', sac, 'flank femur fades', flank)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base_w.blend'))
