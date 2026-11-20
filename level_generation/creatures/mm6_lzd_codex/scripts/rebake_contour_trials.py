import bpy,sys,json,subprocess,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
for level in [2,3]:
 tag=f'contour{level}';bpy.ops.wm.open_mainfile(filepath=str(P/('work/rebake/loft3a.blend'if level==3 else'work/rebake/soft2.blend')));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();pv=np.array([v.value for v in body.data.attributes['piece'].data]);body.data.calc_loop_triangles();tris=np.array([tuple(f.vertices)for f in body.data.loop_triangles]);out=posed.copy()
 for part in (['bow']if level==2 else ['body','bow']):
  ids=np.where((pv==201)==(part=='bow'))[0];remap=np.full(len(posed),-1);remap[ids]=np.arange(len(ids));faces=remap[tris[np.all((pv[tris]==201)==(part=='bow'),axis=1)]]
  path=P/f'work/rebake/{tag}_{part}.npz';np.savez(path,vertices=posed[ids],faces=faces,part=part,level=level);subprocess.run(['/usr/bin/python3',str(P/'scripts/contour_silhouette_fit.py'),str(path)],check=True);out[ids]=np.load(path.with_suffix('.npy'))
 matrices={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones}
 for v in body.data.vertices:
  matrix=Matrix([[0]*4 for _ in range(4)])
  for g in v.groups:
   if g.group in matrices:matrix+=matrices[g.group]*g.weight
  v.co=matrix.inverted()@Vector(out[v.index])
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,tag,level)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level)],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('FIT_SILHOUETTE',tag,{k:v['pooled_iou']for k,v in r.items()},flush=True)
