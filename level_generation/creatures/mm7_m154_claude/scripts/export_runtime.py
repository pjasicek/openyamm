"""Runtime export (m154): work/rig_v6.blend (gated rig, timed clips, bow bones and tracks, Meshy UVs, head split) ->
export/mm7_m154_lod0.glb. One skinned mesh 'M154': materials M154_A (body set 1K, UVMap; the bowstring tube samples a
linen swatch of it), M154Head_A (head set 1K, HeadUV as TEXCOORD_0), Bow_A and Arrow_A (make_bow.py, own textures).
Bones from bow_tracks.py: Bow (bow 100 %, string ends), StringNock (string middle), Arrow (arrow 100 %; scale 0 =
hidden) and Socket_Arrow_Release. Bow and arrow are split into attachments later (tools/split_attachment.py). Clips
Standing, Walking, Running, Attack, Hit, Death, Fidget and Dead (last Death frame held 1 s, arrow hidden); keys at
30 fps, quaternions sign-continuous. Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))   # clips synced from rig_v5 (sync_actions.py)
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'm154_head_basecolor_1k.png'))

# ---------------------------------------------------------------- head UVs into the single UV layer
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
if HEAD:
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])

# ---------------------------------------------------------------- bow, arrow and string (bones from bow_tracks.py)
BR = json.load(open(os.path.join(HERE, 'work', 'bow_rig.json'))); GEO = json.load(open(os.path.join(T, 'props', 'bow_geometry.json')))
B_rest = rig.data.bones['B_R_Hand'].matrix_local @ Matrix(BR['bow_hand'])
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['BowMesh', 'ArrowMesh']
props = []
for o, bone in zip(dst.objects, ('Bow', 'Arrow')):
    scene.collection.objects.link(o)
    o.data.transform(B_rest if bone == 'Bow' else rig.data.bones['Arrow'].matrix_local); o.matrix_world = Matrix()
    o.vertex_groups.clear(); o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    props.append(o)
    print('PROP', bone, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris')
# string: 6-sided tube r 1.1 mm, top end -> nock -> bottom end; weights Bow -> StringNock along each half, the ends
# 0.5 % StringNock so split_attachment.py sees no string triangle wholly on the bow (m214's rule); body material, swatch UV
SW = json.load(open(os.path.join(T, 'm154_swatches.json')))['string_uv']
TOP, BOT, NK = Vector(GEO['top_tip']), Vector(GEO['bot_tip']), Vector(BR['nock_bow'])
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); SEG, SIDES, RAD = 8, 6, 0.0011
pts, wn = [], []
for i in range(SEG + 1):
    pts.append(TOP.lerp(NK, i / SEG)); wn.append(i / SEG)
for i in range(1, SEG + 1):
    pts.append(NK.lerp(BOT, i / SEG)); wn.append(1 - i / SEG)
rings = [[bm.verts.new(B_rest @ (p + Vector((math.cos(2 * math.pi * k / SIDES) * RAD, 0, math.sin(2 * math.pi * k / SIDES) * RAD))))
          for k in range(SIDES)] for p in pts]
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(SIDES):
        f = bm.faces.new((r0[k], r0[(k + 1) % SIDES], r1[(k + 1) % SIDES], r1[k]))
        for lp in f.loops:
            lp[uvl].uv = SW
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
sme = bpy.data.meshes.new('StringMesh'); bm.to_mesh(sme); bm.free()
string = bpy.data.objects.new('StringMesh', sme); scene.collection.objects.link(string)
gB, gN = string.vertex_groups.new(name='Bow'), string.vertex_groups.new(name='StringNock')
for i in range(len(sme.vertices)):
    w = max(wn[i // SIDES], 0.005)
    if w < 1:
        gB.add([i], 1 - w, 'REPLACE')
    gN.add([i], w, 'REPLACE')
print('PROP String', len(sme.polygons) * 2, 'tris')
# ---------------------------------------------------------------- materials


def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


mats = [material('M154_A', 'm154_basecolor_1k.png', 'm154_normal_1k.png', 'm154_metal_rough_1k.png')]
if HEAD:
    mats.append(material('M154Head_A', 'm154_head_basecolor_1k.png', 'm154_head_normal_1k.png', 'm154_head_metal_rough_1k.png'))
pm = [material('Bow_A', 'm154_bow_basecolor.png', 'm154_bow_normal.png', 'm154_bow_metal_rough.png'),
      material('Arrow_A', 'm154_arrow_basecolor.png', 'm154_arrow_normal.png', 'm154_arrow_metal_rough.png')]
me.materials.clear()
for m in mats + pm:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
for o, m in zip(props, pm):
    o.data.materials.clear(); o.data.materials.append(m)
sme.materials.append(mats[0])
for o in bpy.data.objects:
    o.select_set(o in [body, string] + props)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'M154'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    body.data.attributes.remove(body.data.attributes[at])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        if pb.name == 'Arrow':                                       # the arrow stays hidden on the corpse
            pb.scale = (0, 0, 0); pb.keyframe_insert('scale', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm7_m154_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
