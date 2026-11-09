"""Flying demon v2 assembly, run on delivery/mm6_flying_demon.blend (Codex master; body, horns, rig and body
materials are kept). Removes the Codex wings, struts, death plume/ash, review camera/lights and all actions, then
builds new wings from the native spread frame (work/wing_mesh.json from extract_wing.py):
  - membrane mesh = traced native outline, mapped from sprite px to metres at the eye reference
    (s = 0.0035 m/px, sprite eye y 65 -> z 1.762, midline x 384); the root edge hugs the upper back and the
    outer wing sweeps slightly back with a little camber,
  - texture = the native membrane pixels (alpha-cut outline), per tier,
  - bones per side: Wing_Root (Spine2) -> Wing_Arm -> Wing_Finger1..4 along the native finger struts,
  - weights = inverse squared distance to the bone segments in sprite space (top three, normalised).
Saves claude_v2/work/assembled.blend. Blender: Z up, -Y front, +X creature left."""
import bpy, os, json, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S, EYE_Y, EYE_Z, MID_X = 0.0035, 65.0, 1.762, 384.0
rig = bpy.data.objects['Flying_Demon_Rig']

# ---- cleanup -------------------------------------------------------------------------------------------------
drop = [o for o in bpy.data.objects if o.name.startswith(('Flying_Wing_', 'Wing_Strut_', 'Flying_Demon_Ash',
        'Flying_Demon_Disintegration', 'Demon_Native_Review_Camera', 'Flying_Fill', 'Flying_Key', 'Icosphere'))]
for o in drop:
    bpy.data.objects.remove(o, do_unlink=True)
vis = bpy.data.objects.get('Flying_Demon_Visibility')
if vis:
    mw = rig.matrix_world.copy(); rig.parent = None; rig.matrix_world = mw
    bpy.data.objects.remove(vis, do_unlink=True)
for o in list(bpy.data.objects):
    if o.name.startswith('Flying_Plume'):
        bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for o in bpy.data.objects:
    if o.animation_data:
        o.animation_data_clear()
rig.data.pose_position = 'POSE'
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
for b in list(rig.data.edit_bones):
    if b.name.startswith('Wing_'):
        rig.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')

RIG_INV = rig.matrix_world.inverted()

# ---- geometry -------------------------------------------------------------------------------------------------
data = json.load(open(os.path.join(HERE, 'work', 'wing_mesh.json')))
V2 = np.array(data['vertices']); TRI = data['triangles']
x0, y0, x1, y1 = data['bbox']
ROOT_PX = float(data['root_x'])
STRIP_TOP_PX = EYE_Y + (EYE_Z - 1.60) / S          # root strip stops at shoulder height (z 1.60)


def back_y(ax):
    """Wing sheet depth: hugs the upper back near the spine, sits behind the shoulders, outer wing sweeps back."""
    return float(np.interp(ax, (0.0, 0.12, 0.18, 0.30), (-0.035, -0.05, -0.07, -0.10))) + max(0.0, ax - 0.30) * 0.22


def to_world(px, py, sign):
    """Sprite px -> rig-local metres (the rig object sits above the world origin)."""
    ax = (MID_X - px) * S                           # distance from the midline (image-left wing)
    z = EYE_Z - (py - EYE_Y) * S
    return RIG_INV @ Vector((sign * ax, back_y(ax), z))


def camber(v2):
    """Membrane sags backward between the struts: offset grows with distance below the leading edge."""
    return 0.0


# finger struts in sprite px (image-left wing): root joint, wrist (top hook), tips
ROOT_IN, ROOT_OUT, WRIST = (372.0, 108.0), (ROOT_PX, 100.0), (270.0, 20.0)
TIPS = [(8.0, 140.0), (107.0, 197.0), (185.0, 240.0), (282.0, 172.0)]
SEGMENTS = {'Root': (ROOT_IN, ROOT_OUT), 'Arm': (ROOT_OUT, WRIST)}
for k, tip in enumerate(TIPS):
    SEGMENTS[f'Finger{k + 1}'] = (WRIST, tip)


def seg_dist(p, a, b):
    p, a, b = np.asarray(p), np.asarray(a), np.asarray(b)
    t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1)
    return float(np.linalg.norm(p - (a + t * (b - a))))


# Root strip: extend the membrane from the root column to the spine so the wing attaches to the back.
root_rows = [p for p in V2 if p[0] >= ROOT_PX - 1.5]
ry0, ry1 = min(p[1] for p in root_rows), max(p[1] for p in root_rows)

bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
spine2 = eb['mixamorig:Spine2']
for side, sign in (('Left', 1.0), ('Right', -1.0)):
    # image-left wing is the creature's right; mirror for the left
    w = lambda p: to_world(p[0], p[1], sign)
    names = {'Root': f'Wing_{side}_Root', 'Arm': f'Wing_{side}_Arm'}
    root = eb.new(names['Root']); root.head = w(ROOT_IN); root.tail = w(ROOT_OUT); root.parent = spine2
    arm = eb.new(names['Arm']); arm.head = w(ROOT_OUT); arm.tail = w(WRIST); arm.parent = root; arm.use_connect = True
    for k, tip in enumerate(TIPS):
        f = eb.new(f'Wing_{side}_Finger{k + 1}'); f.head = w(WRIST); f.tail = w(tip); f.parent = arm
    for n in [names['Root'], names['Arm']] + [f'Wing_{side}_Finger{k + 1}' for k in range(4)]:
        eb[n].align_roll(Vector((0, 1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')

mat_names = {}
for tier in 'abc':
    mat = bpy.data.materials.new(f'Flying_{tier.upper()}_Wing'); mat.use_nodes = True; mat.use_fake_user = True
    mat.use_backface_culling = False
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    img = bpy.data.images.load(os.path.join(HERE, 'textures', f'wing_{tier}_basecolor.png'))
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.72; bsdf.inputs['Metallic'].default_value = 0.0
    mat.blend_method = 'CLIP' if hasattr(mat, 'blend_method') else mat.blend_method
    try:
        mat.alpha_threshold = 0.5
    except AttributeError:
        pass
    mat_names[tier] = mat

for side, sign in (('Left', 1.0), ('Right', -1.0)):
    pts = [list(p) for p in V2]
    tris = [list(t) for t in TRI]
    # root strip quads (sprite px) from the root column to the spine
    strip_cols = np.linspace(ROOT_PX, ROOT_IN[0], 5)
    strip_rows = np.linspace(max(ry0 + 4, STRIP_TOP_PX), ry1 - 4, 5)   # no membrane behind the neck
    base = len(pts)
    for cx in strip_cols:
        for cy in strip_rows:
            pts.append([float(cx), float(cy)])
    nr = len(strip_rows)
    for i in range(len(strip_cols) - 1):
        for j in range(nr - 1):
            a = base + i * nr + j; b = a + nr
            tris.append([a, b, b + 1]); tris.append([a, b + 1, a + 1])
    verts = [to_world(p[0], p[1], sign) for p in pts]
    faces = [t[::-1] if sign < 0 else t for t in tris]
    me = bpy.data.meshes.new(f'Wing_{side}')
    me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            px, py = pts[me.loops[li].vertex_index]
            uv.data[li].uv = ((px - x0) / (x1 - x0), 1.0 - (py - y0) / (y1 - y0))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat_names['a'])
    obj = bpy.data.objects.new(f'Flying_Wing_{side}', me); bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    for seg in SEGMENTS:
        obj.vertex_groups.new(name=f'Wing_{side}_{seg}')
    for vi, p in enumerate(pts):
        d = {seg: seg_dist(p, *SEGMENTS[seg]) for seg in SEGMENTS}
        if p[0] > ROOT_PX:                              # root strip follows the back
            d = {'Root': 0.0}
        wts = {seg: 1.0 / (dist * dist + 12.0 ** 2) for seg, dist in d.items()}
        top = sorted(wts.items(), key=lambda kv: -kv[1])[:3]
        tot = sum(v for _, v in top)
        for seg, v in top:
            obj.vertex_groups[f'Wing_{side}_{seg}'].add([vi], v / tot, 'REPLACE')
    mod = obj.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
    print('WING', side, 'verts', len(verts), 'tris', len(faces))

for o in bpy.data.objects:
    if o.type == 'EMPTY' and o.name.startswith('Socket_'):
        print('SOCKET', o.name, o.parent_bone)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'assembled.blend'))
print('SAVED', [o.name for o in bpy.data.objects])
