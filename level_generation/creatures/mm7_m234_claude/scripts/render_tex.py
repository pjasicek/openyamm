"""Textured workbench renders of the rest pose: body faces with the body base colour (UVMap), head faces optionally
with the head base colour (HeadUV). Args: -- <blend> <body png> <tag> [head png]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, body_png, tag = a[:3]; head_png = a[3] if len(a) > 3 else None
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']; me = b.data
rig.animation_data_create(); rig.animation_data.action = None
def mat(name, png, uv):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(png))
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv
    nt.links.new(u.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    nt.nodes.active = t
    return m
me.materials.clear(); me.materials.append(mat('body', body_png, 'UVMap'))
if head_png:
    me.materials.append(mat('head', head_png, 'HeadUV'))
    h = me.attributes['head'].data
    for p in me.polygons:
        p.material_index = h[p.index].value
    # Workbench samples every material through the ACTIVE UV layer (the UV Map node is ignored): merge the head UVs into
    # one layer for the preview, as the runtime export does
    mg = me.uv_layers.new(name='Merged'); b_, h_ = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data
    for p in me.polygons:
        for li in p.loop_indices:
            mg.data[li].uv = (h_ if h[p.index].value else b_)[li].uv
    me.uv_layers.active = mg; mg.active_render = True
scene = bpy.context.scene; common.workbench_clay(scene, textured=True)
out = os.path.join(common.REVIEW, tag)
common.render_views(out, 1.0, 2.2, views=('front', 'three_quarter', 'left', 'back'), resolution=(1100, 800))   # m150: the wingspan
common.render_views(out + '_head', 1.6, 0.42, views=('front', 'three_quarter', 'left'), resolution=(400, 400))
