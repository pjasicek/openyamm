"""After sym: a few skin edges on each forearm are non-manifold (3 faces on an edge from the reduction). Faces on a non-manifold skin
edge whose normal disagrees with their neighbours go, the holes close, degenerate faces dissolve. Eyes (part 13) are open shells
and stay. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['part']
skin = lambda e: all(v[pl] == 0 for v in e.verts)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
bm.normal_update()
multi = [e for e in bm.edges if len(e.link_faces) > 2 and skin(e)]
drop = set()
for e in multi:
    fs = list(e.link_faces)
    def agree(f):
        nb = [g for v in f.verts for g in v.link_faces if g is not f]
        return sum(f.normal.dot(g.normal) for g in nb) / max(len(nb), 1)
    fs.sort(key=agree)
    drop.update(fs[:len(fs) - 2])
bmesh.ops.delete(bm, geom=list(drop), context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bd = [e for e in bm.edges if e.is_boundary and skin(e)]
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=12)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('CLEAN multi', len(multi), 'dropped', len(drop), 'filled', len(bd), 'nonman skin', sum(1 for e in bm.edges if not e.is_manifold and skin(e)))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
