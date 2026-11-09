import bpy,bmesh,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
W=P/'work/round2';R=P/'review/round2'
def reset(level):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(W/f'baseline_sword_l{level}.glb'));ob=bpy.data.objects['Sword']
 for mat in ob.data.materials:
  bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 return ob

def reduce(ob,ratio,level):
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);vg=ob.vertex_groups.new(name='_protect')
 for v in ob.data.vertices:
  if -.20<v.co.z<.11 or v.co.z>.83:vg.add([v.index],1.,'REPLACE')
  else:vg.add([v.index],.25,'REPLACE')
 md=ob.modifiers.new('Planar faces','DECIMATE');md.decimate_type='DISSOLVE';md.angle_limit=math.radians(.00001);md.delimit={'NORMAL','MATERIAL','SEAM','UV'};bpy.ops.object.modifier_apply(modifier=md.name)
 md=ob.modifiers.new('Protect grip and tip','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=.00001;bpy.ops.object.modifier_apply(modifier=md.name);ob.vertex_groups.remove(ob.vertex_groups['_protect'])
 return sum(len(f.vertices)-2 for f in ob.data.polygons)
def render(ob,tag,pixels):
 sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=1024;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.display.render_aa='16';sc.render.threads_mode='FIXED';sc.render.threads=4;c=Vector((.06,0,.305))
 for i in range(8):
  a=i*math.pi/4;d=Vector((math.sin(a),-math.cos(a),.12)).normalized();cam=common.ortho_camera('MetricCamera',c+d*6,(0,0,0),2.1778047*1024/pixels);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(R/f'{tag}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
curve=[]
for level,pixels in enumerate([800,550,220,88]):
 ob=reset(level);render(ob,f'sword_l{level}_reference',pixels);hi=1.;lo=None
 def trial(ratio,step):
  ob=reset(level);count=reduce(ob,ratio,level);tag=f'sword_l{level}_{step}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));render(ob,tag,pixels);m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),f'sword_l{level}_reference',tag],text=True));row={'part':'sword','lod':level,'step':step,'ratio':ratio,'triangles':count,'projected_carrier_diameter_pixels':pixels,**m,'blend':f'work/round2/{tag}.blend','reference':f'work/round2/baseline_sword_l{level}.glb','contact_gate':'pending'if m['pass']else 'not_run_visual_rejection'};curve.append(row);(R/'sword_reduction_curve.json').write_text(json.dumps(curve,indent=2));print('SWORD',level,step,ratio,count,m['min_iou'],m['min_ssim'],m['pass'],flush=True);return m['pass']
 for step in range(1,31):
  ratio=.9**step
  if trial(ratio,f's{step:02d}'):hi=ratio
  else:lo=ratio;break
 if lo is not None:
  for j in range(3):
   ratio=(hi+lo)/2
   if trial(ratio,f'refine{j}'):hi=ratio
   else:lo=ratio
