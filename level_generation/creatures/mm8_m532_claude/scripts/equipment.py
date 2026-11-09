"""Fit the bow grip to the measured hand, then build the native recurve bow, quiver, arrows and moving string."""
from pathlib import Path
import bpy,json,sys,math,itertools
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'));import posing as Q
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];Q.reset(rig)
names=('Index','Middle','Ring','Pinky')
kn=np.mean([rig.pose.bones['L'+n+'1'].head[:]for n in names],axis=0)
wr=np.array(rig.pose.bones['LHand'].head)
fdir=kn-wr;fdir/=np.linalg.norm(fdir)
axis=np.array(rig.pose.bones['LIndex1'].head-rig.pose.bones['LPinky1'].head);axis/=np.linalg.norm(axis)
normal=np.cross(axis,fdir);normal/=np.linalg.norm(normal)
tips=np.mean([rig.pose.bones['L'+n+'3'].tail[:]for n in names],axis=0)
if (tips-kn)@normal<0:normal=-normal
radius=.016
centre=kn-fdir*.015+normal*.028
co=np.array([v.co[:]for v in body.data.vertices])
palm=co[(np.linalg.norm(co-kn,axis=1)<.065)&(co[:,0]<kn[0]-.008)&(co[:,0]>.95)]
def radial(p,c=centre):
    q=p-c;return np.linalg.norm(q-np.outer(q@axis,axis),axis=1)
for _ in range(60):
    if len(palm)==0 or radial(palm).min()>radius+.002:break
    centre+=normal*.001

def points(name):return np.array([rig.pose.bones['L'+name+str(i)].head[:]for i in (1,2,3)]+[rig.pose.bones['L'+name+'3'].tail[:]])
def fk(js,ax,angles):
    out=js.copy()
    for i,a in enumerate(angles):
        rot=np.array(Matrix.Rotation(float(a),3,Vector(ax)));out[i+1:]=(out[i+1:]-out[i])@rot.T+out[i]
    return out

def cost(js,want):
    samples=np.concatenate([a+(b-a)*np.array([.25,.5,.75,1.])[:,None]for a,b in zip(js[:-1],js[1:])])
    r=radial(samples);return float(np.sum((r-want)**2+np.maximum(want-.001-r,0)**2*200))
report={}
for name in names:
    js=points(name);ax=axis.copy()
    if(np.array(Matrix.Rotation(.2,3,Vector(ax)))@(js[1]-js[0]))@normal<(js[1]-js[0])@normal:ax=-ax
    fit=json.loads((P/'work/hand_fit.json').read_text())['L']['digits'][name]
    skin=co[fit['vertices']];dist=[]
    for a,b in zip(js[:-1],js[1:]):
        d=b-a;t=np.clip((skin-a)@d/(d@d),0,1);dist.append(np.linalg.norm(skin-a-t[:,None]*d,axis=1))
    half=float(np.median(np.min(dist,axis=0)));want=radius+half+.0015
    grid=np.radians(np.arange(0,106,15));best=min((cost(fk(js,ax,a),want),a)for a in itertools.product(grid,repeat=3)if a[2]<=a[1])
    angles=np.array(best[1])
    for step in (6,2):
        for _ in range(3):
            options=[angles+np.radians(d)for d in itertools.product((-step,0,step),repeat=3)]
            valid=[a for a in options if np.all(a>=0)and np.all(a<=math.radians(115))and a[2]<=a[1]+.001]
            angles=min(valid,key=lambda a:cost(fk(js,ax,a),want))
    for i,a in enumerate(angles):Q.rotate_world(rig,'L'+name+str(i+1),Vector(ax),math.degrees(a))
    report[name]={'curl_degrees':np.degrees(angles).tolist(),'half_thickness':half}
# Thumb closes from its own measured root across the handle.
js=points('Thumb');best=(float('inf'),None)
for swing in np.radians(np.arange(-90,91,15)):
    R=np.array(Matrix.Rotation(float(swing),3,Vector(fdir)));pj=js.copy();pj[1:]=(pj[1:]-pj[0])@R.T+pj[0]
    ax=np.cross(pj[1]-pj[0],normal);ax/=np.linalg.norm(ax)
    for angles in itertools.product(np.radians(np.arange(-30,91,20)),repeat=3):
        score=cost(fk(pj,ax,angles)[1:],radius+.008)
        if score<best[0]:best=(score,(swing,ax,angles))
swing,ax,angles=best[1];Q.rotate_world(rig,'LThumb1',Vector(fdir),math.degrees(swing))
for i,a in enumerate(angles):Q.rotate_world(rig,'LThumb'+str(i+1),Vector(ax),math.degrees(a))
grip={b.name:list(b.rotation_quaternion)for b in rig.pose.bones if b.name.startswith('L')and any(n in b.name for n in (*names,'Thumb'))}
H=rig.data.bones['LHand'].matrix_local.copy();griplocal=H.inverted()@Vector(centre)
Q.reset(rig)
for o in bpy.context.scene.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')

def bone(name,parent,h,t,roll=(0,0,1)):
    b=rig.data.edit_bones.new(name);b.head=h;b.tail=t;b.parent=rig.data.edit_bones[parent];b.align_roll(Vector(roll))
bone('Bow','LHand',Vector(centre),Vector(centre+axis*.12),normal)
stringcentre=centre-normal*.16
bone('StringTop','Bow',Vector(centre+axis*.92-normal*.16),Vector(centre+axis*.94-normal*.16),normal)
bone('StringBottom','Bow',Vector(centre-axis*.92-normal*.16),Vector(centre-axis*.94-normal*.16),normal)
bone('StringNock','Bow',Vector(stringcentre),Vector(stringcentre+axis*.02),normal)
bone('Quiver','HorseChest',Vector((-.43,-.25,.87)),Vector((-.44,-.48,1.48)))
bone('Arrow','Root',Vector((0,0,0)),Vector((0,-.2,0)))
bpy.ops.object.mode_set(mode='OBJECT')
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
# One tiny authored material atlas serves every prop; detail is longitudinal wood/leather grain.
(P/'textures').mkdir(exist_ok=True)
size=256;yy,xx=np.mgrid[:size,:size];palette=np.array([[.24,.11,.045],[.40,.23,.075],[.13,.075,.035],[.56,.43,.25],[.10,.08,.06],[.72,.69,.60],[.26,.28,.29],[.32,.25,.17]])
colors=palette[np.minimum(xx//32,7)];noise=np.random.default_rng(532).normal(0,.012,(size,size,1));grain=.025*np.sin(yy[:,:,None]*.48+xx[:,:,None]*.17)
pix=np.concatenate([np.clip(colors+noise+grain,0,1),np.ones((size,size,1))],axis=2).astype(np.float32)
img=bpy.data.images.new('CentaurProps',width=size,height=size);img.pixels.foreach_set(pix.ravel());img.filepath_raw=str(P/'textures/centaur_props.png');img.file_format='PNG';img.save()
mat=bpy.data.materials.new('CentaurProps');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=img;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
verts=[];faces=[];uvs=[];weights=[]
def tube(pts,radii,binding,strip=0,segments=8,cap=True):
    start=len(verts);count=len(pts)
    for i,p in enumerate(pts):
        p=Vector(p);d=Vector(pts[min(i+1,count-1)])-Vector(pts[max(i-1,0)]);d.normalize();u=d.orthogonal().normalized();w=d.cross(u)
        r=radii[i]if isinstance(radii,list)else radii
        for k in range(segments):
            angle=2*math.pi*k/segments;verts.append(tuple(p+r*(math.cos(angle)*u+math.sin(angle)*w)))
            weights.append(binding[i]if isinstance(binding,list)else binding);uvs.append(((strip+.12+.76*k/segments)/8,i/max(1,count-1)))
    for i in range(count-1):
        for k in range(segments):
            a=start+i*segments+k;b=start+i*segments+(k+1)%segments;c=b+segments;d=a+segments;faces.extend([(a,b,c),(a,c,d)])
    if cap:
        for i,reverse in ((0,True),(count-1,False)):
            c=len(verts);verts.append(tuple(pts[i]));weights.append(binding[i]if isinstance(binding,list)else binding);uvs.append(((strip+.5)/8,.5))
            for k in range(segments):
                a=start+i*segments+k;b=start+i*segments+(k+1)%segments;faces.append((c,b,a)if reverse else(c,a,b))
steps=np.array([-.92,-.80,-.66,-.45,-.22,0,.22,.45,.66,.80,.92]);curve=np.array([-.16,-.04,.075,.09,.055,0,.055,.09,.075,-.04,-.16])
pts=[centre+axis*t+normal*f for t,f in zip(steps,curve)];tube(pts,[.009,.012,.018,.021,.022,radius,.022,.021,.018,.012,.009],'Bow',0)
for z in (-.78,-.46,-.22,.22,.46,.78):
    f=float(np.interp(z,steps,curve));c=centre+axis*z+normal*f;tube([c-axis*.009,c+axis*.009],.023,'Bow',1)
tube([centre-axis*.075,centre+axis*.075],radius,'Bow',2)
tube([centre+axis*.92-normal*.16,stringcentre],.002,['StringTop','StringNock'],4,segments=6)
tube([stringcentre,centre-axis*.92-normal*.16],.002,['StringNock','StringBottom'],4,segments=6)
qb=np.array((-.43,-.25,.87));qt=np.array((-.44,-.48,1.48));qd=(qt-qb)/np.linalg.norm(qt-qb)
tube([qb,qb*.7+qt*.3,qt], [.055,.072,.085],'Quiver',3,cap=False)
tube([qb-qd*.005,qb+qd*.025],.057,'Quiver',2)
tube([qt-qd*.028,qt],.089,'Quiver',1,cap=False)
for k in range(3):
    end=qt+qd*(.19+.045*k)+np.array((.035*(k-1),0,0));start=end-qd*.55
    tube([start,end],.004,'Quiver',0,segments=6)
    tube([end-qd*.11,end-qd*.02],[.018,.012],'Quiver',5,segments=6,cap=False)
tube([(0,0,0),(0,-.78,0)],.004,'Arrow',0,segments=6)
tube([(0,-.78,0),(0,-.85,0)],[.016,0.001],'Arrow',6,segments=6)
tube([(0,.01,0),(0,-.09,0)],[.014,.01],'Arrow',5,segments=6,cap=False)
mesh=bpy.data.meshes.new('Equipment');mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update();obj=bpy.data.objects.new('Equipment',mesh);bpy.context.collection.objects.link(obj);obj.parent=rig
uv=mesh.uv_layers.new(name='UVMap')
for f in mesh.polygons:
    f.use_smooth=True
    for li,vi in zip(f.loop_indices,f.vertices):uv.data[li].uv=uvs[vi]
for name in set(weights):
    g=obj.vertex_groups.new(name=name);g.add([i for i,n in enumerate(weights)if n==name],1,'REPLACE')
mod=obj.modifiers.new('Armature','ARMATURE');mod.object=rig
socket=bpy.data.objects.new('Socket_BowRelease',None);bpy.context.collection.objects.link(socket);socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='StringNock';socket.matrix_world=Matrix.Translation(Vector(stringcentre))
report.update(finger_local=grip,centre=list(centre),axis=list(axis),normal=list(normal),centre_hand_local=list(griplocal),radius=radius,prop_triangles=len(faces),rest_hand_matrix=[list(row)for row in H],bow_rest_matrix=[list(row)for row in rig.data.bones['Bow'].matrix_local])
(P/'work/equipment.json').write_text(json.dumps(report,indent=2,default=float)+'\n')
assert len(rig.data.bones)<128 and all(v.groups for v in mesh.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped_v1.blend'))
print('EQUIPMENT',len(faces),'triangles',len(rig.data.bones),'bones')
