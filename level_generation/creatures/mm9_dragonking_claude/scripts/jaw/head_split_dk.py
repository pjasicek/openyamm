"""Head texture set split for the Dragon King (2026-10-30 user review: the face needs its own 1K head set; after
mm9_yrsa_claude/v2/scripts/head_split.py, CLAUDE_CREATURE_TEXTURES.md "Head detail").

Head faces (face attribute `head` = 1): faces whose mean weight in the skull/jaw subtree (Xheadpiv and its children:
skull, jaw, tongue, horn and fin pivots) is at least HEAD_W, every loose part that touches the head (eyes, teeth,
the side frill), and the mouth cavity (`mouth`, mouth_rebuild.py). Small islands of either side are flipped so the
cut is one clean line around the back of the skull and the throat.
UV layer `HeadUV`:
- head faces except the mouth: Smart UV, packed into 0..1, exported alone as the Meshy head upload
  (enable_original_uv), then scaled by HEAD_SCALE toward the origin (the composed head set takes the retexture
  resampled into the lower-left HEAD_SCALE square);
- mouth faces: their own UVs from mouth_rebuild.py (palate and floor sheets in the top strip v 0.806..0.994), painted
  by compose_head_dk.py from the Codex mouth swatches.
Args: -- <in blend> <out blend> <upload glb> <report json>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REP = argv[:4]
HEAD_W = 0.5
HEAD_SCALE = 0.8
Z_NECK = 14.45      # level cut under the jaw and the frills: the throat below stays on the body set
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent or bpy.data.objects['MM9_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data


def subtree(name):
    out, st = set(), [rig.data.bones[name]]
    while st:
        b = st.pop(); out.add(b.name); st += list(b.children)
    return out


HB = subtree('Xheadpiv')
vg = {g.index: g.name for g in body.vertex_groups}
hw = np.array([sum(g.weight for g in v.groups if vg[g.group] in HB) / max(sum(g.weight for g in v.groups), 1e-9)
               for v in me.vertices])
mouth = np.zeros(len(me.polygons), np.int32)
me.attributes['mouth'].data.foreach_get('value', mouth)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
shell = np.bincount(comp).argmax()
fh = np.array([hw[[v.index for v in f.verts]].mean() for f in bm.faces])
fz = np.array([max(v.co.z for v in f.verts) for f in bm.faces])
head = ((fh >= HEAD_W) & (fz > Z_NECK)) | (mouth > 0)
# loose parts touching the head: whole part
fcomp = np.array([comp[f.verts[0].index] for f in bm.faces])
for k in set(fcomp[head]):
    if k != shell:
        head[fcomp == k] = True
# clean the cut: flip faces whose edge neighbours are mostly the other side (3 passes), then islands < 12 faces
for _ in range(3):
    flip = []
    for f in bm.faces:
        if fcomp[f.index] != shell or mouth[f.index]:
            continue
        nb = [g.index for e in f.edges for g in e.link_faces if g is not f]
        if nb and np.mean(head[nb]) > 0.66 and not head[f.index]:
            flip.append((f.index, True))
        elif nb and np.mean(head[nb]) < 0.34 and head[f.index]:
            flip.append((f.index, False))
    for i, val in flip:
        head[i] = val


def islands(mask):
    seen = np.zeros(len(mask), bool); out = []
    for f in bm.faces:
        if seen[f.index] or not mask[f.index] or fcomp[f.index] != shell:
            continue
        st = [f]; seen[f.index] = True; isl = []
        while st:
            x = st.pop(); isl.append(x.index)
            for e in x.edges:
                for g in e.link_faces:
                    if not seen[g.index] and mask[g.index] and fcomp[g.index] == shell:
                        seen[g.index] = True; st.append(g)
        out.append(isl)
    return out


for isl in islands(head):
    if len(isl) < 12:
        head[isl] = False
for isl in islands(~head):
    if len(isl) < 12:
        head[isl] = True
bm.free()
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.astype(np.int32).tolist())

# HeadUV: Smart UV on the head faces except the mouth
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(head[p.index] and not mouth[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.008, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.006)
bpy.ops.object.mode_set(mode='OBJECT')


def export_upload(out):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    b2 = bmesh.new(); b2.from_mesh(ob.data)
    hl, ml = b2.faces.layers.int['head'], b2.faces.layers.int['mouth']
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f[hl] == 0 or f[ml] > 0], context='FACES')
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
    b2.to_mesh(ob.data); b2.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != 'HeadUV']:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    for at in [x.name for x in ob.data.attributes if not x.name.startswith('.') and x.name not in ('position', 'HeadUV')]:
        try:
            ob.data.attributes.remove(ob.data.attributes[at])
        except RuntimeError:
            pass
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
    n = len(ob.data.polygons); tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    bpy.data.objects.remove(ob, do_unlink=True)
    return n, tris


nup, tup = export_upload(UPLOAD)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    for li in p.loop_indices:
        if mouth[p.index]:
            huv[li].uv = buv[li].uv.copy()
        elif head[p.index]:
            huv[li].uv = (huv[li].uv[0] * HEAD_SCALE, huv[li].uv[1] * HEAD_SCALE)
me.uv_layers.active = me.uv_layers['UVMap']
tri = lambda m: sum(len(p.vertices) - 2 for p in me.polygons if m[p.index])
rep = {'z_neck': Z_NECK, 'head_faces': int(head.sum()), 'head_triangles': tri(head), 'mouth_triangles': tri(mouth > 0),
       'upload_faces': nup, 'upload_triangles': tup, 'head_scale': HEAD_SCALE, 'head_weight_min': HEAD_W,
       'head_bones': sorted(HB)}
json.dump(rep, open(REP, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADSPLIT', json.dumps({k: v for k, v in rep.items() if k != 'head_bones'}))
# check render: head faces red, mouth pink, body grey
me.materials.clear()
for c in ((0.75, 0.75, 0.75, 1), (0.9, 0.35, 0.3, 1), (0.95, 0.6, 0.75, 1)):
    m = bpy.data.materials.new('c'); m.diffuse_color = c; me.materials.append(m)
me.polygons.foreach_set('material_index', [2 if mouth[i] else (1 if head[i] else 0) for i in range(len(me.polygons))])
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body:
        o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.55, 0.6)
c = Vector((0, -3.3, 15.6))
here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for nm, off in (('front', (0, -1, 0.1)), ('side', (1, -0.2, 0.1)), ('back', (0.2, 1, 0.3)), ('below', (0.2, -0.3, -1))):
    cd = bpy.data.cameras.new(nm); cd.type = 'ORTHO'; cd.ortho_scale = 5.5
    cam = bpy.data.objects.new(nm, cd); sc.collection.objects.link(cam)
    cam.location = c + Vector(off).normalized() * 20; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = os.path.join(here, 'work', 'jaw', f'head_split_{nm}.png'); bpy.ops.render.render(write_still=True)
