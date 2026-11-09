"""Right-temple view from below (ring view 270/-20) of a per-LOD GLB with the bandanna piece (HIDE_GROUPS, default 3) removed, flat base colour,
magenta background: tells a skin hole (background shows) from skin faces painted green.
Usage: blender -b -P hide_band.py -- <label> <level> [az el] -> review/temple/noband_<label>_<level>_<az>_<el>.png"""
import math, os, sys, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; label, level = a[:2]; az, el = (int(a[2]), int(a[3])) if len(a) > 3 else (270, -20)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{level}.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects[os.environ.get('REA_NODE', 'PirateCrossbowwoman')]
import numpy as np
from mathutils.kdtree import KDTree
src = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); g = np.load(os.path.join(HERE, 'work', 'groups.npy'))
sc_cen = src['verts'][src['faces']].mean(1); kd = KDTree(len(sc_cen))
for i, p in enumerate(sc_cen):
    kd.insert(p, i)
kd.balance()
# bandanna faces: the nearest source face centre (rest pose) is a bandanna face (group 3)
bm = bmesh.new(); bm.from_mesh(body.data); mw = body.matrix_world
HIDE = {int(x) for x in os.environ.get('HIDE_GROUPS', '3').split(',')}
band = [f for f in bm.faces if g[kd.find(mw @ f.calc_center_median())[1]] in HIDE]
print('BAND faces', len(band), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=band, context='FACES'); bm.to_mesh(body.data); bm.free()
if os.environ.get('REST'):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    # open boundary loops of the welded source above the neck, drawn as red wire (rest pose)
    v, f = src['verts'], src['faces']
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1)
    u, cnt = np.unique(e, axis=0, return_counts=True); b = u[(cnt == 1) & (v[u[:, 0], 2] > 1.45)]
    me = bpy.data.meshes.new('Open'); me.from_pydata(v.tolist(), b.tolist(), []); ob = bpy.data.objects.new('Open', me)
    sc.collection.objects.link(ob); mod = ob.modifiers.new('W', 'WIREFRAME'); mod.thickness = 0.0006
    red = bpy.data.materials.new('Red'); red.use_nodes = True; nt = red.node_tree
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 0, 0, 1)
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface']); me.materials.append(red)
    sk = bmesh.new(); sk.from_mesh(me); sk.free()
else:
    rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
for m in bpy.data.materials:
    if m.use_nodes:
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        if bsdf and bsdf.inputs['Base Color'].links:
            em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(bsdf.inputs['Base Color'].links[0].from_socket, em.inputs['Color'])
            nt.links.new(em.outputs[0], outn.inputs['Surface'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('ORTHO', '.15'))
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 0, 1, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 450
bpy.context.view_layer.update(); c = rig.matrix_world @ rig.pose.bones['B_Head'].head + Vector(tuple(float(x) for x in os.environ.get('TARGET', '-.04,-.03,.07').split(',')))
d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
cam.location = c + d * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
os.makedirs(os.path.join(HERE, 'review', 'temple'), exist_ok=True)
sc.render.filepath = os.path.join(HERE, 'review', 'temple', f'noband_{label}_{level}_{az}_{el}' + ('_rest' if os.environ.get('REST') else '') + os.environ.get('SUFFIX', '') + '.png'); bpy.ops.render.render(write_still=True)
