"""Ear close-ups of a GLB in its rest pose (texture checks: foreign texels on or behind the ears, the jaw-neck line).

Args: -- <glb> <out dir> [views] [size px] [ear height fraction, default 0.45] [uv|-] [scale|auto]
Views (comma list, default rside,lside,rback,lback,party), camera yaw from the front and ortho size at scale 1:
  rside / lside   the character's right / left side at ear height (90 deg, 0.26 m)
  rear / lear     tight ear close-ups (85 deg, 0.13 m, 3 cm toward the back of the head)
  rback / lback   3/4 back (140 deg, 0.3 m)
  rlow / llow     side from 15 deg below (under the ear, 0.26 m)
  rneck / lneck   the jaw-neck line (70 deg, 10 deg below, 0.17 m)
  rprof / lprof   profile (80 deg, 0.3 m; the user's viewer shot of 2026-11-02)
  party           3/4 front from 22 deg above (35 deg, 0.55 m, head and shoulders); front (0 deg, 0.3 m)
The target is the head bone raised by the ear fraction of (head top - head bone). scale multiplies every ortho size and
offset; auto = (head top - head bone) / 0.241 m (mm9_peasantdm1's head), so other bodies frame alike (a hood or tall
hair inflates it: pass a number). EEVEE with the GLB's own maps; LOD and shadow meshes hidden. Environment EAR_HIDE=<text>:
faces whose material name contains the text are deleted before rendering (mm9_ebora: EAR_HIDE=Wing, the throat check);
EAR_BG=r,g,b sets the background colour (a see-through test). Writes
<out dir>/<view>.png. `uv`: an unlit UV pass instead (R = u, G = Blender v = 1 - glTF v, B = (material index + 1) / 10,
0 = background), written as <out dir>/<view>.exr, to map a pixel of a shot back to its texels."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]
views = (a[2] if len(a) > 2 else 'rside,lside,rback,lback,party').split(',')
size = int(a[3]) if len(a) > 3 else 420
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or 'shadow' in o.name):
        o.hide_render = True
if os.environ.get('EAR_HIDE'):
    import bmesh
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        bm = bmesh.new(); bm.from_mesh(o.data)
        bad = [f for f in bm.faces if f.material_index < len(o.data.materials) and o.data.materials[f.material_index]
               and os.environ['EAR_HIDE'] in o.data.materials[f.material_index].name]
        bmesh.ops.delete(bm, geom=bad, context='FACES'); bm.to_mesh(o.data); bm.free()
sc = bpy.context.scene
sc.frame_set(0)
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = tuple(float(v) for v in os.environ.get('EAR_BG', '0.35,0.37,0.4').split(',')) + (1,); bg.inputs['Strength'].default_value = 1.0
for nm, rot, en in (('key', (50, 0, -30), 3.0), ('fill', (60, 0, 140), 1.2), ('rim', (70, 0, 200), 0.8)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en
    lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head') and 'Ponytail' not in b.name)
tgt = (rig.matrix_world @ hb.matrix).translation
# centre on the ear height: the head mesh's vertices around the head bone (skinned rest = mesh rest here)
import numpy as np
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.hide_render:
        co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
        pts.append(co[np.linalg.norm(co[:, :2] - np.array(tgt[:2]), axis=1) < 0.2])
pts = np.concatenate(pts); pts = pts[pts[:, 2] > tgt.z - 0.05]
top = pts[:, 2].max()
EAR = float(a[4]) if len(a) > 4 else 0.45   # ear centre as a fraction from the head bone to the top
K = float(a[6]) if len(a) > 6 and a[6] != 'auto' else (top - tgt.z) / 0.241
tgt = Vector((tgt.x, tgt.y, tgt.z + (top - tgt.z) * EAR))
if len(a) > 5 and a[5] == 'uv':
    for i, m in enumerate(bpy.data.materials):
        if not m.use_nodes:
            continue
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nt.nodes.remove(n)
        o_ = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        uv, sep, comb, em = (nt.nodes.new(t) for t in ('ShaderNodeUVMap', 'ShaderNodeSeparateXYZ',
                                                        'ShaderNodeCombineXYZ', 'ShaderNodeEmission'))
        nt.links.new(uv.outputs[0], sep.inputs[0])
        nt.links.new(sep.outputs[0], comb.inputs[0])
        nt.links.new(sep.outputs[1], comb.inputs[1])
        comb.inputs[2].default_value = (i + 1) / 10.0
        nt.links.new(comb.outputs[0], em.inputs[0])
        nt.links.new(em.outputs[0], o_.inputs[0])
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Raw'
    sc.render.filter_size = 0.0
    bg.inputs['Strength'].default_value = 0
print('EARVIEWS target', tuple(round(x, 3) for x in tgt), 'head top', round(float(top), 3), 'scale', round(K, 3))
# (camera yaw deg: 0 front (the face looks to -Y), -90 the character's right side; height offset m; ortho m; pitch deg)
VIEWS = {'rside': (-90, 0, 0.26, 0), 'lside': (90, 0, 0.26, 0), 'rback': (-140, 0, 0.3, 0),
         'lback': (140, 0, 0.3, 0), 'rlow': (-90, -0.03, 0.26, -15), 'llow': (90, -0.03, 0.26, -15),
         'party': (-35, -0.08, 0.55, 22), 'front': (0, 0.02, 0.3, 0),
         'rneck': (-70, -0.07, 0.17, -10), 'lneck': (70, -0.07, 0.17, -10), 'rprof': (-80, -0.03, 0.3, 0),
         'lprof': (80, -0.03, 0.3, 0), 'rear': (-85, -0.025, 0.13, 0, 0.03), 'lear': (85, -0.025, 0.13, 0, 0.03)}
for v in views:
    ang, dz, scale, pitch = VIEWS[v][:4]
    shift = VIEWS[v][4] if len(VIEWS[v]) > 4 else 0.0     # m along the image's right (both ear views: the back)
    r, pt = math.radians(ang), math.radians(pitch)
    t = tgt + (Vector((0, 0, dz)) + Vector((math.cos(r), math.sin(r), 0)) * shift * (1 if ang < 0 else -1)) * K
    cd.ortho_scale = scale * K
    cam.location = t + Vector((math.sin(r) * math.cos(pt) * 2, -math.cos(r) * math.cos(pt) * 2, math.sin(pt) * 2))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, v + ('.exr' if len(a) > 5 and a[5] == 'uv' else '.png'))
    bpy.ops.render.render(write_still=True)
print('EARVIEWS', glb, out, ','.join(views))
