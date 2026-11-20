"""Apply the xatlas UVs and the baked paint to a boss shell: material <Boss>_Shell (base colour, glow mask as emission
for the preview; the runtime glow is set by claude_shared/emission.py). Usage (Blender): shell_material.py <boss>
[glow_rgb]. Reads work/<boss>/shell_rig.blend + shell_uv.npz + textures/<boss>_shell_*.png; saves shell_tex.blend."""
import bpy, sys
import numpy as np
from pathlib import Path

args = sys.argv[sys.argv.index('--') + 1:]
boss = args[0]
glow_rgb = [float(x) for x in args[1].split(',')] if len(args) > 1 else [1.0, 0.42, 0.1]
P = Path(__file__).resolve().parents[1]
W = P / 'work' / boss
bpy.ops.wm.open_mainfile(filepath=str(W / 'shell_rig.blend'))
shell = bpy.data.objects['Shell']; me = shell.data
uv = np.load(W / 'shell_uv.npz')['uv']
assert len(me.polygons) == len(uv) and all(len(p.vertices) == 3 for p in me.polygons)
for l in list(me.uv_layers):
    me.uv_layers.remove(l)
layer = me.uv_layers.new(name='UVMap')
# per polygon corner: loop_triangles order is polygon order; match the corner vertices
me.calc_loop_triangles()
lt = np.array([tuple(t.vertices) for t in me.loop_triangles])
data = np.zeros((len(me.loops), 2))
for pi, p in enumerate(me.polygons):
    tri = list(lt[pi])
    for k, li in enumerate(range(p.loop_start, p.loop_start + 3)):
        data[li] = uv[pi][tri.index(me.loops[li].vertex_index)]
layer.data.foreach_set('uv', data.ravel())
name = boss.title().replace('_', '') + '_Shell'
m = bpy.data.materials.new(name); m.use_nodes = True
nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
# the projection bake's maps when present (transfer_tex.py replaces them with the retexture's)
if (P / f'textures/{boss}_shell_base.png').exists():
    base = nt.nodes.new('ShaderNodeTexImage')
    base.image = bpy.data.images.load(str(P / f'textures/{boss}_shell_base.png'))
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Metallic'].default_value = 0.0
me.materials.clear(); me.materials.append(m)
m.use_backface_culling = False
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'shell_tex.blend'))
print('MATERIAL', name)
