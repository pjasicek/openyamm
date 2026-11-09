"""Rest-pose textured renders of work/uv_master.blend with a base colour image (Workbench, texture colour).
Args: <basecolor relative to project> <out prefix> [blend] [clip frame]."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
img_path, out = a[:2]
blend = a[2] if len(a) > 2 else 'work/uv_master.blend'
pose = a[3:5] if len(a) > 4 else None
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, blend))
import common_bat as C
mesh = bpy.data.objects['Bat']; rig = bpy.data.objects['Bat_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
if pose:
    rig.animation_data.action = bpy.data.actions[pose[0]]; bpy.context.scene.frame_set(int(pose[1]))
mat = bpy.data.materials.new('prev'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(HERE, img_path))
nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
cells = []
for view, loc, tgt, sc in (('front', (0, -1.6, 0.1), (0, 0, 0.08), 1.05), ('quarter', (-1.0, -1.1, 0.7), (0, 0, 0.08), 1.05),
                           ('top', (0, 0.01, 1.6), (0, 0, 0.0), 1.05), ('head', (-0.3, -0.9, 0.2), (0.02, -0.12, 0.06), 0.3),
                           ('under', (0.0, -0.3, -1.4), (0, 0, 0.05), 1.05), ('back', (0.3, 1.6, 0.4), (0, 0, 0.08), 1.05)):
    p = os.path.join(HERE, f'{out}_{view}.png'); C.render_ortho(loc, tgt, sc, p, res=(700, 525), textured=True); cells.append(p)
C.sheet(os.path.join(HERE, f'{out}_sheet.png'), cells, 2)
print('PREVIEW')
