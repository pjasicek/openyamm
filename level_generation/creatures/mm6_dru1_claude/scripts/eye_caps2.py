"""Eye caps, second version (review 1 follow-up): the first caps (eye_caps.py: a ring halfway to a centre vertex pushed
forward) folded over themselves on the left eye, whose lid opening is concave (the projected eye looked shattered).
Here any existing cap (faces with eye_cap = 1, and the cap-only vertices) is removed and each lid opening (the face
skin's open boundary loop near an eye) is filled with one polygon, triangulated with the BEAUTY method: no new
vertices, so the rim's weights carry the cap. Cap faces: eye_cap = 1, head = 1 (head set), smooth shading; their HeadUV
is set by eye_uv.py. In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
EYES = [Vector((0.017, -0.107, 1.573)), Vector((-0.030, -0.107, 1.573))]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
pl = bm.verts.layers.int['piece']; hl = bm.faces.layers.int['head']
ec = bm.faces.layers.int.get('eye_cap') or bm.faces.layers.int.new('eye_cap')
old = [f for f in bm.faces if f[ec]]
old_v = {v for f in old for v in f.verts}
bmesh.ops.delete(bm, geom=old, context='FACES_ONLY')
lone = [v for v in old_v if v.is_valid and not v.link_faces]
bmesh.ops.delete(bm, geom=lone, context='VERTS')
made = 0
for c in EYES:
    edges = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)
             and all((v.co - c).length < 0.025 for v in e.verts)]
    res = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    faces = res['faces']
    tri = bmesh.ops.triangulate(bm, faces=faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in tri['faces']:
        f[ec] = 1; f[hl] = 1; f.smooth = True
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    made += len(tri['faces'])
    print('EYECAP2 loop edges', len(edges), 'faces', len(tri['faces']))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_mainfile()
print('EYECAPS2 faces', made, 'removed old faces', len(old), 'vertices', len(lone))
