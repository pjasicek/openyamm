"""v2 bakes onto the new UV layout (Blender, Cycles CPU).

Selected-to-active from the straightened v1 Meshy-textured mesh (scripts/make_bake_source.py) onto the +X half of the
new body and head faces (the -X half shares those texels): raw Meshy base colour (DIFFUSE colour pass), tangent
normal including the Meshy normal map, and a hit mask (emission) marking texels whose rays found the source (the
rebuilt shoulder and the mirrored midline may miss; compose fills them from the nearest hit). AO is baked on the
whole new mesh at rest for all three domains (1K, 12 mm distance, as v1).
Usage: bake_v2.py -- <uv.blend> <bake_source.blend> <outdir>"""
import bpy, bmesh, sys
from pathlib import Path
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = Path(a[2]); out.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
if sc.world is None: sc.world = bpy.data.worlds.new('World')

# target: +X half of body and head faces, unrigged copy
tgt = body.copy(); tgt.data = body.data.copy(); tgt.name = 'Target'; sc.collection.objects.link(tgt)
tgt.parent = None; tgt.modifiers.clear(); tgt.matrix_world = body.matrix_world.copy()
bm = bmesh.new(); bm.from_mesh(tgt.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == 2 or f.calc_center_median().x < -1e-7], context='FACES')
bm.to_mesh(tgt.data); bm.free()
slots = [p.material_index for p in tgt.data.polygons]
tgt.data.materials.clear()                      # (resets every polygon's material index)
mats = {}
for label in ('body', 'head'):
    m = bpy.data.materials.new('T_' + label); m.use_nodes = True; tgt.data.materials.append(m); mats[label] = m
for f, src in zip(tgt.data.polygons, slots): f.material_index = 1 if src == 1 else 0

with bpy.data.libraries.load(a[1], link=False) as (avail, sel): sel.objects = ['BakeSource']
srcobj = sel.objects[0]; sc.collection.objects.link(srcobj)

def images(kind, size, colour=(0, 0, 0, 0)):
    ims = {}
    for label, m in mats.items():
        im = bpy.data.images.new(f'{label}_{kind}', size, size, alpha=True, float_buffer=kind == 'normal'); im.generated_color = colour
        if kind == 'normal': im.colorspace_settings.name = 'Non-Color'
        nt = m.node_tree; node = nt.nodes.new('ShaderNodeTexImage'); node.image = im; nt.nodes.active = node; ims[label] = im
    return ims

def save(ims, kind):
    for label, im in ims.items():
        im.filepath_raw = str(out / f'{label}_{kind}.png'); im.file_format = 'PNG'; im.save()

for ob in sc.objects: ob.select_set(ob in (tgt, srcobj))
bpy.context.view_layer.objects.active = tgt; body.hide_render = True
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = .006; bk.max_ray_distance = .03; bk.margin = 0
ims = images('color', 2048); bk.use_pass_direct = False; bk.use_pass_indirect = False; bk.use_pass_color = True
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}); save(ims, 'color'); print('BAKED color', flush=True)
ims = images('normal', 2048, (.5, .5, 1, 0)); bpy.ops.object.bake(type='NORMAL'); save(ims, 'normal'); print('BAKED normal', flush=True)
# hit mask: the source emits white
for slot in srcobj.data.materials:
    nt = slot.node_tree; em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1)
    outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); nt.links.new(em.outputs[0], outn.inputs['Surface'])
ims = images('hit', 2048); bpy.ops.object.bake(type='EMIT'); save(ims, 'hit'); print('BAKED hit', flush=True)

# AO on the whole new mesh, all domains (wings included)
bpy.data.objects.remove(tgt, do_unlink=True); bpy.data.objects.remove(srcobj, do_unlink=True); body.hide_render = False
sc.world.light_settings.distance = .012; bk.use_selected_to_active = False; bk.margin = 8
ao = {}
for slot, label in enumerate(['body', 'head', 'wings']):
    im = bpy.data.images.new('AO_' + label, 1024, 1024, alpha=False); m = body.data.materials[slot]; m.use_nodes = True
    node = m.node_tree.nodes.new('ShaderNodeTexImage'); node.image = im; m.node_tree.nodes.active = node; ao[label] = im
for ob in sc.objects: ob.select_set(ob == body)
bpy.context.view_layer.objects.active = body; sc.cycles.samples = 24
bpy.ops.object.bake(type='AO')
for label, im in ao.items(): im.filepath_raw = str(out / f'{label}_ao_1k.png'); im.file_format = 'PNG'; im.save()
print('BAKED ao')
