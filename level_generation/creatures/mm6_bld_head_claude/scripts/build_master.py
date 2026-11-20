"""Bloodsucker head-set master: the accepted 45 % reduction in the animated master, a new maw (oral disc) and head UVs.

In:  work/anim_v1_source.blend (copy of mm6_bld_claude/work/anim_v1.blend: rig, procedural clips, full mesh) and the
     installed reduction's Cand_45 (mm6_bld_reduce_claude/work/ladder.blend, weights by data transfer, body UVs).
Out: work/master.blend, texturing/bld_head_upload.glb (head faces without the maw, rest pose, head UVs), work/master.json.

- The old flat maw disc (faces on the Maw bone) is removed. The new maw is the sprite's oral disc (native attack b-c:
  the mouth thrust at the viewer): a shallow dish just in front of the tube tip carrying the maw art, with a thick
  rounded hide rim behind it (the art's rim band). Its Maw bone sits at the opening
  centre on the tube's own axis (the old bone pointed straight ahead, 9 degrees off the opening, so the disc tilted out
  of the lip).
- Maw keys: hidden (scale 0.01) whenever the old disc rested at 0.55; it grows with the old opening amount up to the
  old attack span (0.25 m radius); its depth grows to about half that, so the side view reads as a thick lip ring.
- Head faces (face attribute `head`): mostly weighted to Neck2, Head, Mouth or Maw (the eyes sit at the Head root). Their UVs are a fresh layout filling 0..1;
  the maw's inner surface is one round island of MAW_SHARE of the atlas, its outer shell reuses that island's rim band.
  Body faces keep the installed UVs (the body texture set is unchanged)."""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRE = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, 'work', 'anim_v1_source.blend')
LADDER = os.path.join(CRE, 'mm6_bld_reduce_claude', 'work', 'ladder.blend')
R0, DEPTH, SEG, RINGS = 0.020, 0.005, 24, 4            # oral disc radius and its shallow dish depth at scale 1 (m)
ATTACK_RADIUS, REST_SCALE, ATTACK_DEPTH = 0.25, 0.01, 6.0   # axial scale at the attack peak: about half the radial
FORWARD_MARGIN = 0.015                                  # m ahead of the snout at full gape
MAW_SHARE = 0.20                                        # share of the head atlas for the maw art island


def rest(rig):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=SOURCE)
rig = bpy.data.objects['Bld_Rig']
rest(rig)
old = bpy.data.objects['Bld']
with bpy.data.libraries.load(LADDER) as (src, dst):
    dst.objects = ['Cand_45']
mesh = dst.objects[0]
bpy.context.scene.collection.objects.link(mesh)
# the load also brings the ladder's armature and its actions along (modifier dependency): drop them
for o in [o for o in bpy.data.objects if o.name not in ('Bld_Rig', 'Bld', mesh.name)]:
    bpy.data.objects.remove(o)
for a in [a for a in bpy.data.actions if '.' in a.name]:
    bpy.data.actions.remove(a)
for arm in [d for d in bpy.data.armatures if d.users == 0]:
    bpy.data.armatures.remove(arm)
mesh.parent = rig
mesh.matrix_world = old.matrix_world.copy()
mesh.hide_render = mesh.hide_viewport = False
mesh.hide_set(False)
for md in mesh.modifiers:
    if md.type == 'ARMATURE':
        md.object = rig
for name in ('ReduceProtect',):
    if name in mesh.vertex_groups:
        mesh.vertex_groups.remove(mesh.vertex_groups[name])
bpy.data.objects.remove(old)
mesh.name = 'Bld'
mesh.data.name = 'Bld'
mesh.data.materials.clear()
gi = {g.name: g.index for g in mesh.vertex_groups}

# --- remove the old maw disc ---------------------------------------------------------------------------------------
bm = bmesh.new()
bm.from_mesh(mesh.data)
dl = bm.verts.layers.deform.active
maw_verts = [v for v in bm.verts if v[dl].get(gi['Maw'], 0.0) > 0.5]
removed = len(maw_verts)
bmesh.ops.delete(bm, geom=maw_verts, context='VERTS')
bm.to_mesh(mesh.data)
bm.free()

# --- mouth opening from the rest mesh -----------------------------------------------------------------------------
co = np.array([v.co[:] for v in mesh.data.vertices])
mouth = np.array([sum(g.weight for g in v.groups if g.group == gi['Mouth']) for v in mesh.data.vertices]) > 0.5
forward = np.array([0.0, -1.0, 0.0])
reach = co[mouth] @ forward
rim = co[mouth][reach > reach.max() - 0.012]
centre = rim.mean(0)
centre[0] = 0.0                                          # symmetric creature
_, _, vt = np.linalg.svd(rim - rim.mean(0))
axis = vt[2] * np.sign(vt[2] @ forward)
axis[0] = 0.0
axis /= np.linalg.norm(axis)
C, N = Vector(centre), Vector(axis)
# the disc sits 1 mm in front of the most forward head vertex (the snout prongs reach past the tube lip), so at full
# gape it covers the snout end like the sprite's oral disc
head_co = co[np.array([sum(g.weight for g in v.groups if g.group in (gi['Head'], gi['Mouth'])) for v in mesh.data.vertices]) > 0.5]
C = C + N * (((head_co - centre) @ axis).max() + 0.001)

# --- Maw bone at the opening on the tube axis ---------------------------------------------------------------------
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Maw']
eb.head = C
eb.tail = C + N * 0.03
eb.align_roll(Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')
bone = rig.data.bones['Maw']
bx, bz = Vector(bone.matrix_local.col[0][:3]), Vector(bone.matrix_local.col[2][:3])   # radial axes of the bone

# --- new maw: oral disc -------------------------------------------------------------------------------------------------
verts, faces, kinds, radial = [], [], [], []
def ring(radius, depth):
    start = len(verts)
    for s in range(SEG):
        a = 2 * math.pi * s / SEG
        p = C + (bx * math.cos(a) + bz * math.sin(a)) * radius - N * depth
        verts.append(p); radial.append((math.cos(a), math.sin(a), radius / R0))
    return start
# inner surface, seen from the front: centre deep in the throat, rim at the opening plane
verts.append(C - N * DEPTH); radial.append((0.0, 0.0, 0.0))
rings = [ring(R0 * k / RINGS, DEPTH * (1 - (k / RINGS) ** 1.5)) for k in range(1, RINGS + 1)]
for s in range(SEG):
    faces.append((0, rings[0] + s, rings[0] + (s + 1) % SEG)); kinds.append('inner')
for r0, r1 in zip(rings, rings[1:]):
    for s in range(SEG):
        s1 = (s + 1) % SEG
        faces.append((r0 + s, r1 + s, r1 + s1, r0 + s1)); kinds.append('inner')
# outer shell: a thin lip, then a cone behind the rim back into the throat
lip = ring(R0 * 1.04, 0.0015)                               # thick rounded hide rim behind the disc edge
back = [ring(R0 * f, R0 * d) for f, d in ((0.95, 0.22), (0.7, 0.35), (0.35, 0.4))]
for r0, r1 in zip([rings[-1], lip] + back[:-1], [lip] + back):
    for s in range(SEG):
        s1 = (s + 1) % SEG
        faces.append((r0 + s, r0 + s1, r1 + s1, r1 + s)); kinds.append('outer')
dm = bpy.data.meshes.new('maw')
dm.from_pydata([v[:] for v in verts], [], faces)
dm.update()
disc = bpy.data.objects.new('maw', dm)
bpy.context.scene.collection.objects.link(disc)
disc.parent = rig
disc.vertex_groups.new(name='Maw').add(list(range(len(verts))), 1.0, 'REPLACE')
# orient: inner faces toward the front (+N), outer faces away from it
for p, kind in zip(dm.polygons, kinds):
    if (p.normal.dot(N) > 0) != (kind == 'inner'):
        p.flip()
for p in dm.polygons:
    p.use_smooth = True
dm.attributes.new('maw_kind', 'INT', 'FACE').data.foreach_set('value', [1 if k == 'inner' else 2 for k in kinds])
uvl = dm.uv_layers.new(name=mesh.data.uv_layers.active.name)
for p in dm.polygons:
    for li in p.loop_indices:
        cx, cz, k = radial[dm.loops[li].vertex_index]
        uvl.data[li].uv = (0.5 + 0.5 * cx * min(k, 1.0), 0.5 + 0.5 * cz * min(k, 1.0))
for o in bpy.data.objects:
    o.select_set(o in (mesh, disc))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
mesh = bpy.data.objects['Bld']
gi = {g.name: g.index for g in mesh.vertex_groups}

# --- head faces and head UVs --------------------------------------------------------------------------------------
heads = {gi[n] for n in ('Neck2', 'Head', 'Mouth', 'Maw')}
w = [sum(g.weight for g in v.groups if g.group in heads) for v in mesh.data.vertices]
kind_attr = mesh.data.attributes['maw_kind'].data
head = [sum(w[i] for i in p.vertices) / len(p.vertices) >= 0.5 or kind_attr[p.index].value > 0
        for p in mesh.data.polygons]
mesh.data.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [int(h) for h in head])

bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh.data)
kl = bm.faces.layers.int['maw_kind']
uv = bm.loops.layers.uv.active
# Seams instead of smart projection (which cut the decimated head into ~150 islands): the lip between the outer
# tube and the throat cup (faces turned toward the tube axis), and the underside midline of the head and neck.
hide = [f for f in bm.faces if head[f.index] and f[kl] == 0]
hide_ids = {f.index for f in hide}
def throat(f):
    d = f.calc_center_median() - C
    radial = d - N * d.dot(N)
    return radial.length < 0.045 and radial.length > 1e-6 and f.normal.dot(radial.normalized()) < -0.3
inner = {f.index for f in hide if throat(f)}
for e in bm.edges:
    e.seam = False
    faces = [f for f in e.link_faces if f.index in hide_ids]
    if len(faces) != 2:
        continue
    a, b = faces
    if (a.index in inner) != (b.index in inner):
        e.seam = True
    elif a.index not in inner and a.normal.z < -0.3 and b.normal.z < -0.3 \
            and (a.calc_center_median().x > 0) != (b.calc_center_median().x > 0):
        e.seam = True
for f in bm.faces:
    f.select = f.index in hide_ids
bmesh.update_edit_mesh(mesh.data)
bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=0.004)
bm = bmesh.from_edit_mesh(mesh.data)
kl = bm.faces.layers.int['maw_kind']
uv = bm.loops.layers.uv.active
hide_area = sum(abs(sum(l[uv].uv.x * l.link_loop_next[uv].uv.y - l.link_loop_next[uv].uv.x * l[uv].uv.y
                        for l in f.loops)) / 2 for f in bm.faces if f.select)
side = math.sqrt(hide_area * MAW_SHARE / (1 - MAW_SHARE))   # maw island (bounding square) next to the hide islands
for f in bm.faces:
    if f[kl] == 1:
        for l in f.loops:
            l[uv].uv = (l[uv].uv.x * side, l[uv].uv.y * side)
    f.select = head[f.index] and f[kl] != 2
bmesh.update_edit_mesh(mesh.data)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bm = bmesh.from_edit_mesh(mesh.data)
kl = bm.faces.layers.int['maw_kind']
uv = bm.loops.layers.uv.active
inner = [l[uv].uv.copy() for f in bm.faces if f[kl] == 1 for l in f.loops]
lo = Vector((min(p.x for p in inner), min(p.y for p in inner)))
hi = Vector((max(p.x for p in inner), max(p.y for p in inner)))
mc, mr = (lo + hi) / 2, (hi.x - lo.x) / 2
for f in bm.faces:
    if f[kl] == 2:                                    # outer shell: the art's rim band, same angle
        for l in f.loops:
            d = l[uv].uv - Vector((0.5, 0.5))
            d = d.normalized() if d.length > 1e-9 else Vector((1, 0))
            l[uv].uv = mc + d * mr * 0.93
bmesh.update_edit_mesh(mesh.data)
bpy.ops.object.mode_set(mode='OBJECT')

# --- maw keys -----------------------------------------------------------------------------------------------------
attack_scale = ATTACK_RADIUS / R0
report = {}
for act in bpy.data.actions:
    for cb in (cb for l in act.layers for s in l.strips for cb in s.channelbags):
        curves = {fc.array_index: fc for fc in cb.fcurves if fc.data_path == 'pose.bones["Maw"].scale'}
        if not curves:
            continue
        opening = {}
        for k0, k1, k2 in zip(curves[0].keyframe_points, curves[1].keyframe_points, curves[2].keyframe_points):
            t = min(1.0, max(0.0, (k0.co[1] - 0.55) / (4.84 - 0.55)))
            opening[k0.co[0]] = t
            s = REST_SCALE + t * (attack_scale - REST_SCALE)
            a = 0.3 + t * (ATTACK_DEPTH - 0.3)
            for k, v in ((k0, s), (k1, a), (k2, s)):
                k.co[1] = v
                k.handle_left[1] = v
                k.handle_right[1] = v
        # slide the disc forward along the mouth axis (bone +Y) by its dish depth plus a margin as it opens: the flared
        # snout prongs sit in front of the recessed dish centre otherwise and show through it
        frames = sorted(opening)
        location = next(fc for fc in cb.fcurves if fc.data_path == 'pose.bones["Maw"].location' and fc.array_index == 1)
        for k in location.keyframe_points:
            t = opening[min(frames, key=lambda f: abs(f - k.co[0]))]
            v = t * (DEPTH * ATTACK_DEPTH + FORWARD_MARGIN)
            k.co[1] = v
            k.handle_left[1] = v
            k.handle_right[1] = v
        for fc in list(curves.values()) + [location]:
            fc.update()
        report[act.name] = round(max(k.co[1] for k in curves[0].keyframe_points), 3)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'master.blend'))

# --- head upload (no maw) -----------------------------------------------------------------------------------------
dup = mesh.copy()
dup.data = mesh.data.copy()
dup.modifiers.clear()
dup.parent = None
bpy.context.scene.collection.objects.link(dup)
bm = bmesh.new()
bm.from_mesh(dup.data)
kl = bm.faces.layers.int['maw_kind']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index] or f[kl] != 0], context='FACES')
bm.to_mesh(dup.data)
bm.free()
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
out = os.path.join(HERE, 'texturing', 'bld_head_upload.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
mesh = bpy.data.objects['Bld']
kinds = [d.value for d in mesh.data.attributes['maw_kind'].data]
info = {'removed_maw_verts': removed, 'tris': sum(len(p.vertices) - 2 for p in mesh.data.polygons),
        'head_tris': sum(len(p.vertices) - 2 for p, h in zip(mesh.data.polygons, head) if h),
        'maw_tris': sum(len(p.vertices) - 2 for p in mesh.data.polygons if kinds[p.index] > 0),
        'actions': [a.name for a in bpy.data.actions], 'objects': [o.name for o in bpy.data.objects if o.name != dup.name],
        'opening_centre': [round(x, 4) for x in centre], 'opening_axis': [round(x, 4) for x in axis],
        'maw_uv_centre': [round(mc.x, 4), round(mc.y, 4)], 'maw_uv_radius': round(mr, 4), 'maw_max_scale': report}
json.dump(info, open(os.path.join(HERE, 'work', 'master.json'), 'w'), indent=1)
print('MASTER', json.dumps(info))
