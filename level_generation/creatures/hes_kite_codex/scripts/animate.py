"""Eight authored flight/combat/corpse clips, sampled at 24 fps with a fixed living baseline and grounded corpse."""
import bpy,os,sys,json,math,traceback
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import posing as pose

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def pulse(t,peak=.5):return smooth(t/peak) if t<peak else 1-smooth((t-peak)/(1-peak))
def fly(r,t,fast=False):
    for pair,phase in [('Front',0),('Rear',-.25)]:
        a=2*math.pi*(t+phase)
        for side in 'LR':pose.wing(r,pair,side,8+(36 if fast else 31)*math.cos(a),9*math.cos(a-.6),4*(1-math.cos(a)),3*math.sin(a))
    # The tucked legs lag the wing stroke, with a small left/right delay.
    for side,delay in [('L',0),('R',.08)]:
        a=2*math.pi*(t-.12-delay);strength=1.2 if fast else 1
        pose.rotate(r,'Thigh_'+side,'X',10+10*strength*math.sin(a))
        pose.rotate(r,'Shin_'+side,'X',-12-8*strength*math.sin(a-.4))
        pose.rotate(r,'Foot_'+side,'X',8+7*strength*math.sin(a-.8))
    pose.rotate(r,'Neck1','X',3*math.sin(t*2*math.pi));pose.rotate(r,'Head','X',-2*math.sin(t*2*math.pi))
    for i in range(1,8):pose.rotate(r,'Tail'+str(i),'Z',2*math.sin(t*2*math.pi-i*.4))
def attack(r,t):
    # Frame 11 is contact: coil sideways/back, raise the head, then commit the whole body forward.
    rest=(0,0,0,0,0,0,0,0,0,39,8,0)
    keys=[(0,rest),
          (6,(-.13,.16,.04,-16,-12,-22,-18,-9,-12,22,14,28)),
          (8,(-.14,.18,.04,-17,-12,-24,-20,-9,-12,20,12,30)),
          (11,(.035,-.30,-.06,18,3,3,22,-14,12,-8,-12,38)),
          (13,(.025,-.22,-.035,10,1,1,10,-8,16,0,-4,24)),
          (18,rest)]
    frame=t*18
    for (fa,a),(fb,b) in zip(keys,keys[1:]):
        if frame<=fb:
            q=smooth((frame-fa)/(fb-fa));values=[x+(y-x)*q for x,y in zip(a,b)];break
    x,y,z,pitch,roll,yaw,neck1,neck2,head,front,rear,fold=values
    for side in 'LR':
        pose.wing(r,'Front',side,front,9*math.cos(-.6),fold,0)
        pose.wing(r,'Rear',side,rear,9*math.cos(-math.pi/2-.6),fold+4,-3)
    pose.rotate(r,'Spine1','X',pitch);pose.rotate(r,'Spine1','Y',roll);pose.rotate(r,'Spine1','Z',yaw)
    pose.rotate(r,'Neck1','X',neck1);pose.rotate(r,'Neck2','X',neck2);pose.rotate(r,'Head','X',head)
    pose.rotate(r,'Neck1','Z',-.5*yaw);pose.rotate(r,'Head','Z',-.5*yaw)
    for i in range(1,8):pose.rotate(r,'Tail'+str(i),'Z',-yaw*.08)
    pose.translate(r,(x,y,z))
def corpse(r,q):
    pose.rotate(r,'Spine1','X',-9*q)
    pose.rotate(r,'Neck1','X',45*q);pose.rotate(r,'Neck2','X',-18*q);pose.rotate(r,'Head','X',15*q)
    for side in 'LR':
        pose.rotate(r,'Thigh_'+side,'X',132*q);pose.rotate(r,'Shin_'+side,'X',-22*q);pose.rotate(r,'Foot_'+side,'X',-15*q)
        pose.wing(r,'Front',side,-8*q,-2*q,9*q,0)
        pose.wing(r,'Rear',side,-12*q,0,5*q,0)
    for i in range(1,8):pose.rotate(r,'Tail'+str(i),'X',(9 if i==1 else -1)*q)
    fit=P/'work/corpse_fit.json'
    if fit.exists():
        for name,axis,degrees in json.loads(fit.read_text())['corrections']:pose.rotate(r,name,axis,degrees*q)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v3.blend'))
    rig=bpy.data.objects['Ashkite_Rig'];mesh=bpy.data.objects['Ashkite'];sc=bpy.context.scene;sc.render.fps=24
    rig.animation_data_create();reports={};samples={}
    for name,frames in [('Fly',20),('Run',14),('Attack',18),('Sting',18),('Cast',24),('Hit',12),('Death',30),('Dead',24)]:
        act=bpy.data.actions.new(name);act.use_fake_user=True;prev={};bounds=[];lifts=[]
        for f in range(frames+1):
            t=f/frames;rig.animation_data.action=None;pose.reset(rig)
            if name in ('Fly','Run'):fly(rig,t,name=='Run')
            elif name=='Attack':attack(rig,t)
            elif name in ('Cast','Hit'):
                q=pulse(t,.5 if name!='Cast' else .65)
                for side in 'LR':
                    pose.wing(rig,'Front',side,(68 if name=='Cast' else -28)*q+8,10*q,5*q)
                    pose.wing(rig,'Rear',side,(55 if name=='Cast' else -17)*q-20,5*q)
                if name=='Cast':pose.rotate(rig,'Neck1','X',-22*q);pose.rotate(rig,'Head','X',-8*q)
                else:pose.rotate(rig,'Spine1','Z',-15*q);pose.rotate(rig,'Neck2','X',-20*q)
            elif name=='Sting':
                q=pulse(t,.58)
                for side in 'LR':pose.wing(rig,'Front',side,15+20*q,6);pose.wing(rig,'Rear',side,-15+15*q,3)
                pose.rotate(rig,'Spine1','Z',-16*q)
                for i in range(1,8):pose.rotate(rig,'Tail'+str(i),'Z',(62 if i==1 else 22)*q)
                pose.rotate(rig,'Neck1','Z',12*q)
            else:corpse(rig,1 if name=='Dead' else smooth((t-.13)/.68))
            c=pose.coordinates(mesh);lift=-float(c[:,2].min());pose.translate(rig,(0,0,lift));c=pose.coordinates(mesh)
            assert np.isfinite(c).all() and abs(c[:,2].min())<1e-5
            bounds.append([c.min(0).tolist(),c.max(0).tolist()]);lifts.append(lift)
            if name=='Fly':samples[f]=c.copy()
            rig.animation_data.action=act
            for b in rig.pose.bones:
                if b.name in prev and b.rotation_quaternion.dot(prev[b.name])<0:b.rotation_quaternion.negate()
                prev[b.name]=b.rotation_quaternion.copy()
                for field in ('rotation_quaternion','location','scale'):b.keyframe_insert(field,frame=f+1)
        reports[name]={'frames':frames+1,'seconds':frames/24,'bounds':bounds,'root_ground_correction':lifts}
        print('CLIP',name,frames/24,'height',max(b[1][2] for b in bounds),flush=True)
    # One baseline for living clips: per-frame wing contact must never push the whole body upward.
    living=[name for name in reports if name not in ('Death','Dead')]
    baseline=max(max(reports[name]['root_ground_correction']) for name in living)
    for name,report in reports.items():
        rig.animation_data.action=bpy.data.actions[name];bounds=[];corrections=[]
        for f,old in enumerate(report['root_ground_correction']):
            sc.frame_set(f+1);t=f/(report['frames']-1)
            delta=baseline-old if name in living else baseline*(1-smooth((t-.13)/.68)) if name=='Death' else 0
            pose.translate(rig,(0,0,delta));rig.pose.bones['Spine1'].keyframe_insert('location',frame=f+1)
            c=pose.coordinates(mesh);assert np.isfinite(c).all() and c[:,2].min()>-1e-5
            bounds.append([c.min(0).tolist(),c.max(0).tolist()]);corrections.append(old+delta)
            if name=='Fly':samples[f]=c.copy()
        report['bounds']=bounds;report['root_ground_correction']=corrections
        if name in living:assert np.ptp(corrections)<1e-8
        print('FINAL',name,'height',max(b[1][2] for b in bounds),flush=True)
    (P/'review/flight_baseline.json').write_text(json.dumps({'living_baseline_m':baseline,'policy':'One shared living offset; Death eases to the unchanged grounded corpse.'},indent=2)+'\n')
    sc.frame_start=1;sc.frame_end=31;rig.animation_data.action=bpy.data.actions['Fly'];sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_v3.blend'))
    (P/'review/clips_v3.json').write_text(json.dumps(reports,indent=2)+'\n')
    np.savez_compressed(P/'work/fly_samples.npz',**{str(k):v for k,v in samples.items()})
if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
    sys.stdout.flush();os._exit(0)
