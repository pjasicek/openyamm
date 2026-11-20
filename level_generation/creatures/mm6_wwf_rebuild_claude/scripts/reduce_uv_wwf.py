"""Lizardman peasant (copied from mm9_yrsa_claude/scripts/reduce_uv.py): reduce the weighted body after weighting,
then UVs from claude_shared/uv_atlas.py (texture quality pass default; head charts head_factor denser), neutral upload.

Args: <in blend> <out blend> <upload glb> <report json> <config json>
config: "head_bones" (faces mostly weighted to them keep "head_ratio"), "hand_bones" ("hand_ratio"), the rest
"body_ratio"; "head_uv_scale" (face/hair islands this much denser than the body).
Collapse decimation carries the vertex groups. UVs: Smart UV Project, head islands scaled, packed.
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REP, CFG = argv
cfg = json.load(open(CFG))
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
me = ob.data
rig = bpy.data.objects['MM9_Rig']
for b in rig.pose.bones:
    b.matrix_basis.identity()
before = len(me.polygons)


def group_ids(names):
    return {ob.vertex_groups[n].index for n in names if n in ob.vertex_groups}


HEAD = group_ids(cfg['head_bones'])
HAND = group_ids(cfg['hand_bones'])


def share(v, ids):
    return sum(g.weight for g in v.groups if g.group in ids)


vh = [share(v, HEAD) for v in me.vertices]
vk = [share(v, HAND) for v in me.vertices]


def klass(p):
    h = sum(vh[i] for i in p.vertices) / len(p.vertices)
    k = sum(vk[i] for i in p.vertices) / len(p.vertices)
    return 'head' if h >= 0.5 else ('hand' if k >= 0.5 else 'body')


def run(kind, ratio):
    if ratio >= 0.999:
        return
    bpy.context.view_layer.objects.active = ob
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.ops.object.mode_set(mode='OBJECT')
    global vh, vk
    vh = [share(v, HEAD) for v in me.vertices]
    vk = [share(v, HAND) for v in me.vertices]
    for v in me.vertices:
        v.select = False
    for e in me.edges:
        e.select = False
    for p in me.polygons:
        p.select = klass(p) == kind
    for p in me.polygons:
        if p.select:
            for i in p.vertices:
                me.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.decimate(ratio=ratio, use_vertex_group=False)
    bpy.ops.object.mode_set(mode='OBJECT')


counts = {}
for kind in ('head', 'hand', 'body'):
    counts[kind + '_before'] = sum(1 for p in me.polygons if klass(p) == kind)
run('body', cfg['body_ratio'])
run('hand', cfg['hand_ratio'])
run('head', cfg['head_ratio'])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
vh = [share(v, HEAD) for v in me.vertices]
vk = [share(v, HAND) for v in me.vertices]
for kind in ('head', 'hand', 'body'):
    counts[kind + '_after'] = sum(1 for p in me.polygons if klass(p) == kind)
# renormalise and limit to four influences after the collapse
for v in me.vertices:
    gs = sorted([(g.weight, g.group) for g in v.groups if g.weight > 0], reverse=True)
    keep = gs[:4]
    tot = sum(w for w, _ in keep) or 1.0
    for w, gi in gs[4:]:
        ob.vertex_groups[gi].remove([v.index])
    for w, gi in keep:
        ob.vertex_groups[gi].add([v.index], w / tot, 'REPLACE')

for uv in list(me.uv_layers):
    me.uv_layers.remove(uv)
me.uv_layers.new(name='UVMap')
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
report = uv_atlas.unwrap(ob, head_groups=tuple(cfg['head_bones']), head_factor=cfg.get('head_factor', 1.8),
                         **cfg.get('uv_options', {}))
report.update(counts)
json.dump(report, open(REP, 'w'), indent=1)
print('UV_ATLAS', json.dumps(report)[:600])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dup = ob.copy()
dup.data = me.copy()
dup.modifiers.clear()
dup.vertex_groups.clear()
dup.parent = None
dup.matrix_world = ob.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
rep = {'before': before, 'after': len(me.polygons), **counts}
report.update(rep)
json.dump(report, open(REP, 'w'), indent=1)
print('REDUCE ' + json.dumps(rep))
