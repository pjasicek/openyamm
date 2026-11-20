"""Diagnostic renders of the wing root (Blender): faces coloured by material set (body grey, wings blue) and by the
summed weight of the wing bones (red = 1), at chosen clip frames from behind/side, for a .blend (v3) or the installed
cdr1 GLB. Usage: blender -b -P debug_wingroot.py -- <blend|glb> <out prefix> clip:frame ..."""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, pre, shots = a[0], a[1], a[2:]
if src.endswith('.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
else:
    bpy.ops.wm.open_mainfile(filepath=src)
o = bpy.data.objects['Body']; me = o.data; rig = next(x for x in bpy.data.objects if x.type == 'ARMATURE')
for x in bpy.data.objects:
    if x.type == 'MESH' and x is not o: x.hide_render = True
wing = [g.index for g in o.vertex_groups if 'Wing' in g.name]
col = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
slot = {}
for p in me.polygons:
    for v in p.vertices: slot.setdefault(v, set()).add(p.material_index)
wn = [m.name for m in me.materials]
for v in me.vertices:
    w = sum(g.weight for g in v.groups if g.group in wing)
    isw = any('Wing' in wn[s] for s in slot.get(v.index, ()))
    col.data[v.index].color = (min(1, w), .25 + .35 * (not isw), .25 + .6 * isw, 1)
if '--memb' in a:
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent)); import wing_classes
    wing_classes.classify(o, rig)
    mb = me.attributes['membrane'].data; vm = {}
    for p in me.polygons:
        for v in p.vertices: vm[v] = max(vm.get(v, 0), mb[p.index].value) if p.material_index == 2 else vm.get(v, 0)
    for v in me.vertices:
        w = sum(g.weight for g in v.groups if g.group in wing); isw = any('Wing' in wn[s_] for s_ in slot.get(v.index, ()))
        col.data[v.index].color = (min(1, w), .8 * vm.get(v.index, 0), .9 if isw and not vm.get(v.index, 0) else .1, 1)
TEX = '--tex' in shots; shots = [x for x in shots if not x.startswith('--')]
if not TEX:
    m = bpy.data.materials.new('dbg'); m.use_nodes = True; nt = m.node_tree; at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'dbg'
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(at.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs[0])
    me.materials.clear(); me.materials.append(m)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 700
w_ = bpy.data.worlds.new('W'); sc.world = w_; w_.use_nodes = True; w_.node_tree.nodes['Background'].inputs[1].default_value = 4.0 if '--tex' in a else 1.6
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.0
for s in shots:
    clip, fr = s.split(':'); act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(fr)); t = rig.matrix_world @ rig.pose.bones['RWing0'].head
    for name, d in (('back', (-0.6, 1, 0.5)), ('side', (-1, 0.2, 0.15)), ('user', (-1, 0.9, 0.2))):
        cam.location = t + Vector(d).normalized() * 10; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{pre}_{clip}{fr}_{name}.png'; bpy.ops.render.render(write_still=True)
print('DEBUG done')
