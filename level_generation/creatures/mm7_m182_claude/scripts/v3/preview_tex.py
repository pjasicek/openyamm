"""Textured preview of work/v3/uv_master.blend with given body/head/wings base colour maps on UVMap (runtime
layouts), rendered from a render.py spec. Usage: blender -b -P preview_tex.py -- <body.png> <head.png> <wings.png> <spec.json> [out.blend]"""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[2]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data
slots = [p.material_index for p in me.polygons]
me.materials.clear()
for name, img in zip(['TBody', 'THead', 'TWings'], a[:3]):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(Path(img).resolve())); u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = 'UVMap'
    nt.links.new(u.outputs[0], t.inputs[0]); nt.links.new(t.outputs[0], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = .8
    me.materials.append(m)
for p in me.polygons: p.material_index = slots[p.index]
if len(a) > 4: bpy.ops.wm.save_as_mainfile(filepath=str(Path(a[4]).resolve()))
sys.argv = [sys.argv[0], '--', str(P / 'work/v3/__inline__'), a[3]]
spec = json.load(open(a[3])); sc = bpy.context.scene; rig = bpy.data.objects['Rig']
sc.render.engine = 'BLENDER_EEVEE'; w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (.35, .35, .37, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sun = bpy.data.objects.new('K', bpy.data.lights.new('K', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.5; sun.rotation_euler = (0.7, 0.2, -0.6)
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 100
Path(spec['out']).mkdir(parents=True, exist_ok=True)
for s in spec['shots']:
    if s.get('clip'):
        act = bpy.data.actions[s['clip']]; rig.animation_data.action = act
        if len(act.slots): rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(s.get('frame', 0)))
    else:
        if rig.animation_data: rig.animation_data.action = None
        for b in rig.pose.bones: b.matrix_basis.identity()
        sc.frame_set(0)
    res = s.get('res', spec.get('res', [1000, 800])); sc.render.resolution_x, sc.render.resolution_y = res
    t = rig.matrix_world @ rig.pose.bones[s['track']].head + Vector(s.get('offset', [0, 0, 0])) if s.get('track') else Vector(s['target'])
    cam.location = t + Vector(s['dir']).normalized() * 20; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = s['scale']
    sc.render.filepath = str(Path(spec['out']) / (s['name'] + '.png')); bpy.ops.render.render(write_still=True)
print('PREVIEW', len(spec['shots']))
