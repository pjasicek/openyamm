"""Foam ring at the waterline (the native frames paint a broad teal splash round the octopod where it rises out of
the lake). Run on work/anim_base.blend after uv.py: a slightly domed annulus (R_IN..R_OUT, the inner edge a little
above the water, the outer edge just above it) mapped onto textures/foam.png (the MM6 sea serpent's Codex foam ring,
mm6_seas_claude/references_hd/05_foam_ring.png, downsized to 512: transparent hole, ragged outer edge), its own
material slot 1 'Foam' (an alpha cut-out at export), weighted wholly to the unparented FoamRoot bone so it stays on
the water while the body bobs or sinks; anim.py spins and pulses it and shrinks it away on death. The texture's hole
(0.44 R_OUT) sits on the head's base. Joined into 'Octopod' (face attribute part 3) and saved in place."""
import bpy, bmesh, math, os
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_IN, R_OUT, Z_IN, Z_OUT, SEGMENTS, RINGS = 0.20, 0.78, 0.030, 0.006, 48, 4
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
mesh = bpy.data.objects['Octopod']; rig = bpy.data.objects['Octopod_Rig']
if 'Foam' in [m.name for m in mesh.data.materials if m]:
    raise SystemExit('foam already added')
uvname = mesh.data.uv_layers.active.name
bm = bmesh.new(); uv = bm.loops.layers.uv.new(uvname)
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
bmesh.ops.triangulate(bm, faces=bm.faces[:])
foam_me = bpy.data.meshes.new('FoamMesh'); bm.to_mesh(foam_me); bm.free()
foam = bpy.data.objects.new('FoamTmp', foam_me); bpy.context.scene.collection.objects.link(foam)
if not mesh.data.materials:
    mesh.data.materials.append(bpy.data.materials.new('Octopod_A'))
mat = bpy.data.materials.new('Foam')
foam_me.materials.append(mesh.data.materials[0]); foam_me.materials.append(mat)
for p in foam_me.polygons:
    p.material_index = 1
foam_me.attributes.new('part', 'INT', 'FACE')
for i in range(len(foam_me.polygons)):
    foam_me.attributes['part'].data[i].value = 3
foam.vertex_groups.new(name='FoamRoot').add(list(range(len(foam_me.vertices))), 1.0, 'REPLACE')
for o in bpy.context.view_layer.objects:
    o.select_set(o in (mesh, foam))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('FOAM ring added: faces', len(foam_me.polygons) if foam_me.name in bpy.data.meshes else RINGS * SEGMENTS * 2,
      'materials', [m.name for m in mesh.data.materials], 'uv', uvname)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
print('SAVED anim_base.blend')
