"""Chest, collar and collarbone weights of the body (user review 2026-11-02, Talk: "weirdly twists his clothing? like on
breast/collarbones"). fit_rig.py gave body (vest, shirt, collar) vertices near the beard weights of MM9's head-only bones:
Bip01 Ponytail1 (22 % at the upper chest; MM9's Talk swings it 49 deg), Bone03 (MM9's chin; 24-38 deg in AttackMelee/Hit) and
Head (44 % on the collar), and the upper-arm weights ran to the sternum (17 % each). PeasantDM2's chest carries none of the
Ponytail share and its arm share fades medially (humanoid playbook: upper-arm weight fades out medially; no clavicle or
upper-arm weight on the jaw/head). Every body vertex (no head/hand attribute; linings included, they share the cloth's
position): Ponytail1, Bone03 and Head shares -> Neck above ZN1, Spine2 below ZN0, mixed between; on the front and back
of the trunk the UpperArm share keeps smoothstep(|x|, XA0, XA1) and the Clavicle share smoothstep(|x|, XC0, XC1) of itself,
the rest going to Spine2 (or Neck at the collar). Weights only. Args (Blender): <in blend> <out blend>"""
import bpy, bmesh, sys, json
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ZN0, ZN1 = 0.27, 0.33            # Spine2 -> Neck blend for the moved shares (Blender rest; the neck base is ~0.33)
XA0, XA1 = 0.07, 0.17            # upper-arm share: none at the midline, full past 17 cm
XC0, XC1 = 0.02, 0.08            # clavicle share: none on the sternum, full past 8 cm
ZTRUNK0 = 0.05                   # the medial fade applies above the belly
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); hl = bm.faces.layers.int['head']; kl = bm.faces.layers.int['hand']
vs = {v.index for f in bm.faces if not f[hl] and not f[kl] for v in f.verts}
hv = {v.index for f in bm.faces if f[hl] or f[kl] for v in f.verts}
bm.free()
G = {g.name: g for g in ob.vertex_groups}
def ss(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
moved_tot = 0.0; changed = 0
for i in vs - hv:                # vertices shared with head/hand faces keep theirs (seams)
    v = me.vertices[i]; x, y, z = v.co
    w = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
    tot = sum(w.values()) or 1.0
    w = {k: x_ / tot for k, x_ in w.items()}
    t = ss((z - ZN0) / (ZN1 - ZN0))
    to = {}
    def give(amount):
        to['Bip01 Neck'] = to.get('Bip01 Neck', 0.0) + amount * t
        to['Bip01 Spine2'] = to.get('Bip01 Spine2', 0.0) + amount * (1 - t)
    new = {}
    for k, s in w.items():
        if k in ('Bip01 Ponytail1', 'Bone03', 'Bip01 Head'):
            give(s); continue
        if z > ZTRUNK0 and 'UpperArm' in k:
            keep = ss((abs(x) - XA0) / (XA1 - XA0)); new[k] = new.get(k, 0.0) + s * keep; give(s * (1 - keep)); continue
        if z > ZTRUNK0 and 'Clavicle' in k:
            keep = ss((abs(x) - XC0) / (XC1 - XC0)); new[k] = new.get(k, 0.0) + s * keep; give(s * (1 - keep)); continue
        new[k] = new.get(k, 0.0) + s
    for k, s in to.items():
        new[k] = new.get(k, 0.0) + s
    moved = sum(abs(new.get(k, 0) - w.get(k, 0)) for k in set(new) | set(w)) / 2
    if moved < 1e-4:
        continue
    changed += 1; moved_tot += moved
    for k in w:
        G[k].remove([i])
    for k, s in sorted(new.items(), key=lambda kv: -kv[1])[:4]:
        if s > 1e-4:
            G[k].add([i], s, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BODY_REWEIGHT', json.dumps({'vertices_changed': changed, 'mean_share_moved': round(moved_tot / max(changed, 1), 3)}))
