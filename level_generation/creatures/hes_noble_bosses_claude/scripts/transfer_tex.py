"""Bake a Meshy-retextured boss figure onto the shell's UVs (Cycles, selected to active).

The retexture keeps Meshy's geometry in its original coordinates; work/<boss>/figure_map.npz (fit_shell.py) maps
every welded original vertex to its aligned position on our body, so the textured figure is moved onto the shell
first. Bakes base colour (diffuse colour only), tangent-space normal (figure detail and shape onto the shell),
roughness and metallic. Usage (Blender): transfer_tex.py <boss> <retextured.glb> [res]
Writes textures/<boss>_shell_{base,normal,rough,metal}.png and work/<boss>/shell_tex.blend (material updated)."""
import bpy, bmesh, sys, os
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree

args = sys.argv[sys.argv.index('--') + 1:]
boss, src = args[0], args[1]
res = int(args[2]) if len(args) > 2 else 2048
P = Path(__file__).resolve().parents[1]
W = P / 'work' / boss
TX = P / 'textures'
bpy.ops.wm.open_mainfile(filepath=str(W / 'shell_tex.blend'))
sc = bpy.context.scene
shell = bpy.data.objects['Shell']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in new:
    o.select_set(True)
bpy.context.view_layer.objects.active = new[0]
if len(new) > 1:
    bpy.ops.object.join()
tex = bpy.context.view_layer.objects.active; tex.name = 'FigureTex'; tex.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != tex]:
    bpy.data.objects.remove(o, do_unlink=True)
fm = np.load(W / 'figure_map.npz')
orig, aligned = fm['original'], fm['aligned']
kd = KDTree(len(orig))
for i, p in enumerate(orig):
    kd.insert(p, i)
kd.balance()
co = np.array([tuple(v.co) for v in tex.data.vertices])


def umeyama(src, dst):
    ms, md = src.mean(0), dst.mean(0); s_, d_ = src - ms, dst - md
    U, S, Vt = np.linalg.svd(d_.T @ s_ / len(src)); D = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        D[2, 2] = -1
    Rm = U @ D @ Vt; c = (S * np.diag(D)).sum() / (s_ ** 2).sum(1).mean()
    return c, Rm, md - c * Rm @ ms


# the retexture may rescale/recentre the figure: bounding-box start, then similarity ICP onto the original
lo, hi = co.min(0), co.max(0); lo0, hi0 = orig.min(0), orig.max(0)
s0 = (hi0 - lo0).max() / (hi - lo).max()
co = (co - (lo + hi) / 2) * s0 + (lo0 + hi0) / 2
for it in range(40):
    idx = np.array([kd.find(p)[1] for p in co])
    c, Rm, t = umeyama(co, orig[idx]); co = c * co @ Rm.T + t
idx = np.zeros(len(co), int); dist = np.zeros(len(co))
for i, p in enumerate(co):
    _, j, d = kd.find(p); idx[i] = j; dist[i] = d
print('MAP max distance', dist.max(), 'mean', dist.mean(), 'p99', np.percentile(dist, 99))
assert np.percentile(dist, 99) < 2e-3, 'retextured geometry differs from the original figure'
# move each retextured vertex by its nearest original vertex's alignment displacement (exact where they coincide)
tex.data.vertices.foreach_set('co', (co + (aligned[idx] - orig[idx])).ravel()); tex.data.update()
for o in sc.objects:
    o.hide_render = o not in (shell, tex)
# bake setup
try:
    sc.render.engine = 'CYCLES'
except TypeError:
    pass
sc.cycles.device = 'CPU'; sc.cycles.samples = 4
bake = sc.render.bake
bake.use_selected_to_active = True; bake.cage_extrusion = 0.02; bake.max_ray_distance = 0.06; bake.margin = 8
smat = shell.data.materials[0]; nt = smat.node_tree


def target(name, colorspace):
    img = bpy.data.images.new(f'{boss}_shell_{name}', res, res, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img
    for n in nt.nodes:
        n.select = False
    node.select = True; nt.nodes.active = node
    return img, node


bpy.ops.object.select_all(action='DESELECT')
tex.select_set(True); shell.select_set(True); bpy.context.view_layer.objects.active = shell
results = {}
img, node = target('base', 'sRGB')
bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
bpy.ops.object.bake(type='DIFFUSE'); results['base'] = img
img, node = target('normal', 'Non-Color')
bake.normal_space = 'TANGENT'
bpy.ops.object.bake(type='NORMAL'); results['normal'] = img
img, node = target('rough', 'Non-Color')
bpy.ops.object.bake(type='ROUGHNESS'); results['rough'] = img
# metallic through emission on the figure's materials
for m in tex.data.materials:
    t = m.node_tree; b = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    em = t.nodes.new('ShaderNodeEmission'); out = next(n for n in t.nodes if n.type == 'OUTPUT_MATERIAL')
    if b.inputs['Metallic'].is_linked:
        t.links.new(b.inputs['Metallic'].links[0].from_socket, em.inputs['Color'])
    else:
        v = b.inputs['Metallic'].default_value; em.inputs['Color'].default_value = (v, v, v, 1)
    t.links.new(em.outputs[0], out.inputs['Surface'])
img, node = target('metal', 'Non-Color')
bpy.ops.object.bake(type='EMIT'); results['metal'] = img
for k, im in results.items():
    im.filepath_raw = str(TX / f'{boss}_shell_{k}.png'); im.file_format = 'PNG'; im.save()
stale = TX / f'{boss}_shell_base_raw.png'          # grade_gold.py snapshots the new bake next time
if stale.exists():
    stale.unlink()
# material: base + normal + roughness/metallic for the preview and the export
for n in list(nt.nodes):
    if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith(f'{boss}_shell_') and n.image not in results.values():
        pass
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
base_node = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == results['base'])
nt.links.new(base_node.outputs['Color'], bsdf.inputs['Base Color'])
nn = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == results['normal'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nn.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
rn = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == results['rough'])
nt.links.new(rn.outputs['Color'], bsdf.inputs['Roughness'])
mn = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == results['metal'])
nt.links.new(mn.outputs['Color'], bsdf.inputs['Metallic'])
bpy.data.objects.remove(tex, do_unlink=True)
for o in sc.objects:
    o.hide_render = o.name in ('Body', 'Figure')
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'shell_tex.blend'))
print('TRANSFERRED', {k: str(TX / f'{boss}_shell_{k}.png') for k in results})
