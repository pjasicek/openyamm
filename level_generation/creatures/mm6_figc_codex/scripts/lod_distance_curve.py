"""Ten-percent reductions measured on the assembled creature, with two finer boundary steps."""
import bpy,os,json,math,runpy,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/round3';J=R/'lod_refit';J.mkdir(exist_ok=True);curve=json.loads((R/'lod_refit_curve.json').read_text())['curve'] if (R/'lod_refit_curve.json').exists() else [];cache={r['tag']:r for r in curve};selected={}
os.environ['FIGC_POLICY']='lod_fit'
def tag(part,level,step):return f'fit_{part.lower()}_l{level}_s{step:05.2f}'.replace('.','p')
def candidate(level,steps):
 names={p:tag(p,level,steps[p]) for p in ['Body','Axe','Shield']}
 name='joint_l'+str(level)+'_'+ '_'.join(f'{steps[p]:05.2f}'.replace('.','p') for p in ['Body','Axe','Shield'])
 if name in cache:return cache[name]
 for p,n in names.items():
  if not (R/'candidates'/f'{n}.json').exists():
   os.environ['FIGC_REDUCE']=f'{p},{level},{steps[p]}';os.environ['FIGC_SKIP_RENDER']='1'
   try:runpy.run_path(str(P/'scripts/reduction_candidate.py'),run_name='__main__')
   except SystemExit as e:assert e.code==0
 bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig']
 for p,n in names.items():
  with bpy.data.libraries.load(str(R/'candidates'/f'{n}.blend'),link=False) as (src,dst):dst.meshes=[p+'_reduction_mesh']
  o=bpy.data.objects[p];o.data=dst.meshes[0]
  for x in bpy.data.objects:x.select_set(x==o)
  bpy.context.view_layer.objects.active=o;bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 n='joint_l'+str(level)+'_'+ '_'.join(f'{steps[p]:05.2f}'.replace('.','p') for p in ['Body','Axe','Shield']);path=J/f'{n}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
 cal=json.loads((R/'camera.json').read_text());center=Vector(cal['centres']['Body'])
 scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=False;sh.show_cavity=False;sh.show_specular_highlight=True
 scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
 size=[1024,768,384,192][level];pixels=[800,550,220,88][level];scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100;scene.display.render_aa='32'
 data=bpy.data.cameras.new('fixed_comparison');data.type='ORTHO';data.ortho_scale=cal['body_diameter_m']*size/pixels;cam=bpy.data.objects.new('fixed_comparison',data);scene.collection.objects.link(cam);scene.camera=cam
 out=J/n;out.mkdir(exist_ok=True)
 for i in range(8):
  angle=i*math.pi/4;cam.location=center+Vector((math.sin(angle),-math.cos(angle),.08))*6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'{i}.png');bpy.ops.render.render(write_still=True)
 metrics=J/f'{n}_metrics.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(J/('joint_l'+str(level)+'_00p00_00p00_00p00')),str(out),str(metrics)],check=True)
 counts={p:json.loads((R/'candidates'/f'{v}.json').read_text())['triangles'] for p,v in names.items()};m=json.loads(metrics.read_text());row={'tag':n,'level':level,'steps':dict(steps),'parts':names,'part_triangles':counts,'triangles':sum(counts.values()),'minimum_iou':m['minimum_iou'],'minimum_ssim':m['minimum_ssim'],'visual_pass':m['pass'],'blend':str(path.relative_to(P))};curve.append(row)
 (R/'lod_refit_curve.json').write_text(json.dumps({'curve':curve,'selected':selected},indent=2)+'\n');print('JOINT_CURVE',json.dumps(row),flush=True);return row
for level in range(1,4):
 lower=0.0;upper=None;selected[str(level)]=candidate(level,{p:0.0 for p in ['Body','Axe','Shield']})
 for step in range(1,21):
  row=candidate(level,{p:float(step) for p in ['Body','Axe','Shield']})
  if row['visual_pass']:
   previous=selected[str(level)];lower=step;selected[str(level)]=row
   if row['triangles']==previous['triangles']:row['stop_reason']='protected topology floor';upper=step;break
  else:upper=step;break
 assert upper is not None
 for _ in range(2):
  mid=(lower+upper)/2;row=candidate(level,{p:mid for p in ['Body','Axe','Shield']})
  if row['visual_pass']:lower=mid;selected[str(level)]=row
  else:upper=mid
 (R/'lod_refit_curve.json').write_text(json.dumps({'curve':curve,'selected':selected},indent=2)+'\n')
print('REFIT_CURVE_COMPLETE',json.dumps({k:v['triangles'] for k,v in selected.items()}),flush=True)
