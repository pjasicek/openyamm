"""Compress only viewer frames 17–32 of Attack/Cast by 2.5x; preserve every pose value."""
from pathlib import Path
import bpy,sys,json,copy
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
START,END,SPEED=17/48,32/48,2.5
REMOVED=(END-START)*(1-1/SPEED)
def retime(t):
 if t<=START:return t
 if t<END:return START+(t-START)/SPEED
 return t-REMOVED
assert abs(retime(END)-retime(START)-(END-START)/SPEED)<1e-12
assert abs(retime(.875)-.6875)<1e-12
path=P/'export/mm8_m572_lod0.glb';d,b=read_glb(path);b=bytearray(b);seen={};changed=[]
for action in d['animations']:
 if action['name'] not in ('Attack','Cast'):continue
 duration=max(np.frombuffer(accessor_bytes(d,b,s['input']),'<f4').max() for s in action['samplers'])
 assert abs(duration-1.25)<1e-6,('Expected unretimed source',action['name'],float(duration))
 for s in action['samplers']:
  i=s['input']
  if i not in seen:
   times=np.frombuffer(accessor_bytes(d,b,i),'<f4');new=np.array([retime(float(t)) for t in times],dtype='<f4')
   assert np.all(np.diff(new)>0)
   meta=copy.deepcopy(d['accessors'][i]);meta['min']=[float(new.min())];meta['max']=[float(new.max())]
   seen[i]=append_accessor(d,b,meta,new.tobytes())
  s['input']=seen[i]
 changed.append(action['name'])
assert set(changed)=={'Attack','Cast'}
bpy.ops.wm.open_mainfile(filepath=str(P/'phoenix_master.blend'))
for name in changed:
 action=bpy.data.actions[name];assert abs(action.frame_range[1]-40)<1e-5
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:
      time,left,right=key.co.x,key.handle_left.x,key.handle_right.x
      key.co.x=retime(time/32)*32;key.handle_left.x=retime(left/32)*32;key.handle_right.x=retime(right/32)*32
     fc.update()
 assert abs(action.frame_range[1]-34)<1e-5
bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'phoenix_master.blend'))
write_glb(path,d,b)
report={'source_viewer_fps':48,'source_frames':[17,32],'new_frames':[17,23],'speed':SPEED,'removed_seconds':REMOVED,'duration_seconds':retime(1.25),'impact_seconds':retime(.875),'method':'Retimed existing key timestamps in packed Blender and GLB; pose values unchanged.'}
(P/'work/attack_retime.json').write_text(json.dumps(report,indent=2)+'\n')
flames_path=P/'work/flames.json';flames=json.loads(flames_path.read_text());flames['source_attack_pulse_seconds']=.875;flames['attack_pulse_seconds']=report['impact_seconds'];flames['retiming']='work/attack_retime.json'
flames_path.write_text(json.dumps(flames,indent=2)+'\n')
print(json.dumps(report,indent=2))
