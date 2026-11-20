"""Add the procedural ram horns (horn_geom.py) to a rigged blend: one 'Horns' mesh (both sides), rigid on Xheadpiv
like MM9's `ramhorn` piece, UV 'UVMap' = the horn layout, smooth shaded, material 'RamHorn' (textures from
compose_horn.py when they exist).

Args: <in blend (armature 'MM9_Rig' or '<Name>_Rig')> <out blend> <lift metres> [report json]
lift: the rig blend's z offset from the MM9 bind (mm9_rig_source.py lift), so the horns follow the same lift.
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horn_geom as H

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, LIFT = argv[0], argv[1], float(argv[2])
REP = argv[3] if len(argv) > 3 else None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
old = bpy.data.objects.get('Horns')
if old:
    bpy.data.objects.remove(old)
me = bpy.data.meshes.new('Horns')
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
info = {}
for side in (-1, 1):
    V, T, UV, info = H.build(side)
    V = V + np.array([0, 0, LIFT])
    vs = [bm.verts.new(tuple(p)) for p in V]
    for tri, uvs in zip(T, UV):
        f = bm.faces.new([vs[k] for k in tri])
        for loop, uv in zip(f.loops, uvs):
            loop[uvl].uv = tuple(uv)
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
ob = bpy.data.objects.new('Horns', me)
bpy.context.scene.collection.objects.link(ob)
g = ob.vertex_groups.new(name='Xheadpiv')
g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
ob.parent = rig
ob.matrix_parent_inverse = rig.matrix_world.inverted()
mod = ob.modifiers.new('Armature', 'ARMATURE')
mod.object = rig
mat = bpy.data.materials.new('RamHorn')
mat.use_nodes = True
mat.use_backface_culling = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex_dir = os.path.join(HERE, 'textures')
base = os.path.join(tex_dir, 'ramhorn_basecolor.png')
if os.path.exists(base):
    def tex(path, cs):
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = tex(os.path.join(tex_dir, 'ramhorn_normal_1k.png'), 'Non-Color')
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    mr = tex(os.path.join(tex_dir, 'ramhorn_metal_rough_1k.png'), 'Non-Color')
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
else:
    bsdf.inputs['Base Color'].default_value = (0.08, 0.07, 0.05, 1)
me.materials.append(mat)
info.update({'verts': len(me.vertices), 'tris': len(me.polygons)})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
if REP:
    json.dump(info, open(REP, 'w'), indent=1, default=float)
print('HORNS ' + json.dumps(info, default=float))
