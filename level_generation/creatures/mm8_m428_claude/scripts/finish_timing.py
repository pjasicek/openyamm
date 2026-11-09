"""Preserve source speed; blend one-shots with idle and align the evaluated soles/corpse to the floor."""
import bpy, sys, math, json, numpy as np
from pathlib import Path
from mathutils import Quaternion, Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fidget.blend'))
rig=bpy.data.objects['Rig']; body=bpy.data.objects['Body']; sc=bpy.context.scene; sc.render.fps=30
names=[b.name for b in rig.pose.bones]
def act(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots): rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
    act(a); sc.frame_set(int(f),subframe=f-int(f))
    return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def restore(p):
    act(None)
    for n,(q,l) in p.items():
        b=rig.pose.bones[n]; b.rotation_mode='QUATERNION'; b.rotation_quaternion=q; b.location=l
    bpy.context.view_layer.update()
def smooth(x):
    x=float(np.clip(x,0,1)); return x*x*(3-2*x)
def write(name,frames):
    old=bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a=bpy.data.actions.new(name); a.use_fake_user=True; act(a); prev={}
    for f,p in enumerate(frames):
        for n,(q,l) in p.items():
            b=rig.pose.bones[n]
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q.copy(); b.rotation_quaternion=q; b.location=l
            b.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis': b.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1
    act(None)
ST=sample(bpy.data.actions['Standing'],0)
for name,fi,fo in [('Hit',3,6),('Death',6,0)]:                 # Fidget is authored from/to Standing
    a=bpy.data.actions[name]; N=int(a.frame_range[1]); poses=[]; first=sample(a,0)
    for f in range(N+1):
        p=sample(a,f)
        if name=='Hit':
            # Keep the civilian stance and apply the source's recoil relative to its first guard pose.
            p={n:(ST[n] if n=='B_Pelvis' or any(k in n for k in ('Thigh','Calf','Foot','Toe'))
                  else ((q@first[n][0].inverted())@ST[n][0],ST[n][1])) for n,(q,l) in p.items()}
        if name=='Death':
            # The dress hides the legs: the source fall kicks them apart and up out of the skirt. Keep 20 % of the
            # source leg motion relative to the pelvis (legs stay together under the dress, the body falls as one).
            p={n:((ST[n][0].slerp(q if ST[n][0].dot(q)>=0 else -q,.2),l) if any(k in n for k in ('Thigh','Calf','Foot','Toe')) else (q,l))
               for n,(q,l) in p.items()}
        w=min(smooth(f/fi),smooth((N-f)/fo) if fo else 1)
        poses.append({n:(ST[n][0].slerp(q if ST[n][0].dot(q)>=0 else -q,w),ST[n][1].lerp(l,w)) for n,(q,l) in p.items()})
    write(name,poses)
vg=[g.name for g in body.vertex_groups]
foot=np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'))>.5 for v in body.data.vertices])
# the dress chains are simulated later (dress_sim.py) and the hair may rest on the floor: the corpse floor uses the rest
pv=np.zeros(len(body.data.vertices),np.int32); body.data.attributes['piece'].data.foreach_get('value',pv)
solid=np.array([pv[v.index]!=2 and not any(vg[e.group].startswith('Dress_') and e.weight>.01 for e in v.groups) for v in body.data.vertices])
report={}
for name in ('Standing','Walking','Running','Hit','Death','Fidget'):
    a=bpy.data.actions[name]; N=int(a.frame_range[1]); poses=[sample(a,f) for f in range(N+1)]; lows=[]
    for p in poses:
        restore(p); ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        z=np.array([(body.matrix_world@v.co).z for v in me.vertices]); ev.to_mesh_clear()
        lows.append(float(z[solid].min() if name=='Death' else z[foot].min()))
    lows=np.array(lows)
    # Running retains its airborne phase; the other clips keep a support point on the floor.
    dz=-np.minimum(lows,0) if name=='Running' else -lows
    for f,p in enumerate(poses):
        restore(p); b=rig.pose.bones['B_Pelvis']; m=rig.matrix_world@b.matrix; m.translation.z+=float(dz[f]); b.matrix=rig.matrix_world.inverted()@m
        bpy.context.view_layer.update(); p['B_Pelvis']=(b.rotation_quaternion.copy(),b.location.copy())
    if name in ('Standing','Walking','Running'): poses[-1]={n:(q.copy(),l.copy()) for n,(q,l) in poses[0].items()}
    write(name,poses); report[name]={'duration_s':N/30,'lowest_before_cm':[float(lows.min()*100),float(lows.max()*100)]}
    print('TIMING',name,N/30,'s floor correction cm',float(dz.min()*100),float(dz.max()*100))
assert report['Hit']['duration_s']==.5
act(None)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_timed.blend'))
(P/'work/clip_timing.json').write_text(json.dumps(report,indent=2)+'\n')
