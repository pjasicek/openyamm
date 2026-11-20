"""Rest/pose clay shots with chosen garments hidden (vertices of those garments collapsed out of view by a mask
modifier). Args: -- <blend> <out prefix> <views comma> <hide garments comma> <action:frame|rest> [...]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, outp, views, hide, picks = a[0], a[1], a[2].split(','), [int(x) for x in a[3].split(',')], a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; scene = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data])
show = ~np.isin(gv, hide)
if os.environ.get('HIDE_INNER'):          # hide the inner layer of the coat (a vertex whose outward radial ray meets the
    from mathutils import Vector          # coat again within 4 cm) to tell it apart from the outer surface
    from mathutils.bvhtree import BVHTree
    G = (1, 2); co = [v.co.copy() for v in me.vertices]
    T = BVHTree.FromPolygons(co, [tuple(p.vertices) for p in me.polygons if all(gv[i] in G for i in p.vertices)])
    pel = rig.data.bones['B_Pelvis'].head_local
    for i in np.where(np.isin(gv, G))[0]:
        d = Vector((co[i].x - pel.x, co[i].y - pel.y, 0))
        if d.length > 1e-4 and co[i].z < 0.95:
            d.normalize(); h = T.ray_cast(co[i] + d * 0.002, d, 0.04)
            if h[0] is not None:
                show[i] = False
    print('HIDE inner verts', int((~show & np.isin(gv, G)).sum()))
vg = body.vertex_groups.new(name='_show'); vg.add([int(i) for i in np.where(show)[0]], 1.0, 'REPLACE')
m = body.modifiers.new('mask', 'MASK'); m.vertex_group = '_show'
common.workbench_clay(scene)
for pk in picks:
    rig.animation_data_create()
    if pk == 'rest':
        rig.animation_data.action = None
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        name, f = 'rest', 0
    else:
        name, f = pk.split(':'); act = bpy.data.actions[name]; rig.animation_data.action = act
        if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(f))
    for v in views:
        common.render_views(outp + f'_{name}_{f}', float(os.environ.get('ZC', '0.6')), float(os.environ.get('SIZE', '1.3')), views=(v,), resolution=(560, 760))
print('HIDE shots done')
