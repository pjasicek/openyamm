"""Head texture set split (2026-10-30 rework; CLAUDE_CREATURE_TEXTURES.md "Head detail", after
mm9_yrsa_claude/v2/scripts/head_split.py): face attribute `head` on 'Body' = 1 main head, 2 the creature's left arm head
(+X, bones *01), 3 its right arm head, 0 the rest.

Main head: faces whose every vertex has at least `min_weight` of its weight on Bip01 Headx and the Xh* jaw/tongue/nose
chain. Arm heads: the rig gives the upper skull of each arm head to the wrist and forearm bones, so they are cut
geometrically: faces of the arm (vertices mostly on the Xa* chain from Xarmmid down) whose every vertex lies past a
plane across the wrist (through Xawrist + `wrist_offset` along the Xarmmid -> Xawrist axis). Small
pieces (piece 2: teeth, horn and crest spikes, wrist spikes) go whole to the head that most of their faces vote for.
Wings (piece 3/4) never. Writes <blend out> and check renders review/v2/head_split_<view>.png.
Args: <blend in> <blend out> <report json>"""
import bpy, bmesh, json, os, sys
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_W = 0.5
WRIST_OFFSET = float(os.environ.get('WRIST_OFFSET', '-0.22'))   # the wrist spike ring is 22 cm before Xawrist
ARM = ['Xarmmid', 'Xawrist', 'Xaheadpiv', 'Xahead', 'Xajawpiv', 'Xajaw', 'Xatonguepiv', 'Xatongue']
GROUPS = {
    1: ['Bip01 Headx', 'Xhead', 'Xhmouth', 'Xhnose', 'Xhjawpiv', 'Xhjaw', 'Xhchin', 'Xhtonguepiv', 'Xhtongue'],
    2: [n + '01' for n in ('Xaheadpiv', 'Xahead', 'Xajawpiv', 'Xajaw', 'Xatonguepiv', 'Xatongue')],
    3: ['Xaheadpiv', 'Xahead', 'Xajawpiv', 'Xajaw', 'Xatonguepiv', 'Xatongue'],
}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
nv = len(me.vertices)
HW = {k: np.zeros(nv) for k in GROUPS}
for v in me.vertices:
    tot = sum(g.weight for g in v.groups) or 1.0
    for k, names in GROUPS.items():
        ids = {body.vertex_groups[n].index for n in names if n in body.vertex_groups}
        HW[k][v.index] = sum(g.weight for g in v.groups if g.group in ids) / tot
piece = np.zeros(nv, np.int32)
me.attributes['piece'].data.foreach_get('value', piece)
head = np.zeros(len(me.polygons), np.int32)
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
J = lambda n: np.array(rig.matrix_world @ rig.data.bones[n].head_local)
past = {}
for k, suf in ((2, '01'), (3, '')):
    ids = {body.vertex_groups[n + suf].index for n in ARM if n + suf in body.vertex_groups}
    armw = np.array([sum(g.weight for g in v.groups if g.group in ids) / (sum(g.weight for g in v.groups) or 1)
                     for v in me.vertices])
    ax = J('Xawrist' + suf) - J('Xarmmid' + suf); ax /= np.linalg.norm(ax)
    past[k] = ((CO - J('Xawrist' + suf)) @ ax > WRIST_OFFSET) & (armw >= MIN_W)
for p in me.polygons:
    vs = list(p.vertices)
    if piece[vs].max() >= 3:
        continue
    if HW[1][vs].min() >= MIN_W:
        head[p.index] = 1
    for k in (2, 3):
        if past[k][vs].all():
            head[p.index] = k
# small pieces whole, by majority of their faces (ties and minorities -> body)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen = set(); moved = 0
for f in bm.faces:
    if f.index in seen or piece[f.verts[0].index] != 2:
        continue
    comp, st = [], [f]
    seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
    votes = np.bincount(head[comp], minlength=4)
    k = int(np.argmax(votes)) if votes.max() * 2 > len(comp) else 0
    moved += int((head[comp] != k).sum())
    head[comp] = k
bm.free()
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep = {'wrist_offset': WRIST_OFFSET, 'faces': {str(k): int((head == k).sum()) for k in range(4)}, 'min_weight': MIN_W, 'piece_faces_moved': moved}
json.dump(rep, open(REP, 'w'), indent=1)
print('HEADSPLIT', json.dumps(rep))
# check renders: body grey, main head red, left arm head blue, right arm head green
cols = [(0.7, 0.7, 0.7, 1), (0.9, 0.35, 0.3, 1), (0.3, 0.5, 0.95, 1), (0.35, 0.8, 0.4, 1)]
me.materials.clear()
for i, c in enumerate(cols):
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = c; me.materials.append(m)
me.polygons.foreach_set('material_index', head.tolist())
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.55, 0.6)
c = Vector((0, -0.7, 2.5))
os.makedirs(os.path.join(PROJ, 'review', 'v2'), exist_ok=True)
for nm, off in (('front', (0, -1, 0.1)), ('side', (1, -0.2, 0.1)), ('top', (0.2, -0.5, 1))):
    cd = bpy.data.cameras.new(nm); cd.type = 'ORTHO'; cd.ortho_scale = 3.2
    cam = bpy.data.objects.new(nm, cd); sc.collection.objects.link(cam)
    cam.location = c + Vector(off).normalized() * 8; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = os.path.join(PROJ, f'review/v2/head_split_{nm}.png')
    bpy.ops.render.render(write_still=True)
