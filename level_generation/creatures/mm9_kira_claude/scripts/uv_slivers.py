"""Faces whose UVs collapsed onto the atlas origin (user review 2026-11-02: "a dark smudge on the chin below the lower
lip"): three midline sliver triangles under the lower lip and one on the nose bridge (head set) and two at the front of
the collar (body set) have every corner of a UV layer within 0.003 of an atlas corner (Blender (0, 1) = glTF (0, 0)), where the head atlas holds dark hair (the
stroke under the lip that README r7 took for the lip's shadow). Each such corner takes the UV of the same vertex in an
edge-adjacent face whose UVs are valid (the clean neighbouring skin texel), on PartUV (the layer export_kira.py
copies to the runtime UVs; UVMap/HeadUV are working layers). UVs of other faces and the
paint are unchanged. Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
rep = {}
for name, ly in [(n, l) for n, l in bm.loops.layers.uv.items() if n == 'PartUV']:     # the layer export_kira.py ships
    bad = lambda f: any(all((Vector(l[ly].uv) - Vector(c)).length < 0.003 for l in f.loops) for c in ((0, 0), (0, 1), (1, 0), (1, 1)))
    fixed, left = [], 0
    for _ in range(3):                          # neighbours that were degenerate themselves get fixed on a later pass
        todo = [f for f in bm.faces if bad(f)]
        for f in todo:
            ok = True
            for l in f.loops:
                src = None
                for e in f.edges:
                    if l.vert not in e.verts: continue
                    for g in e.link_faces:
                        if g is f or bad(g): continue
                        src = next(x for x in g.loops if x.vert is l.vert); break
                    if src: break
                if src is None:
                    for g in l.vert.link_faces:
                        if g is not f and not bad(g):
                            src = next(x for x in g.loops if x.vert is l.vert); break
                if src is None: ok = False; continue
                l[ly].uv = src[ly].uv
            if ok: fixed.append([round(c, 3) for c in f.calc_center_median()])
    rep[name] = dict(fixed=len(fixed), left=len([f for f in bm.faces if bad(f)]), where=fixed[:8])
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('UVSLIVERS ' + json.dumps(rep))
