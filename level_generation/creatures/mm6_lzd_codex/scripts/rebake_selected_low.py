import bpy,bmesh,sys,json,subprocess,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
from rebake_render import render
from rebake_textures import bake
for level in [1,2,3]:
 tag=f'lod{level}_selected';bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/contact{level}.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
 if level==2:
  # The thin chest strap becomes painted/normal detail on the tunic at this distance.
  bm=bmesh.new();bm.from_mesh(body.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]==9],context='VERTS');bm.to_mesh(body.data);bm.free()
 if level==3:
  a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);names=[g.name for g in body.vertex_groups]
  for v in body.data.vertices:
   weight=sum(g.weight for g in v.groups if names[g.group]in ['B_L_Foot','B_L_Toe0'])
   if weight<.55 or v.co.z>=.13:continue
   matrix=sum((rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted()*g.weight for g in v.groups),Matrix([[0]*4 for _ in range(4)]));point=matrix@v.co
   if point.z<.0105:point.z+=.0035;v.co=matrix.inverted()@point
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));r=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('FINAL_LOD_GATES',tag,{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
 if not r['passed']:continue
 path=bake(path,tag,level);render(path,tag,level,parts=['actor'])
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level),'8','actor'],text=True));(P/f'review/rebake/{tag}_actor_metrics.json').write_text(json.dumps(metrics,indent=2));print('FINAL_LOD_ACTOR',tag,metrics['actor']['pooled_iou'],flush=True)
