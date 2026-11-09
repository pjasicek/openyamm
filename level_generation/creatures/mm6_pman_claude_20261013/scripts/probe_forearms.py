import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_feedback_v2/textured_uv.blend'))
r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
pose={b.name:b.matrix_basis.copy() for b in r.pose.bones};report={}
for name,path in [('current','before_feedback_v2/textured_uv.blend'),('original','before_feedback_v1/textured_uv.blend'),('dense','clearance_v1.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/path));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data;pc=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);names=[g.name for g in o.vertex_groups];weights=np.zeros((len(co),len(names)))
 for v in me.vertices:
  for g in v.groups:weights[v.index,g.group]=g.weight
 r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();faces=np.array([list(f.vertices) for f in me.polygons]);np.savez_compressed(P/'work'/f'forearms_{name}.npz',co=co,piece=pc,faces=faces,weights=weights,names=names)
 report[name]={'vertices':len(co),'faces':len(faces),'bones':{b.name:[list(b.head_local),list(b.tail_local)] for b in r.data.bones if any(s in b.name for s in ['UpperArm','Forearm','Hand'])},'pieces':{str(p):int((pc==p).sum()) for p in [4,5]},'custom_normals':me.has_custom_normals}
 for stage in ['rest','standing']:
  if stage=='standing':
   for b in r.pose.bones:
    if b.name in pose:b.matrix_basis=pose[b.name]
  bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  np.save(P/'work'/f'forearms_{name}_{stage}.npy',posed)
  me.materials.clear();mat=bpy.data.materials.new('Clay');mat.diffuse_color=(.55,.55,.55,1);me.materials.append(mat)
  for f in me.polygons:f.material_index=0
  common.setup_render();common.workbench_clay(bpy.context.scene)
  common.render_views(str(P/'review/feedback_v2'/f'{name}_{stage}'),1.03,.62,views=('left','back'),target=(.29,.04),resolution=(650,850))
(P/'work/forearm_probe.json').write_text(json.dumps(report,indent=2));print('FOREARMS',json.dumps({k:{n:v for n,v in d.items() if n!='bones'} for k,d in report.items()}))
