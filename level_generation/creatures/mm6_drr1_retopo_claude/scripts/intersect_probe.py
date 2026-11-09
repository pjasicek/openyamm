"""Self-intersections (BVH overlap of a mesh with itself, excluding faces sharing a vertex) of the installed master
and the source, in the rest pose and in Standing frame 1. Prints counts and the centres of intersecting pairs."""
import os, bmesh, bpy
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for label, path in (('source', os.path.join(HERE, 'work', 'source_snapshot.blend')),
                    ('new', os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude', 'export', 'mm6_wyrm.blend'))):
    bpy.ops.wm.open_mainfile(filepath=path)
    o = bpy.data.objects['Wyrm']; rig = bpy.data.objects['Wyrm_Rig']
    for pose in ('rest', 'Standing'):
        if pose == 'rest':
            rig.animation_data.action = None
            for b in rig.pose.bones: b.matrix_basis.identity()
        else:
            rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new(); bm.from_object(o, dg); bm.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(bm)
        pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and not set(v.index for v in bm.faces[a].verts) & set(v.index for v in bm.faces[b].verts)]
        body = [(a, b) for a, b in pairs if bm.faces[a].calc_center_median().z < 0.3 and bm.faces[a].calc_center_median().y > -0.42]
        print('INTERSECT', label, pose, len(pairs), 'below head', len(body),
              [tuple(round(c, 3) for c in bm.faces[a].calc_center_median()) for a, b in body[:12]])
        bm.free()
