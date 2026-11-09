"""Find each colour LOD by measured image and rig gates; no fixed LOD ratios."""
import bpy,sys,runpy,json,math,subprocess,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import common,round1_materials as M,round1_reduce_mesh as D
R=P/'review/round1/reduction';R.mkdir(parents=True,exist_ok=True);W=P/'work/reduction';W.mkdir(exist_ok=True)
HIGH=P/'work/round1_high.blend';curve=[];selected=[];previous=HIGH
def render(folder,objname,level,directory=None):
 folder.mkdir(parents=True,exist_ok=True);r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene
 a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 M.setup(b,ax,directory=directory,rebaked=directory is not None);common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard';sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.display.shading.show_cavity=False;sc.display.shading.show_specular_highlight=False;sc.render.resolution_x=sc.render.resolution_y=1024;sc.render.resolution_percentage=100
 target=b if objname in ['Body','Combined'] else ax;other=ax if objname in ['Body','Combined'] else b;target.hide_render=False;other.hide_render=objname!='Combined'
 # Conservative up-switch size; LOD0 is the largest melee-range 700-pixel actor.
 scales=[1.852535*1024/700,2.689537525177002*1024/550,2.689537525177002*1024/220,2.689537525177002*1024/88];scale=scales[level]
 tiers='abc' if objname in ['Body','Combined'] else 'a'
 for tier in tiers:
  M.tier([b,ax],tier,directory=directory)
  for k in range(8):
   angle=k*math.pi/4;cam=common.ortho_camera('reduce_camera',(math.sin(angle)*6,-math.cos(angle)*6,.93),(math.pi/2,0,angle),scale);sc.camera=cam;sc.render.filepath=str(folder/f'{tier}_{k}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 target.hide_render=False;other.hide_render=False
 return {'ortho_scale_m':scale,'image_pixels':1024,'nominal_actor_height_pixels':1.852535/scale*1024}
for level in globals().get('LEVELS',range(4)):
 references={}
 for objname in ['Body','AxeMesh']:
  bpy.ops.wm.open_mainfile(filepath=str(HIGH));references[objname]=R/f'L{level}_{objname}_reference';render(references[objname],objname,level)
 best=previous
 for objname in ['Body','AxeMesh']:
  for step in range(1,20):
   bpy.ops.wm.open_mainfile(filepath=str(best));r=bpy.data.objects['Rig'];r.animation_data.action=None
   for pb in r.pose.bones:pb.matrix_basis.identity()
   bpy.context.view_layer.update();M.setup(bpy.data.objects['Body'],bpy.data.objects['AxeMesh']);obj=bpy.data.objects[objname];counts=D.reduce(obj,r,.90 if objname=='Body' else .95,level);dest=W/f'L{level}_{objname}_{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
   folder=R/f'L{level}_{objname}_{step}';folder.mkdir(parents=True,exist_ok=True)
   if counts['after']==counts['before']:
    curve.append({'level':level,'object':objname,'step':step,**counts,'pass':False,'reason':'protected topology floor'});break
   if level==0:
    texdir=folder/'textures';runpy.run_path(str(P/'scripts/round1_rebake.py'),run_name='__main__',init_globals={'INPUT':str(dest.relative_to(P)),'OUTPUT':str(dest.relative_to(P)),'TEXTURES':str(texdir.relative_to(P)),'REPORT':str((folder/'rebake.json').relative_to(P)),'ONLY':objname})
   else:texdir=P/'textures/round1_rebaked'
   camera=render(folder,objname,level,directory=texdir);metric=folder/'metrics.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(references[objname]),str(folder),str(metric)],check=True);visual=json.loads(metric.read_text())
   entry={'level':level,'object':objname,'step':step,**counts,'camera':camera,'min_iou':visual['min_iou'],'min_ssim':visual['min_ssim'],'visual_pass':visual['pass'],'blend':str(dest.relative_to(P))}
   if visual['pass']:
    sys.argv=['gate','--',str(dest.relative_to(P))];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__');gate=json.loads((P/'review/rig_gates.json').read_text());shutil.copy2(P/'review/rig_gates.json',folder/'rig_gates.json')
    runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__',init_globals={'INPUT':str(dest.relative_to(P)),'REPORT':str((folder/'precision.json').relative_to(P))});prec=json.loads((folder/'precision.json').read_text())
    entry['rig_pass']=all(all(v['pass'].values()) for v in gate.values()) and all(v['pass'] for v in prec.values());entry['max_G4']=max(x['value'] for v in gate.values() for x in v['G4'].values());entry['max_G5']=max(x['value'] for v in gate.values() for x in v['G5'].values());entry['max_G6_mm']=max(x['depth_m']*1000 for v in gate.values() for x in v['G6'].values());entry['failing_clips']=[n for n,v in gate.items() if not all(v['pass'].values())]+[n for n,v in prec.items() if not v['pass']]
   else:entry['rig_pass']=None
   entry['pass']=entry['visual_pass'] and entry['rig_pass'];curve.append(entry);(R/'curve.json').write_text(json.dumps({'steps':curve,'selected':selected},indent=2));print('REDUCTION',json.dumps(entry),flush=True)
   if not entry['pass']:break
   best=dest
  else:raise AssertionError('Reduction did not reach a measured stopping point')
 bpy.ops.wm.open_mainfile(filepath=str(best));out=P/f'work/round1_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));selected.append({'level':level,'blend':str(out.relative_to(P)),'body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh'])});previous=out
 if level==0:runpy.run_path(str(P/'scripts/round1_rebake.py'),run_name='__main__')
 (R/'curve.json').write_text(json.dumps({'steps':curve,'selected':selected},indent=2))
assert len(selected)==len(globals().get('LEVELS',range(4)))
assert all(a['body_triangles']+a['axe_triangles']>b['body_triangles']+b['axe_triangles'] for a,b in zip(selected,selected[1:]))
