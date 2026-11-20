"""Deformation-aware reduction of the 20k hydra (as mm6_seas_claude): the mesh is decimated while posed in a tight
S wave (every ring curved), each vertex's rest position carried as an interpolated point attribute and restored after.
Rest-pose decimation removes the rings of the straight column, and the slivers fold when the body bends. Edges folded
more than SHARP_DEG (spike and claw tips, teeth, crest) and the five heads keep full density; protecting the whole head kept a third of
the mesh (teeth, claws, crown) at full density and floored the result at 13.8k.
Run on work/rig_20k.blend (rig_hyd.py on hd_base, copied):
  blender --background work/rig_20k.blend --python scripts/reduce_bent.py -- <target triangles> <out.blend> [head triangles]"""
import bpy, bmesh, math, os, sys
os.environ.setdefault('HYD_RIG_JSON', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'rig_20k.json'))
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_hyd as A
import hyd_parts as H

args = sys.argv[sys.argv.index('--') + 1:]
TARGET, OUT = int(args[0]), args[1]
HEAD_TRIS = int(args[2]) if len(args) > 2 else 7500           # all five heads together
SHARP_DEG = 90.0
mesh = bpy.data.objects['Hydra']
rest = np.array([tuple(v.co) for v in mesh.data.vertices])
# bent pose: tail in an S wave, every neck pitched forward and yawed to alternating sides, heads pitched, so every
# ring of the body and the necks is curved
P = A.pose(0.2, dict(amp=0.45, speed=1.0),
           lambda k, n, t: (A.profile(k, 0.45, 1.0), A.profile(k, 0.4 * (1 if k % 2 else -1), 1.0), 0.3, 0.0))
A.apply(P); bpy.context.view_layer.update()
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
posed = bpy.data.meshes.new_from_object(ev)
work = bpy.data.objects.new('Bent', posed); bpy.context.scene.collection.objects.link(work)
att = posed.attributes.new('rest_co', 'FLOAT_VECTOR', 'POINT'); att.data.foreach_set('vector', rest.ravel())
# keep group from the rest geometry (same vertex order)
bm = bmesh.new(); bm.from_mesh(mesh.data); sharp = np.zeros(len(rest))
for e in bm.edges:
    if len(e.link_faces) == 2:
        a = math.degrees(e.calc_face_angle())
        for x in e.verts:
            sharp[x.index] = max(sharp[x.index], a)
bm.free()
for g in list(work.vertex_groups):
    work.vertex_groups.remove(g)
keep = work.vertex_groups.new(name='keep')
# heads keep Meshy's full density (CLAUDE_CREATURE_TEXTURES.md, Head detail: reduce outside the head); at 10k overall
# they kept ~450 triangles each and read crumpled
adj = [[] for _ in rest]
for e in mesh.data.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
heads = H.head_part(rest, H.owners(mesh, A.D['chains']), A.D['chains'], H.HEAD_BACK + 0.02)   # the flood leaks on the 20k mesh
keep.add([int(i) for i in np.nonzero((sharp > SHARP_DEG) | (heads > 0))[0]], 1.0, 'REPLACE')
print('HEAD vertices kept', int((heads > 0).sum()), 'of', len(rest))
for o in bpy.context.view_layer.objects:
    o.select_set(o is work)
bpy.context.view_layer.objects.active = work
heads_group = work.vertex_groups.new(name='heads')
heads_group.add([int(i) for i in np.nonzero(heads > 0)[0]], 1.0, 'REPLACE')


def tris(ratio, group, invert):
    m = work.modifiers.new('r', 'DECIMATE'); m.ratio = ratio; m.vertex_group = group; m.invert_vertex_group = invert
    e = work.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    n = sum(len(p.vertices) - 2 for p in e.polygons); work.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    work.modifiers.remove(m); return n


def decimate_to(target, group, invert):
    lo, hi = 0.002, 1.0
    for _ in range(16):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tris(mid, group, invert) <= target else (lo, mid)
    m = work.modifiers.new('r', 'DECIMATE'); m.ratio = lo; m.vertex_group = group; m.invert_vertex_group = invert
    bpy.ops.object.modifier_apply(modifier=m.name)


# stage 1: the heads alone down to HEAD_TRIS; stage 2: everything else down to the total, heads (and sharp tips) kept
total_now = sum(len(p.vertices) - 2 for p in work.data.polygons)
head_now = sum(1 for p in work.data.polygons if all(heads[v] > 0 for v in p.vertices))
if head_now > HEAD_TRIS:
    decimate_to(total_now - head_now + HEAD_TRIS, 'heads', False)
decimate_to(TARGET, 'keep', True)
me = work.data
rc = np.zeros(len(me.vertices) * 3); me.attributes['rest_co'].data.foreach_get('vector', rc)
me.vertices.foreach_set('co', rc); me.attributes.remove(me.attributes['rest_co']); me.update()
work.vertex_groups.clear()
for o in (mesh, bpy.data.objects['Hydra_Rig']):
    bpy.data.objects.remove(o, do_unlink=True)
work.name = me.name = 'Hydra'
for p in me.polygons:
    p.use_smooth = True
print('REDUCED_BENT triangles', sum(len(p.vertices) - 2 for p in me.polygons), 'vertices', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
