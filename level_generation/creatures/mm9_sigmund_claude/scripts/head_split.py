"""Head texture set split (CLAUDE_CREATURE_TEXTURES.md "Head detail"; user review 2026-10-30: the faces need their own
1K head set and a head retexture).

Head faces: every loose part whose median height is above the neck cut (head and neck shells, hair, hood, eyes,
headband beads), the parts named in `include` / minus `exclude` (by index in the size-independent order printed
here), and, on parts that span the cut (one-shell Meshy bodies), the faces whose vertices are all above `neck_cut_z`
(a level cut through the neck, natm rule). Hand faces (`hand` = 1, graft_hands.py) keep their HeadUV squares.
- face attribute `head` = 1; UV layer `HeadUV`: the head faces Smart-UV-projected and packed into 0..1, exported
  alone as <upload> for the Meshy head retexture (enable_original_uv: true);
- then the head islands are scaled by `head_scale` toward the UV origin (the hands' squares sit in the freed corner),
  so the composed head set is the retexture resampled into the lower-left square (compose_headhand.py).
Writes <blend_out> and <report json>. Args: -- <config json>"""
import bpy, bmesh, json, math, os, sys
import numpy as np
CFG = json.load(open(sys.argv[sys.argv.index('--') + 1]))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda p: p if os.path.isabs(p) else os.path.join(PROJ, p)
bpy.ops.wm.open_mainfile(filepath=P(CFG['blend_in']))
body = bpy.data.objects[CFG.get('body', 'Body')]
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
hand = np.zeros(len(me.polygons), np.int32)
if 'hand' in me.attributes:
    me.attributes['hand'].data.foreach_get('value', hand)
# connected parts (by vertex), ordered by their lowest vertex index (stable across runs)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(me.vertices), np.int32); cid = 0
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
bm.free()
cut = CFG['neck_cut_z']
parts = {}
for k in range(cid):
    m = comp == k
    parts[k] = dict(n=int(m.sum()), zmed=float(np.median(CO[m, 2])), lo=CO[m].min(0).round(3).tolist(),
                    hi=CO[m].max(0).round(3).tolist())
big = max(parts, key=lambda k: parts[k]['n'])
whole = {k for k, p in parts.items() if p['zmed'] > cut and not (k == big and CFG.get('span_big', True))}
whole |= set(CFG.get('include', []))
whole -= set(CFG.get('exclude', []))
span = set(CFG.get('span', [])) | ({big} if CFG.get('span_big', True) else set())
# neck radius: on a spanning shell only faces within this horizontal distance of the neck joint (the shoulders and a
# vest collar are above a level cut too)
NR = CFG.get('neck_radius')
NB = next((b for b in rig.data.bones if b.name.endswith('Neck')), None)
NC = np.array((rig.matrix_world @ NB.head_local)[:2]) if NB is not None else np.zeros(2)
HW = None
if CFG.get('weight_bones'):           # spanning shell: only skin weighted mostly to these bones (not the shoulders)
    gi = {body.vertex_groups[n].index for n in CFG['weight_bones'] if n in body.vertex_groups}
    HW = np.array([sum(g.weight for g in v.groups if g.group in gi) / max(sum(g.weight for g in v.groups), 1e-9)
                   for v in me.vertices])
head = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    vs = list(p.vertices)
    if hand[p.index]:
        continue
    c = comp[vs[0]]
    if c in whole or (c in span and CO[vs, 2].min() > cut and
                      (NR is None or np.linalg.norm(CO[vs, :2] - NC, axis=1).max() < NR or CO[vs, 2].min() > cut + 0.1)
                      and (HW is None or HW[vs].min() >= 0.5)):
        head[p.index] = 1
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.tolist())
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(head[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')


def export_head(out):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    b2 = bmesh.new(); b2.from_mesh(ob.data); hl = b2.faces.layers.int['head']
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f[hl] == 0], context='FACES')
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
    n = len(ob.data.polygons)
    bpy.data.objects.remove(ob, do_unlink=True)
    return n


nup = export_head(P(CFG['upload']))
S = CFG.get('head_scale', 0.8)
huv = me.uv_layers['HeadUV'].data
for p in me.polygons:
    if head[p.index]:
        for li in p.loop_indices:
            huv[li].uv = (huv[li].uv[0] * S, huv[li].uv[1] * S)
me.uv_layers.active = me.uv_layers[CFG.get('uv', 'UVMap')]
rep = {'neck_cut_z': cut, 'head_faces': int(head.sum()), 'hand_faces': int(hand.sum()), 'upload_faces': nup,
       'whole_parts': sorted(int(k) for k in whole), 'span_parts': sorted(int(k) for k in span), 'head_scale': S,
       'parts': {int(k): v for k, v in parts.items()}}
json.dump(rep, open(P(CFG['report']), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=P(CFG['blend_out']))
print('HEADSPLIT', json.dumps({k: v for k, v in rep.items() if k != 'parts'}))
# check render of the split: head faces tinted
cols = {0: (0.75, 0.75, 0.75, 1), 1: (0.9, 0.35, 0.3, 1), 2: (0.3, 0.5, 0.95, 1)}
for i, nm in cols.items():
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = nm; me.materials.append(m)
base = len(me.materials) - 3
me.polygons.foreach_set('material_index', (base + head + 2 * hand).tolist())
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.55, 0.6)
from mathutils import Vector
hv = np.unique(np.concatenate([list(me.polygons[i].vertices) for i in np.where(head)[0]]))
c = Vector(CO[hv].mean(0).tolist())
for nm, off in (('front', (0, -1, 0)), ('side', (1, 0, 0)), ('back', (0, 1, 0))):
    cd = bpy.data.cameras.new(nm); cd.type = 'ORTHO'; cd.ortho_scale = float(np.ptp(CO[hv], 0).max()) * 1.4
    cam = bpy.data.objects.new(nm, cd); sc.collection.objects.link(cam)
    cam.location = c + Vector(off); cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = P(f'review/head_split_{nm}.png'); bpy.ops.render.render(write_still=True)
