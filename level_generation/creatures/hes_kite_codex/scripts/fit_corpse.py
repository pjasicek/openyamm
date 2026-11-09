import bpy,sys,os,json,traceback
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import posing as pose;from animate import corpse
try:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v3.blend'));r=bpy.data.objects['Ashkite_Rig'];m=bpy.data.objects['Ashkite'];pose.reset(r);corpse(r,1)
 d=np.load(P/'work/surface_v3.npz');v=d['positions'];domain=d['domains'];c=pose.coordinates(m)
 body=(domain=='Body')&(v[:,1]>-.4)&(v[:,1]<.05)&(v[:,2]>.27);floor=float(c[body,2].min());target=floor+.025
 corrections=json.loads((P/'work/corpse_fit.json').read_text())['corrections'] if (P/'work/corpse_fit.json').exists() else [];report={}
 for part in ['Front_L','Front_R','Rear_L','Rear_R']:
  sel=(domain==part)&(abs(v[:,0])>.22)
  def score():
   z=pose.coordinates(m)[sel,2]-target
   return float(np.mean(z*z)+4*np.mean(np.minimum(z,0)**2))
  for step in [12,6,3,1]:
   for repeat in range(3):
    improved=False
    for seg in ['Upper','Fore','Finger1','Finger2','Finger3']:
     name=part+'_'+seg
     for axis in ['X','Y']:
      old=r.pose.bones[name].matrix.copy();best=score();delta=0
      for angle in [-step,step]:
       r.pose.bones[name].matrix=old;bpy.context.view_layer.update();pose.rotate(r,name,axis,angle);val=score()
       if val<best:best=val;delta=angle
      r.pose.bones[name].matrix=old;bpy.context.view_layer.update()
      if delta:pose.rotate(r,name,axis,delta);corrections.append([name,axis,delta]);improved=True
    if not improved:break
  z=pose.coordinates(m)[sel,2]-floor;report[part]={'min':float(z.min()),'max':float(z.max()),'p95':float(np.percentile(z,95))}
 (P/'work/corpse_fit.json').write_text(json.dumps({'corrections':corrections,'body_floor':floor,'wings':report},indent=2)+'\n');print('FIT',report,flush=True)
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
