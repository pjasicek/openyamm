"""Packed body UVs on the textured master (2026-10-22 review: "blurry because texture doesnt cover everything").
Meshy's own layout (copied by transfer_uv.py) used 51 % of the 1K body page, a third of it the head faces' unused
islands (the head has its own set), at 224 texels/m median (the cloak 174) against the Landfall guard's 350.
dump:  triangulates the master's remaining quads (the goggles') in place, then writes work/uvpack_in.npz: the body
       (non-head) triangles' vertex ids, rest positions, Meshy's corner UVs (UVMap), corner normals, piece and garment.
apply: keeps Meshy's layout as layer 'MeshyUV' and writes the packed corner UVs (work/uv_pack.npz, uv_atlas.py) into
       'UVMap' on the body faces; head faces keep 'HeadUV' (their 'UVMap' corners are parked at the page's last texel).
Args: -- dump <blend> | apply <blend> <uv_pack.npz>"""
import bpy, bmesh, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
mode, blend = a[0], os.path.abspath(a[1])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=blend)
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()


def body_tris():
    hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
    sel = [p for p in me.polygons if not hd[p.index]]
    assert all(len(p.vertices) == 3 for p in sel)
    return sel, hd


if mode == 'dump':
    bm = bmesh.new(); bm.from_mesh(me)
    quads = [f for f in bm.faces if len(f.verts) > 3]
    if quads:
        bmesh.ops.triangulate(bm, faces=quads, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(me); me.update()
        print('TRIANGULATED', len(quads), 'quads')
        bpy.ops.wm.save_mainfile()
    bm.free()
    sel, hd = body_tris()
    uv = me.uv_layers['UVMap'].data
    cn = np.array([tuple(c.vector) for c in me.corner_normals]) if hasattr(me, 'corner_normals') else None
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
    co = np.array([tuple(v.co) for v in me.vertices], np.float64)
    vid = np.array([list(p.vertices) for p in sel], np.int32)
    loops = np.array([list(p.loop_indices) for p in sel], np.int32)
    old = np.array([[tuple(uv[l].uv) for l in p.loop_indices] for p in sel], np.float64)
    np.savez(os.path.join(HERE, 'work', 'uvpack_in.npz'), co=co, vid=vid, loops=loops, old_uv=old,
             normals=cn[loops], piece=pv[vid[:, 0]], garment=gv[vid[:, 0]], poly=np.array([p.index for p in sel]))
    print('DUMP', len(sel), 'body triangles of', len(me.polygons), 'faces; head faces', int(hd.sum()))
elif mode == 'apply':
    d = np.load(os.path.abspath(a[2]))
    sel, hd = body_tris()
    assert len(sel) == len(d['uv'])
    if 'MeshyUV' not in me.uv_layers:
        src = me.uv_layers['UVMap']; keep = me.uv_layers.new(name='MeshyUV')
        for i, l in enumerate(src.data):
            keep.data[i].uv = l.uv
    uv = me.uv_layers['UVMap'].data; meshy = me.uv_layers['MeshyUV'].data
    moved = 0
    for p, corners in zip(sel, d['uv']):
        for li, c in zip(p.loop_indices, corners):
            uv[li].uv = (float(c[0]), float(c[1])); moved += 1
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                uv[li].uv = (0.9995, 0.0005)
    me.uv_layers.active = me.uv_layers['UVMap']
    me['uv_pack'] = 1
    bpy.ops.wm.save_mainfile()
    print('APPLY', moved, 'body corners packed; MeshyUV kept;', 'texels/m', float(d['tpu']), 'utilization', float(d['utilization']))
