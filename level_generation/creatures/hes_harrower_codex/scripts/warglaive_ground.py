"""Ground models of Vreth's relic pair (2026-10-24): his glaive (work/warglaive_vreth_baked.blend, the same mesh as the
held one) lying face up on the ground, as the Hesper ground items are exported (Y-up glTF, world units, resting on
y = 0, one node): 160 units long (a 1.2 m blade at the ground items' 1.25 x, GROUND_ITEM_3D_PLAYBOOK), its own baked
texture set (warglaives/vreth/tex: base colour, normal, metal-roughness) on the plate faces and an orange-white
emissive material on the glow ribbons. Vreth's Last Cut, the left glaive, is the right one mirrored through its face.
Writes warglaives/ground/hes_vreths_{first,last}_cut_export.glb. Args: none"""
from pathlib import Path
import bpy, bmesh
from mathutils import Matrix
P = Path(__file__).resolve().parents[1]
OUT = P / 'warglaives' / 'ground'; OUT.mkdir(parents=True, exist_ok=True)
TEX = P / 'warglaives' / 'vreth' / 'tex'
LENGTH_UNITS = 160.0
GLOW = (1.0, 0.8, 0.55, 1.0)


def plate_material():
    m = bpy.data.materials.new('vreth_glaive'); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    def tex(name, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(str(TEX / name)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex('basecolor.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('normal.png', 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex('metal_rough.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


def glow_material():
    m = bpy.data.materials.new('vreth_glaive_glow'); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = GLOW; bsdf.inputs['Emission Color'].default_value = GLOW
    bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


for name, mirror in (('hes_vreths_first_cut', False), ('hes_vreths_last_cut', True)):
    bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'warglaive_vreth_baked.blend'))
    ob = bpy.data.objects['Warglaive_vreth']; me = ob.data
    for other in [o for o in bpy.data.objects if o != ob]:
        bpy.data.objects.remove(other)
    zs = [v.co.z for v in me.vertices]; s = LENGTH_UNITS / (max(zs) - min(zs))
    # glaive frame: long axis Z, faces +-Y -> Blender: long axis X, faces +-Z (up), so it lies flat
    lay = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0))).to_4x4() @ Matrix.Scale(s, 4)
    if mirror:
        lay = lay @ Matrix.Diagonal((1, -1, 1, 1))
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=lay, verts=bm.verts)
    if mirror:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    zmin = min(v.co.z for v in bm.verts)
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]
    bmesh.ops.translate(bm, verts=bm.verts, vec=(-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -zmin))
    bm.to_mesh(me); bm.free()
    me.materials[0] = plate_material(); me.materials[1] = glow_material()
    ob.name = me.name = name
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}_export.glb'), export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_extras=False)
    print('GROUND', name, 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'scale', round(s, 2), flush=True)
