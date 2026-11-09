"""Create the goblin's editable biped/digit rig and weight the current neutral model in Blender."""
import bpy
import json
import sys
import math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import active,look_at
SCENE='MM6 Goblin rig studio'

def bone_specs(paths):
    specs={}
    def add(name,head,tail,parent=None):specs[name]={'head':head,'tail':tail,'parent':parent}
    add('root',(0,0,0),(0,0,.18))
    add('pelvis',(0,0,.97),(0,0,1.09),'root')
    add('spine',(0,0,1.09),(0,0,1.29),'pelvis')
    add('chest',(0,0,1.29),(0,0,1.45),'spine')
    add('neck',(0,0,1.45),(0,.015,1.58),'chest')
    add('head',(0,.015,1.58),(0,0,1.80),'neck')
    for s,label in [(-1,'R'),(1,'L')]:
        add('clavicle.'+label,(s*.07,0,1.425),(s*.25,0,1.44),'chest')
        add('upper_arm.'+label,(s*.25,0,1.44),(s*.366,.012,1.17),'clavicle.'+label)
        add('forearm.'+label,(s*.366,.012,1.17),(s*.413,-.005,.94),'upper_arm.'+label)
        add('hand.'+label,(s*.413,-.005,.94),(s*.424,-.018,.87),'forearm.'+label)
        add('thigh.'+label,(s*.10,0,.94),(s*.129,-.012,.49),'pelvis')
        add('shin.'+label,(s*.129,-.012,.49),(s*.133,.022,.13),'thigh.'+label)
        add('foot.'+label,(s*.133,.022,.13),(s*.133,-.12,.04),'shin.'+label)
    for name,path in paths.items():
        label=name[-1];parent=('foot.' if name.startswith('toe') else 'hand.')+label
        for i in range(len(path)-1):
            n=name if i==0 else name+'.'+str(i)
            add(n,path[i],path[i+1],parent);parent=n
    add('weapon.R',(-.437,-.032,.873),(-.437+.30*math.sin(math.radians(18)),
        -.032-.30*math.cos(math.radians(18)),.873),'hand.R')
    return specs

def weight_skin(obj,specs):
    coords=np.array([tuple(v.co) for v in obj.data.vertices]);x=coords[:,0];z=coords[:,2];ax=np.abs(x)
    candidates=[n for n in specs if n not in ['root','head','weapon.R']]
    distances=[]
    for name in candidates:
        a=np.array(specs[name]['head']);b=np.array(specs[name]['tail']);d=b-a
        t=np.clip(((coords-a)*d).sum(axis=1)/np.dot(d,d),0,1)
        distance=np.linalg.norm(coords-(a+t[:,None]*d),axis=1)
        valid=np.ones(len(coords),dtype=bool)
        if name.endswith(('.R','.L')) or '.R.' in name or '.L.' in name:
            right='.R' in name;valid &= x<.012 if right else x>-.012
        if name.startswith(('finger','thumb')):valid &= (ax>.335)&(z<.97)
        elif name.startswith('toe'):valid &= (ax<.25)&(z<.14)
        elif name.startswith(('thigh','shin','foot')):valid &= (ax<.26)&(z<1.04)
        elif name.startswith(('upper_arm','forearm','hand','clavicle')):
            # Anatomical separation: hands near the hips must not pull thigh/pelvis skin when raised.
            valid &= ((ax>.25)|((ax>.16)&(z>1.28)))&(z>.70)
        else:valid &= (ax<.27)&(z>.83)
        distances.append(np.where(valid,distance,np.inf))
    distances=np.array(distances).T
    nearest=np.argpartition(distances,3,axis=1)[:,:4]
    chosen=np.take_along_axis(distances,nearest,axis=1)
    assert np.isfinite(chosen[:,0:4]).any(axis=1).all(),'Unclassified skin region'
    weights=1/np.maximum(chosen+.012,.012)**5;weights/=weights.sum(axis=1)[:,None]
    for group in list(obj.vertex_groups):obj.vertex_groups.remove(group)
    groups=[obj.vertex_groups.new(name=n) for n in candidates]
    for vi,(indices,values) in enumerate(zip(nearest,weights)):
        for index,w in zip(indices,values):
            if w>0:groups[int(index)].add([vi],float(w),'REPLACE')
    sums=[sum(g.weight for g in v.groups) for v in obj.data.vertices]
    return {'vertices':len(coords),'max_weight_sum_error':max(abs(v-1) for v in sums),'max_influences':4}

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Inspect existing rig checkpoint before rebuilding'
    source=bpy.data.scenes['MM6 Goblin body studio']
    bpy.context.window.scene=source;bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    meshes=[o for o in scene.objects if o.type=='MESH']
    data=json.loads((ROOT/'body_landmarks.json').read_text());specs=bone_specs(data['digit_paths'])
    arm=bpy.data.armatures.new('Goblin anatomy and prop controls')
    rig=bpy.data.objects.new('Goblin RIG',arm);scene.collection.objects.link(rig);active(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,spec in specs.items():
        bone=arm.edit_bones.new(name);bone.head=spec['head'];bone.tail=spec['tail']
        if spec['parent']:bone.parent=arm.edit_bones[spec['parent']]
        bone.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in arm.bones:bone.inherit_scale='NONE'
    rig.show_in_front=True;arm.display_type='OCTAHEDRAL'
    skin=next(o for o in meshes if o.name.startswith('Goblin body | connected skin'))
    report=weight_skin(skin,specs)
    for obj in meshes:
        if obj is not skin:
            group_names=[g.name for g in obj.vertex_groups]
            assert len(group_names)==1,(obj.name,group_names)
            group=group_names[0]
            if obj.name.startswith('Claw '):
                digit=obj.name[5:].split('.00')[0]
                if digit in data['digit_paths']:
                    count=len(data['digit_paths'][digit])-1
                    terminal=digit if count==1 else digit+'.'+str(count-1)
                    obj.vertex_groups[0].name=terminal
            assert all(g.name in specs for g in obj.vertex_groups),(obj.name,[g.name for g in obj.vertex_groups])
        world=obj.matrix_world.copy();obj.parent=rig;obj.matrix_world=world
        modifier=obj.modifiers.new('Goblin skin deformation','ARMATURE');modifier.object=rig
        modifier.use_deform_preserve_volume=False  # Match standard glTF linear skinning during visual review.
    rig['pose_help']='Named FK biped/digit controls; root positions the whole actor; weapon.R controls the held scimitar.'
    rig['animation_state']='Neutral rig checkpoint; final animation clips not authored yet.'
    scene.frame_start=1;scene.frame_end=24;scene.render.fps=24
    (ROOT/'rig').mkdir(exist_ok=True)
    (ROOT/'rig/bone_manifest.json').write_text(json.dumps(specs,indent=2)+'\n')
    report.update({'bones':len(specs),'mesh_objects':len(meshes),'status':'Neutral rig and deformation probes, no final clips'})
    (ROOT/'rig/weights_report.json').write_text(json.dumps(report,indent=2)+'\n')
    bpy.data.libraries.write(str(ROOT/'rig/neutral_rig_library.blend'),{scene},fake_user=True)
    camera=scene.camera;camera.data.ortho_scale=2.35;camera.location=(-3.2,-4,.98);look_at(camera,(0,0,.98))
    def swing(name,axis,degrees):
        bone=rig.pose.bones[name];rest=bone.bone.matrix_local.to_quaternion()
        bone.rotation_mode='QUATERNION'
        bone.rotation_quaternion=rest.inverted() @ Quaternion(axis,math.radians(degrees)) @ rest
    def reset():
        for p in rig.pose.bones:p.matrix_basis.identity()
        bpy.context.view_layer.update()
    for label,changes in [
        ('neutral',[]),
        ('raised_sword',[('upper_arm.R',(1,0,0),-65),('forearm.R',(1,0,0),-65),('head',(0,0,1),-12)]),
        ('step_probe',[('thigh.L',(1,0,0),-24),('shin.L',(1,0,0),16),('thigh.R',(1,0,0),15),('shin.R',(1,0,0),40)])]:
        reset()
        for args in changes:swing(*args)
        bpy.context.view_layer.update()
        scene.render.filepath=str(ROOT/'review'/f'rig_v2_probe_{label}.png');bpy.ops.render.render(write_still=True)
    reset();active(rig)
    print(json.dumps(report))

if __name__=='__main__':build()
