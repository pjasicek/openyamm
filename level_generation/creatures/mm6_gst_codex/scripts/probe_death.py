from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/animate_ghost.py').read_text();exec(s[:s.index("\nrig.animation_data_clear()")])
pose('Dead',0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();length=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1);mask=(PA[E[:,0]]==0)&(EL>.002);rat=length[mask]/EL[mask];print('DEAD STRETCH',np.percentile(rat,[95,99,100]),flush=True)
for edge in np.where(mask)[0][np.argsort(rat)[-8:]]:print('EDGE',C[E[edge]].tolist(),float(length[edge]/EL[edge]))
common.workbench_clay(sc);common.render_views(str(P/'review/dead_probe'),.40,1.10,views=('front','left'),resolution=(640,480))
