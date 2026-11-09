import bpy,bmesh,numpy as np,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v2.blend'))
rig=bpy.data.objects['Wyrm_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
mesh=bpy.data.objects['Wyrm'];me=mesh.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;tris=[t for t in me.loop_triangles if t.material_index==1]
np.savez(P/'work/head_uv3d.npz',uv=np.array([[uv[l].uv[:] for l in t.loops] for t in tris]),xyz=np.array([[me.vertices[v].co[:] for v in t.vertices] for t in tris]),part=np.array([me.attributes['part'].data[t.vertices[0]].value for t in tris]))
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bm.to_mesh(me);bm.free()
sys.argv=['bake_creature_ao.py','--','Wyrm',str(P/'textures/wyrm_head_ao_2k.png'),'.012','2048'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
