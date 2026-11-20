import bpy,bmesh,json,numpy as np,shutil
from pathlib import Path
root=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/quad_remesh_trial_03_neutral')
s=bpy.data.scenes['MM6 Goblin - Quad Remesh Neutral'];o=s.objects['Retopo_Goblin_QR_200K_Neutral'];m=o.data
m.calc_loop_triangles();areas=np.array([t.area for t in m.loop_triangles]);co=np.array([o.matrix_world@v.co for v in m.vertices]);tris=np.array([t.vertices[:] for t in m.loop_triangles]);c=co[tris].mean(axis=1)
bm=bmesh.new();bm.from_mesh(m)
r={'raw_body_triangles':len(tris),'loop_triangles_area_under_1e_12':int((areas<1e-12).sum()),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'loose_vertices':sum(not v.link_faces for v in bm.verts),'regions':{}}
for name,mask in {'head_z_above_062':c[:,2]>.62,'hands_absx_above_039_z_below_018':(abs(c[:,0])>.39)&(c[:,2]<.18),'belt_skirt_hip':(abs(c[:,0])<.30)&(c[:,2]>-.21)&(c[:,2]<.20),'skirt_height_band':(abs(c[:,0])<.30)&(c[:,2]>-.21)&(c[:,2]<.09)}.items():r['regions'][name]={'triangles':int(mask.sum()),'percent':float(mask.mean()*100)}
bm.free();r['note']='Spatial regions approximate, may include nearby anatomy; not semantic component counts.'
(root/'topology_audit.json').write_text(json.dumps(r,indent=2)+'\n');shutil.copy2('/tmp/Exoside/QuadRemesher/Blender/RetopoSettings.txt',root/'submitted_settings.txt')
print(json.dumps(r))
