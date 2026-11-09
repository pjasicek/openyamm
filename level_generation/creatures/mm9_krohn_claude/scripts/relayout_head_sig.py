"""New head UV layout with the face as ONE chart (2026-11-02): xatlas at the texture pass's default chart cost split the
mirrored face along its midline and around the chin, and in game the coarse mip levels blend the hair islands packed
next to those seams into the face (a dark 'goatee' and a spot between the brows in the viewer at party distance).
xatlas splits the face down its midline at any chart cost, so the face (head-shell faces in a front box: |x| < FX,
y < FY, FZ0 < z < FZ1, facing forward) is unwrapped on its own as one island (Blender angle-based, its border the only
seam) and handed to uv_atlas.py as a ready chart with the other head faces (not hands, not the elf ears: they keep
their islands); uv_atlas scales the face FACE_F (option face_factor, default 1.4) times denser and packs everything. Written into
HeadUV scaled by HEAD_SCALE; the old HeadUV is kept as
HeadUV_old so transfer_head_paint.py can carry the paid paint over (one resample). Mesh, weights and the body UVs are
unchanged. mm9_peasantdboy: used BEFORE the head retexture (no transfer needed) and also writes the head upload.
Args (Blender): <in blend> <out blend> <report json> <upload glb> [key=value uv_atlas options, e.g. max_cost=8]"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 2), 'claude_shared'))
import uv_atlas
HEAD_SCALE = 0.8
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REPORT, UPLOAD = argv[:4]
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[4:])}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = body.data
n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
me.attributes['hand'].data.foreach_get('value', hn)
ear_g = body.vertex_groups.get('Bip01 ElfEars')
earv = set()
if ear_g:
    for v in me.vertices:
        if any(g.group == ear_g.index and g.weight > 0.5 for g in v.groups):
            earv.add(v.index)
ear = np.array([all(i in earv for i in p.vertices) for p in me.polygons])
head = (hd == 1) & (hn == 0) & ~ear
if 'HeadUV_old' not in me.uv_layers:
    old = me.uv_layers.new(name='HeadUV_old')
    src = me.uv_layers['HeadUV'].data
    dst = me.uv_layers['HeadUV_old'].data
    for k in range(len(src)):
        dst[k].uv = src[k].uv
FX, FY, FZ0, FZ1 = 0.058, -0.04, 0.583, 0.755  # Sigmund face box (face_probe.py)
# the face shell: the largest connected part among the head faces
bmh = bmesh.new(); bmh.from_mesh(me); bmh.faces.ensure_lookup_table()
comp = [-1] * len(bmh.faces); k = 0
for f in bmh.faces:
    if comp[f.index] >= 0 or not head[f.index]:
        continue
    st = [f]; comp[f.index] = k
    while st:
        g = st.pop()
        for e in g.edges:
            for h in e.link_faces:
                if comp[h.index] < 0 and head[h.index]:
                    comp[h.index] = k; st.append(h)
    k += 1
from collections import Counter
big = Counter(c for c in comp if c >= 0).most_common(1)[0][0]
face = np.zeros(n, bool)
for f in bmh.faces:
    c = f.calc_center_median()
    if comp[f.index] == big and abs(c.x) < FX and c.y < FY and FZ0 < c.z < FZ1 and f.normal.y < -0.1:
        face[f.index] = True
    # the nostrils' undersides fold over the cheeks in a flat unwrap (overlapping texels: the paint transfer drew a
    # streak from the nose to the cheek); they stay with xatlas
    if face[f.index] and abs(c.x) < 0.018 and 0.652 < c.z < 0.668 and f.normal.z < -0.25:
        face[f.index] = False
# keep the face region one disc: fill pockets (non-face faces surrounded by face faces)
for it in range(3):
    for f in bmh.faces:
        if comp[f.index] == big and not face[f.index]:
            nb = [h for e in f.edges for h in e.link_faces if h is not f]
            if nb and sum(face[h.index] for h in nb) >= 2 and f.normal.z > -0.25:
                c = f.calc_center_median()
                if abs(c.x) < FX + 0.01 and FZ0 - 0.005 < c.z < FZ1 + 0.005 and c.y < FY + 0.01:
                    face[f.index] = True
bmh.free()
rest = head & ~face


def part(mask):
    d = body.copy(); d.data = me.copy(); d.modifiers.clear(); d.parent = None
    d.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(d)
    dmm = d.data
    fa = dmm.attributes.new('tp_face', 'INT', 'FACE'); fa.data.foreach_set('value', list(range(n)))
    va = dmm.attributes.new('tp_v', 'INT', 'POINT'); va.data.foreach_set('value', list(range(len(dmm.vertices))))
    b2 = bmesh.new(); b2.from_mesh(dmm); b2.faces.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if not mask[f.index]], context='FACES')
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
    b2.to_mesh(dmm); b2.free(); dmm.update()
    d.vertex_groups.clear()
    for l in [l.name for l in dmm.uv_layers if l.name != 'UVMap']:
        dmm.uv_layers.remove(dmm.uv_layers[l])
    return d


def write_back(d, xform):
    dmm = d.data
    srcf = np.zeros(len(dmm.polygons), np.int32); dmm.attributes['tp_face'].data.foreach_get('value', srcf)
    srcv = np.zeros(len(dmm.vertices), np.int32); dmm.attributes['tp_v'].data.foreach_get('value', srcv)
    du = dmm.uv_layers['UVMap'].data
    hu = me.uv_layers['HeadUV'].data
    areas = []
    for p in dmm.polygons:
        q = me.polygons[int(srcf[p.index])]
        # by original vertex index (rounded positions collided on the mirrored midline's slivers: needles across
        # the face chart that the paint transfer drew as streaks)
        pos = {int(srcv[dmm.loops[li].vertex_index]): xform(np.array(du[li].uv)) for li in p.loop_indices}
        for li in q.loop_indices:
            u = pos[me.loops[li].vertex_index]
            hu[li].uv = (u[0] * HEAD_SCALE, u[1] * HEAD_SCALE)
        t = np.array([xform(np.array(du[li].uv)) for li in p.loop_indices])
        a2 = abs((t[1, 0] - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[2, 0] - t[0, 0]) * (t[1, 1] - t[0, 1])) / 2
        areas.append((a2, p.area))
    return np.array(areas)


# all re-laid faces in one uv_atlas run; the face is fed in as one ready chart: its Blender angle-based unwrap replaces
# xatlas's charts on those faces (in this script only: uv_atlas._xatlas is wrapped), then uv_atlas merges, scales to one
# density (the face FACE_F times denser through a vertex group, as the head factor) and packs as usual
dall = part(head)
dmm = dall.data
srcf = np.zeros(len(dmm.polygons), np.int32); dmm.attributes['tp_face'].data.foreach_get('value', srcf)
fmask = face[srcf]
bm2 = bmesh.new(); bm2.from_mesh(dmm); bm2.faces.ensure_lookup_table()
for e in bm2.edges:
    lf = e.link_faces
    e.seam = bool(len(lf) == 2 and fmask[lf[0].index] != fmask[lf[1].index])
for f in bm2.faces:
    f.select = bool(fmask[f.index])
bm2.to_mesh(dmm); bm2.free()
for o in bpy.data.objects:
    o.select_set(o is dall)
bpy.context.view_layer.objects.active = dall
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.hide(unselected=True)
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0)
bpy.ops.mesh.reveal()
bpy.ops.object.mode_set(mode='OBJECT')
ful = dmm.uv_layers['UVMap'].data
face_corner = np.array([[tuple(ful[li].uv) for li in p.loop_indices] for p in dmm.polygons], np.float64)
vg = dall.vertex_groups.new(name='FACEHI')
vg.add(sorted({v for p in dmm.polygons if fmask[p.index] for v in p.vertices}), 1.0, 'REPLACE')
_orig = uv_atlas._xatlas


def _with_face(mode, inputs, *opts):
    res = _orig(mode, inputs, *opts)
    if mode == 'charts':
        ch = res['chart'].copy(); uv = res['uv'].astype(np.float64).copy()
        ch[fmask] = ch.max() + 1
        uv.reshape(len(ch), 3, 2)[fmask] = face_corner[fmask]
        res = dict(res, chart=ch, uv=uv)
    return res


uv_atlas._xatlas = _with_face
FACE_F = float(options.pop('face_factor', 1.4))
report = uv_atlas.unwrap(dall, head_groups=('FACEHI',), head_factor=FACE_F, **options)
uv_atlas._xatlas = _orig
dall.vertex_groups.clear()
areas = write_back(dall, lambda u: u)
bpy.data.objects.remove(dall)
af, ar = areas[fmask], areas[~fmask]
dens = lambda a: float(np.sqrt(a[:, 0].sum() / a[:, 1].sum()))
report.update(head_faces=int(head.sum()), face_faces=int(face.sum()), ear_faces=int(ear.sum()), face_factor=FACE_F,
              density_face=round(dens(af), 3), density_rest=round(dens(ar), 3),
              face_density_ratio=round(dens(af) / dens(ar), 2),
              zero_area=int((ar[:, 0] < 1e-10).sum() + (af[:, 0] < 1e-10).sum()))
# head upload for the Meshy head retexture: the head faces with HeadUV / HEAD_SCALE as their only UV layer
up = part(head)
um = up.data
src = np.zeros(len(um.polygons), np.int32); um.attributes['tp_face'].data.foreach_get('value', src)
hu = me.uv_layers['HeadUV'].data; uu = um.uv_layers['UVMap'].data
srcv = np.zeros(len(um.vertices), np.int32); um.attributes['tp_v'].data.foreach_get('value', srcv)
for p in um.polygons:
    q = me.polygons[int(src[p.index])]
    byv = {me.loops[lq].vertex_index: hu[lq].uv for lq in q.loop_indices}
    for li in p.loop_indices:
        u = byv[int(srcv[um.loops[li].vertex_index])]
        uu[li].uv = (u[0] / HEAD_SCALE, u[1] / HEAD_SCALE)
for an in ('tp_face', 'tp_v'):
    if an in um.attributes:
        um.attributes.remove(um.attributes[an])
for o in bpy.data.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
bpy.data.objects.remove(up)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REPORT, 'w'), indent=1)
print('RELAYOUT', json.dumps(report))
