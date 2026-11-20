"""Full-body Attack frames straight from GLBs, with the sword attachment placed on the `Sword` node as the engine
does (attachment root under the node). The node's world matrix comes from forward kinematics on the GLB itself (the
glTF importer reorients bones, so a pose bone's matrix is not the node's), converted to Blender's Z-up.
Frames count at 48 fps (the viewer's numbering).
Usage: blender -b -P attack_shots.py -- <label=glb,...> <frame,...> <out dir> [sword glb]
-> <out>/<label>_<frame>_<view>.png for the views side, front, q34 (and close: the upper body three-quarter)"""
import json, os, sys, bpy
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = args[2]; os.makedirs(out, exist_ok=True)
SWORD = args[3] if len(args) > 3 else os.path.join(HERE, '../../../assets_source/worlds/mm8/models/mm8_m456_sword.glb')
VIEWS = {'side': ((-1, 0, .08), 2.1, .85), 'front': ((0, -1, .08), 2.1, .85), 'q34': ((-.7, -.7, .25), 2.1, .85),
         'close': ((-.55, -.8, .3), 1.2, 1.15), 'legs': ((-.8, -.6, .15), 1.1, .5)}
VIEWS = {k: VIEWS[k] for k in os.environ.get('SHOT_VIEWS', ','.join(VIEWS)).split(',')}
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # glTF Y-up -> Blender Z-up


def sword_node(glb, seconds):
    doc_raw = open(glb, 'rb').read(); n = int.from_bytes(doc_raw[12:16], 'little'); doc = json.loads(doc_raw[20:20 + n])
    binary = doc_raw[28 + n:]; nodes = doc['nodes']; idx = {x.get('name'): i for i, x in enumerate(nodes)}
    parent = {c: i for i, x in enumerate(nodes) for c in x.get('children', [])}
    anim = next(a for a in doc['animations'] if a['name'] == 'Attack')

    def acc(i):
        a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.frombuffer(binary, '<f4', a['count'] * k, v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], k)
    ch = {(c['target']['node'], c['target']['path']): anim['samplers'][c['sampler']] for c in anim['channels']}

    def val(j, path, t):
        if (j, path) not in ch:
            return np.array(nodes[j].get(path, {'rotation': [0, 0, 0, 1], 'translation': [0, 0, 0], 'scale': [1, 1, 1]}[path]))
        ts = acc(ch[(j, path)]['input'])[:, 0]; vs = acc(ch[(j, path)]['output'])
        k = int(np.clip(np.searchsorted(ts, t, side='right') - 1, 0, len(ts) - 1))
        if k >= len(ts) - 1:
            return vs[-1]
        f = (t - ts[k]) / (ts[k + 1] - ts[k]); a, b = vs[k].astype(float), vs[k + 1].astype(float)
        if path == 'rotation' and a @ b < 0:
            b = -b
        q = a * (1 - f) + b * f
        return q / np.linalg.norm(q) if path == 'rotation' else q
    i = idx['Sword']; chain = [i]
    while chain[-1] in parent:
        chain.append(parent[chain[-1]])
    M = Matrix.Identity(4)
    for j in reversed(chain):
        x, y, z, w = val(j, 'rotation', seconds)
        L = Matrix.LocRotScale(Vector(val(j, 'translation', seconds)), __import__('mathutils').Quaternion((w, x, y, z)),
                               Vector(val(j, 'scale', seconds)))
        M = M @ L
    return C @ M @ C.inverted()


for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb), bone_heuristic='BLENDER')
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
            o.hide_render = True
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(SWORD))
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    for o in new:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
            o.hide_render = True
    local = {o: o.matrix_world.copy() for o in roots}
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    rig.animation_data.action = bpy.data.actions['Attack']
    for fr in args[1].split(','):
        f = float(fr) * sc.render.fps / 48.0
        sc.frame_set(int(f), subframe=f - int(f)); bpy.context.view_layer.update()
        node = sword_node(os.path.abspath(glb), float(fr) / 48.0)
        for o in roots:
            o.matrix_world = node @ local[o]
        bpy.context.view_layer.update()
        for view, (d, size, h) in VIEWS.items():
            c = Vector((0, 0, h)); cam.location = c + Vector(d).normalized() * 5
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size; cam.data.clip_end = 20
            sc.render.filepath = os.path.join(out, f'{label}_{fr}_{view}.png'); bpy.ops.render.render(write_still=True)
print('ATTACKSHOTS done')
