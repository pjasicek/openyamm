"""Geometry-only reduction curve; high detail is rebaked after silhouette selection."""
import bpy,bmesh,json,sys,math,subprocess,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old
old.R=R

def reduce(body,rig,ratio,factor=.01):
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 # Reconnect normal/UV-split glTF vertices; the subsequent bake restores the high surface shading.
 bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.to_mesh(body.data);bm.free()
 protection=old.protect(body,rig,0)
 md=body.modifiers.new('Planar','DECIMATE');md.decimate_type='DISSOLVE';md.angle_limit=math.radians(.1);md.delimit={'MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 md=body.modifiers.new('Silhouette protected','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=factor;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 body.vertex_groups.remove(body.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 return protection

def main():
 body,rig=old.reset(0);act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=[v.co.z for v in m.vertices];h=max(z)-min(z);ev.to_mesh_clear();pixels=2.1778047/h*700
 old.render(body,rig,'high_silhouette',pixels);curve=[]
 for step in range(1,16):
  body,rig=old.reset(0);ratio=.9**step;prot=reduce(body,rig,ratio);count=sum(len(p.vertices)-2 for p in body.data.polygons);tag=f'body_s{step:02d}';rig.animation_data.action=None
  for bone in rig.pose.bones:bone.matrix_basis.identity()
  bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
  metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),'high_silhouette',tag],text=True));row={'tag':tag,'ratio':ratio,'triangles':count,'min_iou':metrics['min_iou'],'views':[x['iou']for x in metrics['views']],'silhouette_pass':metrics['min_iou']>=.99,'actor_height_px':700,'body_standing_height_m':h,'protection':prot,'blend':f'work/round3/{tag}.blend'};curve.append(row);(R/'silhouette_curve.json').write_text(json.dumps(curve,indent=2));print('SILHOUETTE',tag,count,row['min_iou'],flush=True)
  if not row['silhouette_pass']:break
if __name__=='__main__':main()
