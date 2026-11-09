import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
attack_only='--attack-only' in sys.argv
source=P/('work/textured_master.blend' if attack_only else 'work/armed_rig.blend');bpy.ops.wm.open_mainfile(filepath=str(source))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];D=json.loads((P/'work/rig.json').read_text());G=json.loads((P/'work/grip.json').read_text());B=D['bones'];J=np.array(D['tail']['joints']);K=D['tail']['root_index'];TAILLEN=np.linalg.norm(np.diff(J,axis=0),axis=1)
if attack_only:
    rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
GRIP={n:pb.matrix_basis.copy()for n,pb in rig.pose.bones.items()if any('_'+d in n for d in ['thumb','index','middle','ring','pinky','Sword'])}
def unit(v):
    v=Vector(v);return v.normalized() if v.length>1e-8 else Vector((0,0,1))
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def pulse(t,a,b,c):return smooth(a,b,t)*(1-smooth(b,c,t))
def setworld(n,head,tail,rot=None):
    rest=rig.data.bones[n];r=rest.matrix_local.to_3x3()
    if rot is None:r=(rest.tail_local-rest.head_local).rotation_difference(Vector(tail)-Vector(head)).to_matrix()@r
    else:r=rot
    m=r.to_4x4();m.translation=Vector(head);rig.pose.bones[n].matrix=m
    bpy.context.view_layer.update()
def pose(clip,t,duration):
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    for n,m in GRIP.items():rig.pose.bones[n].matrix_basis=m
    phase=2*math.pi*t/duration;walk=clip in ['Walk','Running'];attack=clip=='Attack';cast=clip=='Cast';dead=clip in ['Death','Dead'];death=smooth(.15,1.42,t) if clip=='Death' else 1. if clip=='Dead' else 0.
    if dead:phase=0.
    wind=pulse(t,.04,.70,1.02) if attack else 0.;blow=pulse(t,.75,1.05,1.65)if attack else 0.;magic=pulse(t,.08,.9,1.55)if cast else 0.;hit=pulse(t,0,.18,.625)if clip=='Hit'else 0.;fidget=math.sin(phase)*math.sin(math.pi*t/duration)**2 if clip=='Fidget'else 0.
    pitch=.02*math.sin(phase) if walk else .008*math.sin(phase);pitch+=-.27*wind+.27*blow-.16*hit-1.43*death
    roll=.028*math.sin(phase)if walk else 0;roll+=.25*wind-.28*blow+.03*fidget
    rotation=Matrix.Rotation(pitch,3,'X')@Matrix.Rotation(roll,3,'Y');root=Vector(J[K])+Vector((0,0,.008*math.sin(phase*2)if walk else 0))
    points=[None]*len(J)
    points[K]=root
    for i in range(K-1,-1,-1):
        vec=rotation@(Vector(J[i])-Vector(J[i+1]));vec=vec.lerp(Vector((0,TAILLEN[i],.02*TAILLEN[i])),death);points[i]=points[i+1]+vec.normalized()*TAILLEN[i]
    arc=0
    for i in range(K,len(J)-1):
        length=TAILLEN[i];arc+=length
        heading=.20+1.95*arc+.32*(math.sin(phase-4*arc)if walk else .18*math.sin(phase-2*arc))
        heading+=.24*death
        z=.18*(1-arc/sum(TAILLEN[K:]))+.025
        prev=points[i];dz=max(-length*.75,min(length*.75,z-prev.z));xy=math.sqrt(length*length-dz*dz)
        points[i+1]=prev+Vector((math.cos(heading)*xy,math.sin(heading)*xy,dz))
    for i in list(range(K-1,-1,-1))+list(range(K,len(J)-1)):
        h,ta=(points[i+1],points[i])if i<K else(points[i],points[i+1]);setworld(f'Serpent_{i:02}',h,ta)
    bpy.context.view_layer.update()
    for n,a in [('Spine',-.035*wind+.035*blow),('Chest',-.08*wind+.1*blow),('UpperChest',-.03*magic),('Neck',-.035*wind+.045*blow),('Head',-.10*wind+.14*blow+.025*fidget)]:rig.pose.bones[n].rotation_quaternion=Quaternion((1,0,0),a)
    rig.pose.bones['Chest'].rotation_quaternion=Quaternion((0,1,0),.16*wind-.22*blow)@Quaternion((0,0,1),.04*wind-.035*blow)@rig.pose.bones['Chest'].rotation_quaternion
    rig.pose.bones['Head'].rotation_quaternion=Quaternion((0,1,0),.05*wind-.06*blow)@Quaternion((0,0,1),-.045*wind+.04*blow)@rig.pose.bones['Head'].rotation_quaternion
    bpy.context.view_layer.update()
    for sd in G:
        row=int(sd[1])-1;sgn=1 if sd[0]=='L'else-1;parent='UpperChest'if row==0 else'Chest';delta=rig.pose.bones[parent].matrix@rig.data.bones[parent].matrix_local.inverted()
        sh=rig.pose.bones[sd+'_UpperArm'].head.copy();wr0=Vector(D['joints'][sd+'_Hand']);el0=Vector(D['joints'][sd+'_Forearm']);sh0=Vector(D['joints'][sd+'_UpperArm']);v=wr0-sh0
        local=sh0+v*.83+Vector((0,-.06,[.005,.055,.05][row]))
        sway=.015*math.sin(phase+row*.7+(0 if sgn>0 else math.pi))if walk else .006*math.sin(phase+row)
        local+=Vector((sgn*sway,0,0));w=strike=0.
        if attack:
            # Each arm has its own anticipation and impact, without splitting the strike into six separate attacks.
            transition=smooth(0,.18,t)*(1-smooth(1.48,1.75,t))
            peak,impact={'L1':(.62,.97),'R1':(.655,1.0),'L2':(.69,1.025),'R2':(.675,1.01),'L3':(.725,1.075),'R3':(.705,1.05)}[sd]
            w=pulse(t,.05+row*.025,peak,impact)
            strike=pulse(t,peak,impact,1.70)
            raised=sh0+Vector((sgn*[.14,.32,.54][row], [-.08,.16,.12][row], [.38,.22,.055][row]+(.025 if sgn>0 else -.025)))
            cut=sh0+Vector((sgn*[.12,.32,.48][row],[-.39,-.22,.14][row],[-.06,-.20,-.28][row]+(.025 if sgn<0 else 0)))
            raised.y+={'L1':.02,'R1':-.015,'L2':.025,'R2':-.015,'L3':.015,'R3':-.025}[sd]
            cut.y+={'L1':-.02,'R1':.015,'L2':.015,'R2':-.025,'L3':-.01,'R3':.02}[sd]
            local=local+(raised-local)*w+(cut-local)*strike
            arc=math.sin(math.pi*smooth(peak,impact,t))
            local+=Vector({'L1':(.008,-.075,.025),'R1':(-.012,-.06,.04),'L2':(.012,.05,.04),'R2':(-.008,-.04,.02),'L3':(.018,-.03,.018),'R3':(-.015,-.025,.035)}[sd])*arc
            if row==2:local.x+=sgn*.06*pulse(t,1.12,1.36,1.68)
        local+=Vector((sgn*.03*magic,-.07*magic,.12*magic));local.z+=.035*fidget*(1-row*.25)
        # Spread the arms on the recoil, then keep the wrists beside the torso during the backward fall.
        local+=Vector((sgn*(.09*pulse(t,.0,.4,.9)if clip=='Death'else 0),-.03*death,.08*death))
        # Grip direction is independent of wrist position; the native fan keeps upper blades upright.
        ang=[.22,.8,1.32][row]
        blade=unit((sgn*math.sin(ang),-.12,math.cos(ang)))
        if attack:
            # Interpolate sweep angles so the blades travel over the head, not through an antipodal vector flip.
            sweep=math.atan2(.12,math.cos(ang))*(1-w-strike)+{'L1':-.58,'R1':-.52,'L2':-.60,'R2':-.48,'L3':-.55,'R3':-.62}[sd]*w+{'L1':2.30,'R1':2.24,'L2':2.36,'R2':2.27,'L3':2.33,'R3':2.20}[sd]*strike
            fan=math.atan2(math.sin(ang),math.hypot(.12,math.cos(ang)))*(1-w-strike)+[.08,.20,.60][row]*w+[.08,.20,.60][row]*strike
            blade=Vector((sgn*math.sin(fan),-math.cos(fan)*math.sin(sweep),math.cos(fan)*math.cos(sweep)))
        if cast:blade=unit((sgn*math.sin(ang-.3*magic),-.18*magic,math.cos(ang-.3*magic)))
        blade=unit(blade.lerp(Vector((sgn,0,.03)),death))
        blade=delta.to_3x3()@blade
        if death>.5:blade=unit(blade.lerp(Vector((sgn,.1,.025)),smooth(.5,1,death)))
        normal=np.array(D['hands'][sd]['normal']);fw=np.array(D['hands'][sd]['forward']);ac=np.array(D['hands'][sd]['across']);ac=ac-fw*np.dot(ac,fw);ac/=np.linalg.norm(ac);cross=np.cross(fw,ac);src=np.column_stack([fw,ac,cross]);sign=1 if cross[1]<0 else-1
        nz=delta.to_3x3()@Vector((0,-sign,0));fd=unit(blade.cross(nz))
        if attack:
            outward=delta.to_3x3()@Vector((sgn,0,0));preferred=outward*.35+unit(delta@local-sh)*.65;aligned=unit(preferred-blade*preferred.dot(blade));fd=unit(fd.lerp(aligned,min(1,w+strike)))
        nz=fd.cross(blade);dst=Matrix((fd,blade,nz)).transposed();r=dst@Matrix(src).transposed()@rig.data.bones[sd+'_Hand'].matrix_local.to_3x3()
        L1=(el0-sh0).length;L2=(wr0-el0).length;target=delta@local;target=target.lerp(sh+fd*((L1+L2)*.72),death*.75);vec=target-sh;reach=min(vec.length,(L1+L2)*.985);d=vec.normalized();target=sh+d*reach
        a=(L1*L1-L2*L2+reach*reach)/(2*reach);height=math.sqrt(max(0,L1*L1-a*a));pole=(target-fd*L2)-(sh+d*a)
        if attack:pole=unit(pole).lerp(unit(delta.to_3x3()@Vector((sgn,[-1.4,.70,1.0][row],[.90,.20,-1.0][row]))),transition)
        perp=unit(pole-d*pole.dot(d));el=sh+d*a+perp*height
        if attack:
            relaxed=r.to_quaternion();fore=unit(target-el);outward=delta.to_3x3()@Vector((sgn,0,0));blade=unit(blade+outward*[.35,.35,.10][row]);along=blade.dot(fore);limit=math.sin(math.radians(40))
            if abs(along)>limit:blade=unit(blade-fore*along)*math.sqrt(1-limit*limit)+fore*math.copysign(limit,along)
            outward=delta.to_3x3()@Vector((sgn,0,0));blade=unit(blade+outward*max(0,[.10,.22,.45][row]-blade.dot(outward)))
            along=blade.dot(fore);limit=math.sin(math.radians(50))
            if abs(along)>limit:blade=unit(blade-fore*along)*math.sqrt(1-limit*limit)+fore*math.copysign(limit,along)
            fd=unit(fore-blade*fore.dot(blade));nz=fd.cross(blade);dst=Matrix((fd,blade,nz)).transposed();r=dst@Matrix(src).transposed()@rig.data.bones[sd+'_Hand'].matrix_local.to_3x3()
        if attack:r=relaxed.slerp(r.to_quaternion(),transition).to_matrix()
        setworld(sd+'_UpperArm',sh,el);setworld(sd+'_Forearm',el,target);bpy.context.view_layer.update()
        setworld(sd+'_Hand',target,None,r)
    for i in range(4):rig.pose.bones[f'Hair_{i}'].rotation_quaternion=Quaternion((1,0,0),(.025*math.sin(phase-i*.6)if walk else .01*math.sin(phase-i*.5))-.12*death)
    bpy.context.view_layer.update()
    if death>0:
        for i in range(4):
            n=f'Hair_{i}';pb=rig.pose.bones[n];h=pb.head.copy();original=pb.tail.copy();L=rig.data.bones[n].length
            desired=h+Vector((0,L*.98,-min(L*.2,max(0,h.z-.08))))
            target=original.lerp(desired,death);target=h+(target-h).normalized()*L
            setworld(n,h,target)
    bpy.context.view_layer.update()
    # Ground the skin; attached blade clearance is checked independently.
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());minimum=min((ev.matrix_world@v.co).z for v in ev.data.vertices)
    rig.location.z=-minimum+.003
    bpy.context.view_layer.update()

if '--stress' in sys.argv:
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('World');sc.world.color=(.12,.12,.14)
    cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.3
    for clip,t,duration in [('Standing',0,3),('Walk',.2,.875),('Attack',.7,1.7),('Attack',1.,1.7),('Death',1.5,1.5)]:
        rig.location.z=0;pose(clip,t,duration)
        for view,location in [('front',(0,-6,2)),('quarter',(4,-6,3)),('side',(6,0,2))]:
            deps=bpy.context.evaluated_depsgraph_get();coords=[ob.evaluated_get(deps).matrix_world@v.co for ob in bpy.data.objects if ob.type=='MESH' for v in ob.evaluated_get(deps).data.vertices];target=Vector(tuple((min(p[i] for p in coords)+max(p[i] for p in coords))/2 for i in range(3)));cam.location=target+Vector(location);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();inv=cam.rotation_euler.to_matrix().transposed();c=[inv@(p-target) for p in coords];cam.data.ortho_scale=1.12*max(max(p[i]for p in c)-min(p[i]for p in c)for i in [0,1]);sc.render.filepath=str(P/'review'/f'stress_{clip}_{t}_{view}.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/stress.blend'))
else:
    clips={'Standing':3.,'Walk':.875,'Running':.625,'Fidget':2.,'Attack':1.75,'Cast':1.75,'Hit':.625,'Death':1.5,'Dead':1.}
    if attack_only:
        clips={'Attack':1.75}
        rig.animation_data.action=None
        for track in list(rig.animation_data.nla_tracks):
            if track.name=='Attack':rig.animation_data.nla_tracks.remove(track)
        bpy.data.actions.remove(bpy.data.actions['Attack'])
    elif rig.animation_data:rig.animation_data_clear()
    sc=bpy.context.scene;sc.render.fps=24;reports=json.loads((P/'work/animation_audit.json').read_text()) if attack_only else {};weights={'co':np.array([v.co[:]for v in body.data.vertices]),'edges':np.array([e.vertices[:]for e in body.data.edges])};rest=np.linalg.norm(weights['co'][weights['edges'][:,0]]-weights['co'][weights['edges'][:,1]],axis=1)
    for clip,duration in clips.items():
        action=bpy.data.actions.new(clip);rig.animation_data_create();rig.animation_data.action=action;rig.location=(0,0,0);maximum=0;floor=1e6;last_rotation={};hemisphere_fixes=0
        for f in range(round(duration*24)+1):
            sc.frame_set(f);rig.location.z=0;pose(clip,f/24,duration)
            for pb in rig.pose.bones:
                # Linear quaternion curves must stay on one hemisphere between sampled poses.
                q=pb.rotation_quaternion.copy()
                if pb.name in last_rotation and q.dot(last_rotation[pb.name])<0:
                    q.negate();pb.rotation_quaternion=q;hemisphere_fixes+=1
                last_rotation[pb.name]=q.copy()
                pb.keyframe_insert('location',frame=f,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=f,group=pb.name);pb.keyframe_insert('scale',frame=f,group=pb.name)
            rig.keyframe_insert('location',frame=f)
            ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());c=np.array([(ev.matrix_world@v.co)[:]for v in ev.data.vertices]);st=np.linalg.norm(c[weights['edges'][:,0]]-c[weights['edges'][:,1]],axis=1)/np.maximum(rest,1e-5);maximum=max(maximum,float(np.percentile(st,99)));floor=min(floor,float(c[:,2].min()))
        track=rig.animation_data.nla_tracks.new();track.name=clip;track.strips.new(clip,0,action);track.mute=True
        reports[clip]={'duration':duration,'floor':floor,'edge_stretch_p99_max':maximum,'quaternion_hemisphere_fixes':hemisphere_fixes};print(clip,reports[clip],flush=True)
    # Match runtime linear samples in the editable master.
    for action in bpy.data.actions:
     for layer in action.layers:
      for strip in layer.strips:
       for bag in strip.channelbags:
        for curve in bag.fcurves:
         for key in curve.keyframe_points:key.interpolation='LINEAR'
    rig.animation_data.action=None
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    rig.location=(0,0,0);sc.frame_set(0);(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/textured_master.blend' if attack_only else 'work/anim_v1.blend')))
