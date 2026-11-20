"""Texel lookup and AO for the final Wyrm (work/uv_final.blend), written into the Wyrm project:
work/uv3d_v3.npz (body faces) and work/head_uv3d_v3.npz (head faces): per triangle UVs, rest-pose positions and part
(0 body, 1 tongue, 2 eye, 3 cheek, 4 tooth); textures/wyrm_ao_v3_2k.png and wyrm_head_ao_v3_2k.png
(each baked with only its own material's faces, so the overlapping layouts do not mix)."""
import os
import runpy
import sys
import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WYRM = os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude')
SHARED = os.path.join(os.path.dirname(HERE), 'claude_shared')
STAGE = os.environ.get('REA_STAGE', 'dump')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_UVBLEND', 'uv_final_v5.blend')))
rig = bpy.data.objects['Wyrm_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
mesh = bpy.data.objects['Wyrm']; me = mesh.data
if STAGE == 'dump':
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    part = me.attributes['part'].data
    for slot, name in ((0, 'uv3d_v3.npz'), (1, 'head_uv3d_v3.npz')):
        tris = [t for t in me.loop_triangles if t.material_index == slot]
        np.savez(os.path.join(WYRM, 'work', name),
                 uv=np.array([[uv[l].uv[:] for l in t.loops] for t in tris]),
                 xyz=np.array([[me.vertices[v].co[:] for v in t.vertices] for t in tris]),
                 part=np.array([8 if ('moved' in me.attributes and me.attributes['moved'].data[t.polygon_index].value)
                                else 7 if ('patch' in me.attributes and me.attributes['patch'].data[t.polygon_index].value)
                                else part[t.vertices[0]].value for t in tris]))
        print('DUMPED', name, len(tris))
else:   # REA_STAGE=ao_body / ao_head: delete the other material's faces, bake AO (blend is not saved)
    keep = 0 if STAGE == 'ao_body' else 1
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != keep], context='FACES')
    bm.to_mesh(me); bm.free()
    out = os.path.join(WYRM, 'textures', 'wyrm_ao_v3_2k.png' if keep == 0 else 'wyrm_head_ao_v3_2k.png')
    sys.argv = ['bake_creature_ao.py', '--', 'Wyrm', out, '0.04' if keep == 0 else '0.012', '2048']
    runpy.run_path(os.path.join(SHARED, 'bake_creature_ao.py'), run_name='__main__')
    print('AO', out)
