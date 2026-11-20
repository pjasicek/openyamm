import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];D=json.loads((P/'work/rig.json').read_text());B=D['bones'];result={}
def rx(a):
    c,s=np.cos(a),np.sin(a);return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rz(a):
    c,s=np.cos(a),np.sin(a);return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def radial(p,c,axis):
    d=p-c;return np.linalg.norm(d-axis*np.dot(d,axis))
for sd,h in D['hands'].items():
    wr=np.array(D['joints'][sd+'_Hand']);fw=np.array(h['forward']);normal=np.array(h['normal']);axis=np.array(h['across']);axis/=np.linalg.norm(axis)
    best=None
    for forward in [.10,.12,.14]:
      for offset in [.035,.05,.065]:
        center=wr+fw*forward+normal*offset;sol={};cost=0
        for digit in ['index','middle','ring','pinky']:
            a=B[sd+'_'+digit+'0'];b=B[sd+'_'+digit+'1'];r0=np.array(a['rot']);r1=np.array(b['rot']);base=np.array(a['head']);v0=np.array(a['tail'])-base;v1=np.array(b['tail'])-np.array(b['head']);choice=None
            for q0 in np.linspace(.2,1.9,36):
              rot0=r0@rx(q0);mid=base+rot0@r0.T@v0
              for q1 in np.linspace(.4,2.0,33):
                tip=mid+rot0@r0.T@r1@rx(q1)@r1.T@v1
                radii=np.array([radial(mid,center,axis),radial(tip,center,axis)])
                score=np.sum((radii-.028)**2)+np.sum(np.maximum(.022-radii,0)**2)*12+.00003*(q0-.9)**2
                # Fingers must curl around the front of the handle, not away behind the palm.
                score+=max(0,-np.dot(tip-base,normal))**2
                if choice is None or score<choice[0]:choice=(score,float(q0),float(q1),radii.tolist())
            cost+=choice[0];sol[digit]={'angles':[choice[1],choice[2]],'radii':choice[3]}
        if best is None or cost<best[0]:best=(cost,center,sol)
    cost,center,sol=best
    # Thumb opposition uses a basal sweep and two flexions around the same handle.
    a=B[sd+'_thumb0'];b=B[sd+'_thumb1'];r0=np.array(a['rot']);r1=np.array(b['rot']);base=np.array(a['head']);v0=np.array(a['tail'])-base;v1=np.array(b['tail'])-np.array(b['head']);choice=None
    target=wr+fw*.12+normal*.055
    for sweep in np.linspace(-1.3,1.3,27):
      for q0 in np.linspace(-1.0,1.7,28):
        rot0=r0@rz(sweep)@rx(q0);mid=base+rot0@r0.T@v0
        for q1 in np.linspace(.2,1.8,17):
            tip=mid+rot0@r0.T@r1@rx(q1)@r1.T@v1;radius=radial(tip,center,axis)
            score=(radius-.03)**2+max(.023-radius,0)**2*12+.15*np.sum((tip-target)**2)+max(0,-np.dot(tip-base,normal))**2
            if choice is None or score<choice[0]:choice=(score,float(sweep),float(q0),float(q1),float(radius))
    sol['thumb']={'angles':[choice[2],choice[3]],'sweep':choice[1],'radius':choice[4]}
    for digit,s in sol.items():
        r=rz(s.get('sweep',0))@rx(s['angles'][0]);rig.pose.bones[sd+'_'+digit+'0'].rotation_quaternion=Matrix(r).to_quaternion();rig.pose.bones[sd+'_'+digit+'1'].rotation_quaternion=Matrix(rx(s['angles'][1])).to_quaternion()
    result[sd]={'center':center.tolist(),'axis':axis.tolist(),'fingers':sol,'cost':cost};print(sd,'grip',cost,'center',center,flush=True)
    # The attachment socket is centered inside the solved fist.
    eb=rig.data.bones[sd+'_Sword'];pb=rig.pose.bones[sd+'_Sword'];pb.location=eb.matrix_local.to_3x3().inverted()@(Vector(center)-eb.head_local)
bpy.context.view_layer.update()
ed=np.array([e.vertices[:]for e in body.data.edges]);co=np.array([v.co[:]for v in body.data.vertices]);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=np.array([v.co[:]for v in ev.data.vertices]);ratio=np.linalg.norm(posed[ed[:,0]]-posed[ed[:,1]],axis=1)/np.maximum(1e-5,np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1));checks={}
for sd in D['fingers']:
    ids=set(D['fingers'][sd]['hand_verts']);mask=np.array([int(a) in ids and int(b)in ids for a,b in ed]);checks[sd]=float(ratio[mask].max())
print('G5_HAND_STRETCH',checks,flush=True);(P/'work/grip_stretch.json').write_text(json.dumps(checks,indent=2))
(P/'work/grip.json').write_text(json.dumps(result,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/grip_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.15,.15,.17)
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.42
for sd,h in result.items():
    target=Vector(h['center']);cam.location=target+Vector((.2,-2,.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'grip_{sd}.png');bpy.ops.render.render(write_still=True)
