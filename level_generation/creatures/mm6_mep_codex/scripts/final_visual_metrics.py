import bpy,bmesh,json,sys,math,subprocess
from pathlib import Path
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm
R=p/'review/reduction';results=[]
for level in range(4):
 for tier in 'abc':
  for reference in [True,False]:
   bpy.ops.wm.open_mainfile(filepath=str(p/('work/textured.blend' if reference else f'work/final_lod{level}.blend')));ob=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
   if not reference:
    bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]==100],context='VERTS');bm.to_mesh(ob.data);bm.free()
   for mat in ob.data.materials:
    if mat.name.startswith('MepStaff'):continue
    prefix='mep_head' if 'Head' in mat.name else 'mep';folder=p/'textures' if reference else p/f'textures/lod{level}'
    node=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(folder/f'{prefix}_review_{tier}.png'),check_existing=False);mat.node_tree.nodes.active=node
   if reference:
    a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
    for sd,degrees in [('L',-11.63773),('R',6.24394)]:
     pb=r.pose.bones[f'B_{sd}_Foot'];m=(Quaternion((0,0,1),math.radians(degrees))@pb.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=0)
   tag=f'final_{"ref" if reference else "lod"}{level}_{tier}';rm.render(ob,r,'body',level,tag)
  score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'final_ref{level}_{tier}',f'final_lod{level}_{tier}'],text=True));score['pass']=(score['min_iou']>=.99 and score['min_ssim']>=.95) if level==0 else score['pooled_iou']>=.97;results.append({'lod':level,'tier':tier,**score});print('FINAL_VISUAL',level,tier,score['min_iou'],score['min_ssim'],score['pass'],flush=True)
(p/'review/final_visual_metrics.json').write_text(json.dumps(results,indent=2))

assert len(results)==12 and all(row["pass"] for row in results),"Final LOD visual gate failed"
