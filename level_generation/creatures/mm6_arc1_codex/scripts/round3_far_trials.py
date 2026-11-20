import bpy,sys,json,math,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
D=P/'review/round3/reduction';camera=json.loads((D/'camera.json').read_text())['body'];rows=[]
for offset in [-.003,-.0015,.0015,.003,.005,.008]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/lod3.blend'));body=bpy.data.objects['Body'];gn={g.index:g.name for g in body.vertex_groups};piece=body.data.attributes['piece'];moved=0
 for v in body.data.vertices:
  protect=sum(g.weight for g in v.groups if any(t in gn[g.group]for t in ['Hand','Finger','Foot','Toe','Head','Neck']))>.15
  if not protect and piece.data[v.index].value in [0,1]and v.co.z>.04:v.co+=v.normal*offset;moved+=1
 body.data.update();r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;sc.frame_set(0);common.workbench_clay(sc,False);sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.resolution_x=sc.render.resolution_y=192;sc.render.resolution_percentage=100;center=Vector(camera['center']);scale=camera['body_diameter_m']*192/88;tag=f'far_offset{offset}'
 for ob in bpy.data.objects:
  if ob.type=='MESH':ob.hide_render=ob.name not in ['Body','BowAsset','BowString']
 for i in range(8):
  d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();cam=common.ortho_camera('DistanceCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(D/f'{tag}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 metric=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'assembled_l3_Standing_high',tag],text=True));row={'offset_m':offset,'moved_vertices':moved,'pooled_iou':metric['pooled_iou']};rows.append(row);print('FAR_TRIAL',row,flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round3/{tag}.blend'))
(D/'far_trials.json').write_text(json.dumps(rows,indent=2))
runpy=None
