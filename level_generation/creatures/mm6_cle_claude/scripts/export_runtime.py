"""Runtime export: work/rig_v4.blend -> export/mm6_cle_lod0.glb (one skinned mesh 'Cleric', materials Cleric_A (body
set) and ClericHead_A (head texture set)); adapted from mm6_thf_claude/scripts/export_runtime.py.
 - Body maps from prepare_textures.py: base colour 1024, normal 1024, ORM 1024 (R AO, G roughness, B metallic).
 - Head faces (attribute `head`, apply_head_split.py) keep their own 0..1 UVs and the head maps from
   claude_shared/compose_head_set.py.
 - The staff joins the mesh (100 % on the Staff bone; build_runtime.sh splits it into an attachment afterwards), its
   faces mapped into the atlas gold swatches by their position along the staff: the finial, crossbars and collar knob
   bright gold, the shaft darker gold.
 - Sockets (non-deforming bones): Socket_Staff_Head at the ring centre (the StaffTip bone; Attack's bolts leave it),
   Socket_Palm_R in front of the right palm (Cast, user review 2026-10-14: the library Cast thrusts the free palm).
 - Hands (user review 2026-10-14): the old hand faces (`old_hand`) are removed and HandL/HandR (fit_hands.py) join
   under the head material; the head faces' UVs are scaled by fit.json head_scale (hand_texture_set.py maps).
 - Game clips: Standing, Walking, Running, Attack, Cast, Hit, Death, Dead, Fidget (quaternion keys sign-continuous).
 - Walk stride from the planted-foot travel, written to export/export_info.json."""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
T = os.path.join(common.PROJECT, 'textures')
mesh, rig, staff = bpy.data.objects['Cleric'], bpy.data.objects['Cleric_Rig'], bpy.data.objects['Staff']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


def fix_quaternion_signs(action):
    """Each bone's quaternion keys sign-continuous (opposite-sign neighbours interpolate the long way round)."""
    curves = {}
    for fc in fcurves(action):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    flipped = 0
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]
        prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] = -keys[i][j].co[1]
                    keys[i][j].handle_left[1] = -keys[i][j].handle_left[1]
                    keys[i][j].handle_right[1] = -keys[i][j].handle_right[1]
                q = [-x for x in q]
                flipped += 1
            prev = q
        for fc in comps.values():
            fc.update()
    return flipped


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname))
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


body = material('Cleric_A', 'cle_a_basecolor_1k.png', 'cle_normal_1k.png', 'cle_metal_rough_1k.png')
head = material('ClericHead_A', 'cle_headhand_basecolor.png', 'cle_headhand_normal_1k.png', 'cle_headhand_metal_rough_1k.png')
head_flags = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['head'].data.foreach_get('value', head_flags)
mesh.data.materials.clear()
mesh.data.materials.append(body)
mesh.data.materials.append(head)
mesh.data.polygons.foreach_set('material_index', head_flags)

# new hands (fit_hands.py, user review 2026-10-14): the head texture set is scaled into its lower-left corner
# (hand_texture_set.py) and the hands use its freed top-right squares; the old hand faces go
FIT = json.load(open(os.path.join(common.WORK, 'hands', 'fit.json')))
uvd = mesh.data.uv_layers.active.data
for p in mesh.data.polygons:
    if head_flags[p.index]:
        for li in p.loop_indices:
            uvd[li].uv = (uvd[li].uv[0] * FIT['head_scale'], uvd[li].uv[1] * FIT['head_scale'])
import bmesh
old_hand = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['old_hand'].data.foreach_get('value', old_hand)
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.faces.ensure_lookup_table()
# the tunic skirt's lining goes too (user review 2026-10-14 (3)): the body material is double-sided, so the outside
# shows its own back from inside, and the lining (skirt_shell.py, skirt_sides.json) showed through the outside as
# light shards wherever the walk folded the panel's edges
# and an exact inner copy of the outside replaces it (skirt_shell.add_inside: same weights, 4 mm in, the dark inside
# swatch), so the panel still shows a darker inside where it curls instead of its own back lit as a front
SD = json.load(open(os.path.join(common.WORK, 'skirt_sides.json')))
LINING = set(SD['inner']); OUTSIDE = [f for f in bm.faces if f.index in set(SD['skirt']) - LINING]
import skirt_shell
SWL = json.load(open(os.path.join(T, 'cle_staff_swatches.json')))['lining']
INSIDE = skirt_shell.add_inside(bm, OUTSIDE, bm.loops.layers.uv.active, (SWL[0], SWL[1]))
INS = set(INSIDE)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in INS and (old_hand[f.index] or f.index in LINING)],
                 context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(mesh.data); bm.free()
hands = [bpy.data.objects[n] for n in ('HandL', 'HandR')]
uv_name = mesh.data.uv_layers.active.name
for h in hands:
    h.data.uv_layers.remove(h.data.uv_layers['MHUV'])
    h.data.uv_layers['HandUV'].name = uv_name
    h.data.materials.clear(); h.data.materials.append(body); h.data.materials.append(head)
    h.data.polygons.foreach_set('material_index', [1] * len(h.data.polygons))
    for a in [a.name for a in h.data.attributes if a.name == 'hand']:
        h.data.attributes.remove(h.data.attributes[a])
    h.modifiers.clear()
hr = bpy.data.objects['HandR']; wr = rig.matrix_world @ rig.pose.bones['RightHand'].head
hv = [hr.matrix_world @ v.co for v in hr.data.vertices]
hdir = (sum(hv, Vector()) / len(hv) - wr).normalized()
band = [v for v in hv if 0.035 < (v - wr).dot(hdir) < 0.075]
pc = sum(band, Vector()) / len(band)
PALM = list(pc + Vector((max(v.x for v in band) - pc.x + 0.015, 0, 0)))   # palm faces +X (the thigh) at rest
print('LINING removed', len(LINING), 'skirt lining faces; inside copy', len(INSIDE), 'faces')
print('HANDS removed', int(old_hand.sum()), 'old faces; new', [sum(len(p.vertices) - 2 for p in h.data.polygons) for h in hands])

# staff faces into the gold swatches (by position along the rest staff axis, measured from the grip)
ST = json.loads(bpy.context.scene['cle_staff'])
SW = json.load(open(os.path.join(T, 'cle_staff_swatches.json')))
axis, grip = Vector(ST['axis']), Vector(ST['grip'])
finial_from = ST['length'] - ST['grip_from_foot'] - 0.215          # collar knob and above, from the grip
uvl = staff.data.uv_layers.new(name='UVMap') if not staff.data.uv_layers else staff.data.uv_layers.active
uvl = staff.data.uv_layers.active.data
counts = {}
for p in staff.data.polygons:
    s_ = (staff.matrix_world @ p.center - grip).dot(axis)
    name = 'gold' if s_ > finial_from else 'gold_dark'
    u, v, r = SW[name]
    for k, li in enumerate(p.loop_indices):
        ang = 2.0 * np.pi * k / len(p.loop_indices)
        uvl[li].uv = (u + r * np.cos(ang), v + r * np.sin(ang))
    counts[name] = counts.get(name, 0) + 1
    p.use_smooth = True
print('STAFF faces', counts)
staff.data.materials.clear(); staff.data.materials.append(body)
for a in [a.name for a in mesh.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head', 'old_hand')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])
staff.modifiers.clear()
for o in bpy.data.objects:
    o.select_set(o in [mesh, staff] + hands)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('JOINED', mesh.name, 'materials', [m.name for m in mesh.data.materials], 'tris',
      sum(len(p.vertices) - 2 for p in mesh.data.polygons))

# sockets
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
eb['StaffTip'].name = 'Socket_Staff_Head'
# Cast launches from the free right palm (library Cast: the palm thrusts at the target): palm centre 1.5 cm out of the
# palm surface, measured on the new right hand at rest
pb_ = eb.new('Socket_Palm_R'); pb_.parent = eb['RightHand']; pb_.use_deform = False
palm_local = rig.matrix_world.inverted() @ Vector(PALM)
pb_.head = palm_local; pb_.tail = palm_local + Vector((0, 0, -0.03))
bpy.ops.object.mode_set(mode='OBJECT')
print('SOCKETS', [b.name for b in rig.data.bones if b.name.startswith('Socket_')])

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print('SIGNS', {a.name: fix_quaternion_signs(a) for a in bpy.data.actions})

act = bpy.data.actions['Walking']
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
ys = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f)
    ys.append((rig.matrix_world @ rig.pose.bones['LeftFoot'].head).y)
stride = (max(ys) - min(ys)) / 0.6
rig.animation_data.action = bpy.data.actions['Standing']
if bpy.data.actions['Standing'].slots:
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
bpy.context.scene.frame_set(0)
out = os.path.join(common.PROJECT, 'export', 'mm6_cle_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_length_m': stride, 'rest_bounds_m': [list(lo), list(hi)],
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
