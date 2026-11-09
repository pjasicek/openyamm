"""v2 bake source (Blender): the v1 textured mesh (work/textured_master.blend, reduced v1 layout with the Meshy body
and head retextures) moved into the v2 frame (scripts/straighten.py coordinates), keeping only the kept +X side
(faces with a centre at x >= -1 mm) and no v1 wing faces. Materials emit the raw Meshy maps (body 4K, head 2K) and
carry their normal maps, for Cycles selected-to-active bakes onto the new UV layout (scripts/bake_v2.py).
Usage: make_bake_source.py -- <straight.npy> <out.blend>"""
import bpy, bmesh, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/textured_master.blend'))
rig = bpy.data.objects['Rig']; o = bpy.data.objects['Body']
o.modifiers.clear(); o.parent = None; bpy.data.objects.remove(rig, do_unlink=True)
me = o.data; co = np.load(a[0]); me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
bm = bmesh.new(); bm.from_mesh(me)
dead = [f for f in bm.faces if f.material_index == 2 or f.calc_center_median().x < -.001]
bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free()
for slot, label in [(0, 'body'), (1, 'head')]:
    mat = me.materials[slot]; mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfDiffuse')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(P / f'meshy/{label}_retexture_v1/texture_urls_0_base_color.png'))
    nrm = nt.nodes.new('ShaderNodeTexImage'); nrm.image = bpy.data.images.load(str(P / f'meshy/{label}_retexture_v1/texture_urls_0_normal.png'))
    nrm.image.colorspace_settings.name = 'Non-Color'
    # Meshy normal maps are +Y down (DirectX); flip green for Blender's OpenGL convention
    sep = nt.nodes.new('ShaderNodeSeparateColor'); inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.
    comb = nt.nodes.new('ShaderNodeCombineColor'); nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nrm.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Red'], comb.inputs['Red'])
    nt.links.new(sep.outputs['Green'], inv.inputs[1]); nt.links.new(inv.outputs[0], comb.inputs['Green']); nt.links.new(sep.outputs['Blue'], comb.inputs['Blue'])
    nt.links.new(comb.outputs['Color'], nm.inputs['Color'])
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
o.name = 'BakeSource'; bpy.ops.wm.save_as_mainfile(filepath=a[1]); print('BAKE_SOURCE', len(me.polygons))
