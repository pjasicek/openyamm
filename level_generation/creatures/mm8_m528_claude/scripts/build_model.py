"""Authored smoke ring, core and pulse/dispersion rig; white stars are engine particles."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Euler,Vector

P=Path(__file__).resolve().parents[1]
FPS=48; TAU=2*math.pi; SMOKE=12
FULL='--full' in sys.argv
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.fps=FPS
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def pulse(t,a,b):return math.sin(math.pi*(t-a)/(b-a))**2 if a<t<b else 0

arm=bpy.data.armatures.new('WispRig');rig=bpy.data.objects.new('WispRig',arm)
bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
names=['Root','Ring','Core','Flash']+[f'Smoke{i:02d}' for i in range(SMOKE)]
for name in names:
    b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,0,.1)
    if name!='Root':b.parent=arm.edit_bones['Root']
bpy.ops.object.mode_set(mode='OBJECT')
socket=bpy.data.objects.new('Socket_Core',None);bpy.context.collection.objects.link(socket)
socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Core';socket.location=(0,-.1,0)

def material(name,filename):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED';m.use_backface_culling=True
    ns=m.node_tree.nodes;bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED');t=ns.new('ShaderNodeTexImage')
    t.image=bpy.data.images.load(str(P/'textures'/filename));t.extension='REPEAT' if name=='WispSmoke' else 'EXTEND'
    m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(t.outputs['Alpha'],bs.inputs['Alpha'])
    m.node_tree.links.new(t.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
    bs.inputs['Roughness'].default_value=1;bs.inputs['Metallic'].default_value=0
    return m
bodymat=material('WispSmoke','m528_smoke.png');fxmat=material('WispLight','m528_fx.png')

class Mesh:
    def __init__(self):self.v=[];self.f=[];self.uv=[];self.b=[]
    def face(self,coords,uvs,bone,reverse=False):
        if reverse:coords=coords[::-1];uvs=uvs[::-1]
        k=len(self.v);self.v.extend(coords);self.uv.extend(uvs);self.b.extend([bone]*len(coords))
        # Keep final triangulation and transparent face order explicit.
        if len(coords)==4:self.f.extend([(k,k+1,k+2),(k,k+2,k+3)])
        else:self.f.append(tuple(range(k,k+len(coords))))
    def object(self,name,mat):
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        uv=mesh.uv_layers.new(name='UVMap')
        for p in mesh.polygons:
            p.use_smooth=True
            for li in p.loop_indices:uv.data[li].uv=self.uv[mesh.loops[li].vertex_index]
        ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat)
        for name in sorted(set(self.b)):
            ids=[i for i,b in enumerate(self.b) if b==name];ob.vertex_groups.new(name=name).add(ids,1,'REPLACE')
        ob.parent=rig;ob.modifiers.new('WispRig','ARMATURE').object=rig
        return ob

def torus(mesh,seg,tube):
    def point(i,j):
        a=TAU*i/seg;b=TAU*j/tube;r=.140+.083*math.cos(b)+.006*math.sin(3*a+2*b)
        return (r*math.cos(a),r*math.sin(a),.070*math.sin(b)+.006*math.sin(4*a))
    # Reversed inner surface first, outward surface last: no opaque smoke or double-sided depth writes.
    for inward in (True,False):
        for i in range(seg):
            for j in range(tube):
                mesh.face([point(i,j),point(i+1,j),point(i+1,j+1),point(i,j+1)],
                    [(i/seg,j/tube),((i+1)/seg,j/tube),((i+1)/seg,(j+1)/tube),(i/seg,(j+1)/tube)],'Ring',inward)

def cards(mesh,bone,tile,width,height,planes=3):
    u0=(tile%4)/4;u1=u0+.25;v1=1-(tile//4)/4;v0=v1-.25
    uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
    for i in range(planes):
        a=math.pi*i/planes;side=Vector((math.cos(a),math.sin(a),0))*width*.5
        up=Vector((0,0,height*.5));coords=[-side-up,side-up,side+up,-side+up]
        for rev in (True,False):mesh.face(coords,uv,bone,rev)

objects=[];counts=[]
for lod,(seg,tube,smokes) in enumerate([(48,12,SMOKE),(32,8,10),(20,6,8),(12,4,6)]):
    suffix='' if lod==0 else f'_LOD{lod}'
    body=Mesh();torus(body,seg,tube);ob=body.object('WispRing'+suffix,bodymat);objects.append(ob)
    fx=Mesh()
    for i in range(smokes):cards(fx,f'Smoke{i:02d}',6+i%6,.18,.18,1)
    cards(fx,'Core',13,.30,.13,3);cards(fx,'Core',12,.23,.075,3)
    cards(fx,'Flash',14,.63,.63,3)
    ob=fx.object('WispSparks'+suffix,fxmat);objects.append(ob)
    counts.append(len(body.f)+len(fx.f))

previous_quaternions={}
def pose(name,location=(0,0,0),angles=(0,0,0),scale=1):
    b=rig.pose.bones[name];s=(scale,scale,scale) if isinstance(scale,(int,float)) else scale
    transform=Matrix.Translation(location)@Euler(angles,'XYZ').to_matrix().to_4x4()@Matrix.Diagonal((*s,1))
    b.rotation_mode='QUATERNION';b.matrix_basis=b.bone.matrix_local.inverted()@transform@b.bone.matrix_local
    if name in previous_quaternions and b.rotation_quaternion.dot(previous_quaternions[name])<0:
        b.rotation_quaternion.negate()
    previous_quaternions[name]=b.rotation_quaternion.copy()
    b.keyframe_insert('location',frame=scene.frame_current);b.keyframe_insert('rotation_quaternion',frame=scene.frame_current)
    b.keyframe_insert('scale',frame=scene.frame_current)

def animate(name,seconds):
    previous_quaternions.clear()
    action=bpy.data.actions.new(name);rig.animation_data_create();rig.animation_data.action=action
    frames=round(seconds*FPS);assert abs(frames/FPS-seconds)<1e-8
    for f in range(frames+1):
        scene.frame_set(f);t=f/FPS;q=f/frames;p=TAU*q
        attack=name=='Attack';dying=name=='Death';dead=name=='Dead';hit=name=='Hit'
        live=0 if dead else 1-smooth((t-.08)/.18) if dying else 1
        charge=smooth(t/.75) if attack and t<=.75 else 1-smooth((t-.75)/.23) if attack else 0
        hitpulse=pulse(t,0,.375) if hit else 0
        tilt=-.18 if name=='Walking' else 0
        pose('Root',(.012*math.sin(p),-.018*charge,.018*math.sin(p)),(.035*math.sin(p),0,0),1)
        pose('Ring',(0,0,.015*math.sin(2*p)),(.22+tilt+.075*math.sin(p),.08*math.sin(p+.4),p),
            (max(.0001,live*(1-.15*charge-.18*hitpulse)),)*3)
        pose('Core',(0,0,.012),(.22+tilt,0,0),max(.0001,live*(1+.20*math.sin(4*p)+.4*charge)))
        flash=(.12+.8*pulse(t,.53,.96)) if attack and .53<t<.96 else 1.2*pulse(t,0,.16) if dying else 0
        pose('Flash',(0,0,0),(0,0,0),max(.0001,flash))
        for i in range(SMOKE):
            angle=i*2.399963;z=1-2*(i+.5)/SMOKE;rad=math.sqrt(1-z*z)
            direction=Vector((rad*math.cos(angle),rad*math.sin(angle),z))
            distance=.20+.40*smooth(t/.5625) if dying else 0
            s=1.25*pulse(t,.06,.54) if dying else 0
            pose(f'Smoke{i:02d}',direction*distance,(0,0,i*.43),max(.0001,s))
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    action.use_fake_user=True

clips={'Standing':2.5,'Walking':1.25,'Attack':1.0}
if FULL:clips.update(Hit=.375,Death=.5625,Dead=1.)
for name,seconds in clips.items():animate(name,seconds)
rig.animation_data.action=bpy.data.actions['Standing'];scene.frame_set(0)
for ob in objects:ob.hide_render='_LOD' in ob.name;ob.hide_viewport='_LOD' in ob.name
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/m528_master.blend'))
for ob in objects:ob.hide_viewport=False
for ob in bpy.data.objects:ob.select_set(ob in objects or ob==rig or ob==socket)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m528_raw.glb'),use_selection=True,export_format='GLB',
    export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
    export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
    export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'export/export_info.json').write_text(json.dumps({'clips':clips,'triangles':counts,'bones':len(names),
    'scale':100,'origin':'Local ring centre at (0,0,0); runtime bindings lift it to the 128-pixel actor canvas centre.',
    'release_seconds':.75,'influences':1,'stage':'complete_clips' if FULL else 'pilot'},indent=2)+'\n')
assert counts[0] + 24 * 2 < 9000
assert all(a>b for a,b in zip(counts,counts[1:]))
print('BUILT',counts,clips)
