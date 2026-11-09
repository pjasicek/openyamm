import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import round4_search as S
for kind,level in [('body',0),('body',1),('body',2),('axe',0),('axe',1)]:
 tag=f'{kind}_lod{level}';file=S.OUT/f'{tag}_curve.json';curve=json.loads(file.read_text());passing=[r for r in curve['steps']if r['visual']['pass']]
 start=min(passing,key=lambda r:r['triangles'])if passing else {'blend':f'work/round4/{tag}_0.blend','triangles':curve['before']}
 bpy.ops.wm.open_mainfile(filepath=str(P/start['blend']));S.reset();obj=bpy.data.objects['Body'if kind=='body'else 'Axe']
 S.CALIBRATION.clear();S.CALIBRATION['diameter']=curve['camera']['bound_diameter_m']
 if kind=='axe':
  # The accepted prop centre is invariant under the protected contour reduction.
  S.activate('Standing');ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=S.np.array([tuple(obj.matrix_world@v.co)for v in me.vertices]);ev.to_mesh_clear();S.CALIBRATION['axe_center']=((co.min(0)+co.max(0))/2).tolist();S.reset()
 S.reduce(obj,.95,planar=not passing);path=S.WORK/f'{tag}_refine.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));folder=S.OUT/tag/'refine_05';S.render(folder,kind,level);metrics=S.evaluate(S.OUT/tag/'reference',folder)
 curve['steps'].append({'step':'refine_05','triangles':S.triangles(obj),'ratio_to_original':S.triangles(obj)/curve['before'],'visual':metrics,'blend':str(path.relative_to(P))})
 file.write_text(json.dumps(curve,indent=2)+'\n');print('REFINE',tag,S.triangles(obj),metrics['min_iou'],metrics['min_ssim'],metrics['pass'],flush=True)
