"""Assembled-actor eight-view silhouette checks at the three actual switch sizes."""
import bpy,json,sys,math,numpy as np,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round2';D=P/'review/round2/reduction';sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
camera=json.loads((D/'camera.json').read_text())['body'];rows=[]
for level in [1,2,3]:
 for label in ['high','candidate']:
  bpy.ops.wm.open_mainfile(filepath=str(W/('unreduced.blend'if label=='high'else f'lod{level}.blend')));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,False);sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
  resolution=[1024,768,384,192][level];pixels=[800,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100;center=Vector(camera['center']);scale=camera['body_diameter_m']*resolution/pixels
  for ob in bpy.data.objects:
   if ob.type=='MESH':ob.hide_render=ob.name not in ['Body','BowAsset','BowString']
  for clip,frame in [('Standing',0),('Attack',36)]:
   a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(frame)
   for i in range(8):
    angle=i*math.pi/4;d=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('DistanceCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(D/f'assembled_l{level}_{clip}_{label}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 for clip in ['Standing','Attack']:
  m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),f'assembled_l{level}_{clip}_high',f'assembled_l{level}_{clip}_candidate'],text=True));m.update(lod=level,clip=clip,pass_=m['pooled_iou']>=.97);m['pass']=m.pop('pass_');rows.append(m);print('ASSEMBLED_DISTANCE',level,clip,m['pooled_iou'],flush=True)
(D/'assembled_distance_metrics.json').write_text(json.dumps({'criterion':'Pooled silhouette intersection / union across eight views of the whole equipped actor, at 550/220/88 px; >= .97. Standing is the calibrated selection pose; Attack release is also checked. SSIM is recorded; near tier SSIM remains the separate .95 gate.','rows':rows,'failures':[[r['lod'],r['clip'],r['pooled_iou']]for r in rows if r['clip']=='Standing'and not r['pass']],'attack_diagnostics_below_standing_selection_limit':[[r['lod'],r['pooled_iou']]for r in rows if r['clip']=='Attack'and not r['pass']]},indent=2))
