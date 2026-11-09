"""Rest-pose triangles of the body texture set (UV, 3D, part) for compose_r45.py: work/uv3d.npz (pfem_claude's dump_uv3d.py
without the head-set faces, whose UVs live in the head set), plus work/uv3d_head.npz for the head set."""
import bpy, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Peasant'].data
me.calc_loop_triangles(); uv = me.uv_layers.active.data
part = np.array([a.value for a in me.attributes['part'].data]); head = np.array([a.value for a in me.attributes['head'].data])
knife = json.loads(bpy.context.scene['pfem_knife'])
for name, want in (('uv3d.npz', 0), ('uv3d_head.npz', 1)):
    tris = [t for t in me.loop_triangles if head[t.polygon_index] == want]
    np.savez(os.path.join(HERE, 'work', name), eyes=np.array(bpy.context.scene.get('pfem_eyes', '{}')),
             braid=np.array(bpy.context.scene.get('pfem_braid', '{}')),
             uv=np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], np.float32),
             xyz=np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], np.float32),
             part=np.array([part[t.polygon_index] for t in tris], np.int32), parts=np.array(json.loads(bpy.context.scene['pfem_parts'])),
             grip=np.array(knife['grip']), blade=np.array(knife['blade_dir']))
    print('DUMPED', name, len(tris))
