"""Check and render native attack anchors before rebuilding exports."""
from pathlib import Path
p=Path(__file__).resolve().parent/'animate_lizard.py'
exec(compile(p.read_text().split('reports={}')[0],str(p),'exec'))
out=P/'review/attack_revision_02';out.mkdir(exist_ok=True)
report={}
for t in [0,.18,.5,.68,.88,1.,1.1,1.25]:
 m=pose('Attack',t);a=co();m.update(max_z=float(a[:,2].max()),min_z=float(a[:,2].min()),snout=list(rig.pose.bones['Head'].tail),left_foot_min_z=float(a[FEET['L'],2].min()),right_foot_min_z=float(a[FEET['R'],2].min()));report[str(t)]=m
 print('ATTACK',t,m,flush=True)
assert max(x['ik_error'] for x in report.values())<.001
assert max(x['contact_error'] for x in report.values())<.001
assert report['0.5']['max_z']>2.5 and report['0.5']['snout'][2]>report['0']['snout'][2]+.7
assert report['0.5']['left_foot_min_z']>.3 and report['0.5']['right_foot_min_z']<.01
assert report['0.5']['snout'][0]>.2 and report['1.0']['snout'][0]<-.4
assert report['1.0']['snout'][1]<report['0.5']['snout'][1]-1.0
(out/'anchor_audit.json').write_text(json.dumps(report,indent=2)+'\n')
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=4.2
for t in [0,.5,.68,.88,1.]:
 pose('Attack',t)
 for label,pos in [('front',(0,-8,1.5)),('side',(8,.4,1.5)),('quarter',(5,-7,3.2))]:
  target=Vector((0,.4,1.4));cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/f'pilot_{int(t*100):03d}_{label}.png');bpy.ops.render.render(write_still=True)
