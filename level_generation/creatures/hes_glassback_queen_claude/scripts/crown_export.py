"""(Copied from hes_glassback_claude/scripts/crest_export.py.) Export the Queen's glass pieces with their LODs as static
GLBs in the rig's rest space (glTF Y-up), for crown_post.py: the crown (Crown_Head) and the tall crest on Spine1-3 and
Tail1 (no Neck1: the bare neck below the crown; Spine3 trimmed by crown.py) ->
work/crest_raw/hes_glassback_queen_<crown|crest>_<bone>.glb. Args: -- <crown.blend>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
T = C.path('textures')
glass = bpy.data.materials['Glass']; glass.use_nodes = True; nt = glass.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
img = bpy.data.images.load(os.path.join(T, 'hgb_glass_basecolor_512.png'))
tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = img; nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
mr = bpy.data.images.load(os.path.join(T, 'hgb_glass_metal_rough_256.png')); mr.colorspace_settings.name = 'Non-Color'
tm = nt.nodes.new('ShaderNodeTexImage'); tm.image = mr; sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tm.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
glow = bpy.data.materials['Glow']; glow.use_nodes = True
gb = next(n for n in glow.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
gb.inputs['Base Color'].default_value = (0, 0, 0, 1)
gb.inputs['Emission Color'].default_value = (0.42, 0.68, 1.0, 1); gb.inputs['Emission Strength'].default_value = 1.0
os.makedirs(C.path('work/crest_raw'), exist_ok=True)
groups = {}
for o in bpy.data.objects:
    base = o.name.split('_LOD')[0]
    if base == 'Crown_Head' or base in ('Crest_tall_Spine1', 'Crest_tall_Spine2', 'Crest_tall_Spine3', 'Crest_tall_Tail1'):
        groups.setdefault(base, []).append(o)
for base, objs in sorted(groups.items()):
    copies = []
    for o in objs:
        c = bpy.data.objects.new(o.name + '_x', o.data.copy())
        bpy.context.scene.collection.objects.link(c)
        c.matrix_world = o.matrix_world.copy()
        copies.append((o, c))
    for o, c in copies:
        name = o.name
        o.name = name + '_src'
        c.name = name
    for ob in bpy.data.objects:
        ob.select_set(any(ob is c for _, c in copies))
    out = C.path('work/crest_raw/hes_glassback_queen_' + ('crown_head' if base == 'Crown_Head' else 'crest_' + base[11:].lower()) + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_apply=True)
    for o, c in copies:
        bpy.data.objects.remove(c, do_unlink=True)
        o.name = o.name[:-4]
    print('CREST_EXPORT', os.path.basename(out), len(objs), 'levels')
