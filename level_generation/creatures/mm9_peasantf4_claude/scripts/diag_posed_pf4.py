"""Posed diagnostic renders of a PF4 GLB (job 8 follow-up): every material keeps its base colour texture, back faces are magenta (what the
one-sided viewer culls), LOD0 only. Views in Blender world space after import (Z up, the model faces -Y, her left arm at -X after the
mirror; check the first render). Args (after --): <glb> <out prefix> <clip:seconds,...> <views: name=cx,cy,cz/tx,ty,tz/ortho;...> [size]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items, views = a[0], a[1], a[2].split(','), a[3]
size = int(a[4]) if len(a) > 4 else 600
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        bpy.data.objects.remove(o, do_unlink=True)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    pr = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    lk = pr.inputs['Base Color'].links if pr else []
    tex = lk[0].from_node if lk else None
    while tex is not None and tex.type != 'TEX_IMAGE':
        ins = [i for i in tex.inputs if i.links]; tex = ins[0].links[0].from_node if ins else None
    geo = nt.nodes.new('ShaderNodeNewGeometry'); mix = nt.nodes.new('ShaderNodeMixShader'); d = nt.nodes.new('ShaderNodeBsdfDiffuse')
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (1, 0, 1, 1)
    if tex: nt.links.new(tex.outputs['Color'], d.inputs['Color'])
    nt.links.new(geo.outputs['Backfacing'], mix.inputs['Fac']); nt.links.new(d.outputs[0], mix.inputs[1]); nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outn.inputs['Surface'])
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.35, 0.37, 0.4, 1); bg.inputs['Strength'].default_value = 0.6
sc.render.resolution_x = sc.render.resolution_y = size
import math
for i, (rot, en) in enumerate((((50, 0, 200), 3.0), ((60, 0, 20), 1.5), ((-40, 0, 100), 1.0))):
    ld = bpy.data.lights.new(f'L{i}', 'SUN'); ld.energy = en; lo = bpy.data.objects.new(f'L{i}', ld)
    lo.rotation_euler = [math.radians(x) for x in rot]; sc.collection.objects.link(lo)
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.clip_start = 0.001; cd.clip_end = 30
for it in items:
    clip, t = it.split(':')
    act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * 24.0; sc.frame_set(int(fr), subframe=fr % 1.0); bpy.context.view_layer.update()
    for v in views.split(';'):
        nm, spec = v.split('='); c_, t_, o_ = spec.split('/')
        cam.location = Vector([float(x) for x in c_.split(',')]); tgt = Vector([float(x) for x in t_.split(',')])
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = float(o_)
        sc.render.filepath = f'{out}_{clip}{t}_{nm}.png'; bpy.ops.render.render(write_still=True)
print('POSED', out)
