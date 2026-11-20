"""List boundary loops of 'Body' and fill those with <= max_edges edges (stray holes in Meshy's shell: a cheek hole
under the right eye, a notch in the hair). Big loops (hand stubs, sleeve/neck openings) are kept.
New faces take the material of a neighbour face; attributes default to the neighbour's (head/hand) values.
Args: <in blend> [out blend max_edges]"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bnd = {e for e in bm.edges if e.is_boundary}
loops = []
while bnd:
    e = bnd.pop(); loop = [e]; stack = [e]
    while stack:
        a = stack.pop()
        for v in a.verts:
            for f in v.link_edges:
                if f in bnd:
                    bnd.discard(f); loop.append(f); stack.append(f)
    loops.append(loop)
filled = 0
for loop in sorted(loops, key=len):
    c = sum(((e.verts[0].co + e.verts[1].co) / 2 for e in loop), bpy.types.Object.bl_rna and __import__('mathutils').Vector()) / len(loop)
    print('LOOP', len(loop), [round(x, 3) for x in c])
    if len(argv) > 1 and len(loop) <= int(argv[2]):
        res = bmesh.ops.holes_fill(bm, edges=loop, sides=0)
        res = bmesh.ops.triangulate(bm, faces=res['faces'])
        for f in res['faces']:
            nb = [g for e in f.edges for g in e.link_faces if g is not f]
            if nb:
                f.material_index = nb[0].material_index
                f.smooth = nb[0].smooth
            filled += 1
if len(argv) > 1:
    # face attributes (int) copied from a neighbour
    for layer in list(bm.faces.layers.int.values()):
        for f in bm.faces:
            if f[layer] == 0:
                nb = [g for e in f.edges for g in e.link_faces if g is not f]
                vals = [g[layer] for g in nb if g[layer] != 0]
                if vals and len(vals) == len(nb):
                    f[layer] = vals[0]
    bm.to_mesh(me); me.update()
    print('FILLED faces', filled)
    bpy.ops.wm.save_as_mainfile(filepath=argv[1])
