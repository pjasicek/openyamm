"""Foam collar at the waterline (the native walk/attack/hit/death frames paint turquoise foam round the base).
Run on work/rig_v1.blend after rig_seas.py: builds a slightly domed annulus round the column base (R_IN..R_OUT,
inner edge a little above the water, outer edge just above it), maps it onto textures/foam.png (the Codex top-down
foam ring, references_hd/05_foam_ring.png: transparent hole in the middle, ragged outer edge), gives it its own
material 'Foam' (alpha cut-out set in the runtime step) and an unparented 'FoamRoot' bone at the origin, so the collar
stays on the water while the body leans or sinks; anim_seas.py spins and pulses it and shrinks it away on death.
Joins it into 'Seas' (material slot 1) and saves work/rig_v1.blend in place."""
import bpy, bmesh, math, os, shutil
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_IN, R_OUT, Z_IN, Z_OUT, SEGMENTS, RINGS = 0.085, 0.33, 0.028, 0.004, 48, 4
shutil.copy(os.path.join(HERE, 'references_hd', '05_foam_ring.png'), os.path.join(HERE, 'textures', 'foam.png'))
mesh = bpy.data.objects['Seas']; rig = bpy.data.objects['Seas_Rig']

bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
grid = []
for r in range(RINGS + 1):
    f = r / RINGS; rad = R_IN + (R_OUT - R_IN) * f; z = Z_IN + (Z_OUT - Z_IN) * f
    grid.append([bm.verts.new((rad * math.cos(2 * math.pi * k / SEGMENTS), rad * math.sin(2 * math.pi * k / SEGMENTS), z))
                 for k in range(SEGMENTS)])
uv_scale = 0.49 / R_OUT
for r in range(RINGS):
    for k in range(SEGMENTS):
        face = bm.faces.new((grid[r][k], grid[r][(k + 1) % SEGMENTS], grid[r + 1][(k + 1) % SEGMENTS], grid[r + 1][k]))
        for loop in face.loops:
            loop[uv].uv = (0.5 + loop.vert.co.x * uv_scale, 0.5 + loop.vert.co.y * uv_scale)
foam_me = bpy.data.meshes.new('Foam'); bm.to_mesh(foam_me); bm.free()
foam = bpy.data.objects.new('Foam', foam_me); bpy.context.scene.collection.objects.link(foam)
mat = bpy.data.materials.new('Foam'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
img = bpy.data.images.load(os.path.join(HERE, 'textures', 'foam.png'))
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
foam_me.materials.append(mat)
for layer in mesh.data.uv_layers:
    layer.name = 'UVMap'

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
b = rig.data.edit_bones.new('FoamRoot'); b.head = Vector((0, 0, 0)); b.tail = Vector((0, 0, 0.1)); b.parent = None
bpy.ops.object.mode_set(mode='OBJECT')
foam.vertex_groups.new(name='FoamRoot').add(list(range(len(foam_me.vertices))), 1.0, 'REPLACE')
for o in bpy.context.view_layer.objects:
    o.select_set(o in (mesh, foam))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('FOAM ring added: faces', RINGS * SEGMENTS, 'materials', [m.name for m in mesh.data.materials])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
