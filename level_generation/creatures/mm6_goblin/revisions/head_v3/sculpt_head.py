"""Reference-driven goblin head sculpt. Run through Blender MCP, not ordinary Python."""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import ellipsoid,loft,tube,join,unify,subtract,mesh_object,active,apply,look_at

SCENE='MM6 Goblin head sculpt'

def surface_material(name,low,high,roughness=.53,metallic=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=roughness;bs.inputs['Metallic'].default_value=metallic
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=45
    tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.65
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2
    ramp.color_ramp.elements[0].color=(*low,1);ramp.color_ramp.elements[1].position=.8
    ramp.color_ramp.elements[1].color=(*high,1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=260
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.00045
    l.new(grain.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return mat

def skin_material():
    mat=surface_material('Goblin olive skin | restored reference pigment',(.025,.035,.008),(.10,.13,.027),.48)
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    bs.inputs['Subsurface Weight'].default_value=.035
    ref=n.new('ShaderNodeTexImage');ref.name='Reviewed AI restored face'
    ref.image=bpy.data.images.load(str(ROOT/'reference_restoration/head_v1.png'),check_existing=True)
    ref.image.pack();ref.extension='EXTEND'
    uv=n.new('ShaderNodeUVMap');uv.uv_map='Restored face projection';l.new(uv.outputs['UV'],ref.inputs['Vector'])
    mask=n.new('ShaderNodeVertexColor');mask.layer_name='Face projection blend'
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX'
    base=next(link.from_socket for link in list(l) if link.to_socket==bs.inputs['Base Color'])
    l.new(base,mix.inputs[1]);l.new(ref.outputs['Color'],mix.inputs[2]);l.new(mask.outputs['Color'],mix.inputs[0])
    l.new(mix.outputs[0],bs.inputs['Base Color'])
    return mat

def make_head():
    parts=[]
    # Sample a continuous facial surface. Relief belongs to the envelope, not stacked facial spheres.
    profile=[(1.575,.020,-.043,.035),(1.595,.060,-.077,.063),(1.615,.073,-.093,.072),
        (1.640,.080,-.098,.075),(1.670,.087,-.092,.084),(1.700,.101,-.084,.096),
        (1.730,.110,-.080,.109),(1.760,.112,-.081,.123),(1.790,.107,-.085,.144),
        (1.820,.100,-.078,.121),(1.850,.082,-.060,.100),(1.880,.049,-.024,.073),
        (1.905,.005,.027,.037)]
    vertices=[];faces=[];sides=160;rows=144
    def gaussian(x,c,w):return math.exp(-((x-c)/w)**2)
    for row in range(rows):
        z=1.575+(1.905-1.575)*row/(rows-1)
        k=next((i for i in range(len(profile)-1) if z<=profile[i+1][0]),len(profile)-2)
        a,b=profile[k:k+2];t=(z-a[0])/(b[0]-a[0])
        # Cubic Hermite slopes across adjacent sections avoid horizontal shelves at every ring landmark.
        previous=profile[max(0,k-1)];following=profile[min(len(profile)-1,k+2)]
        h=b[0]-a[0];values=[]
        for j in range(1,4):
            m0=(b[j]-previous[j])/(b[0]-previous[0])
            m1=(following[j]-a[j])/(following[0]-a[0])
            values.append((2*t**3-3*t*t+1)*a[j]+(t**3-2*t*t+t)*h*m0+
                (-2*t**3+3*t*t)*b[j]+(t**3-t*t)*h*m1)
        radius,front,back=values
        cy=(front+back)/2
        for i in range(sides):
            angle=i*2*math.pi/sides;c=math.cos(angle);x=radius*math.sin(angle)
            y=cy-(cy-front)*max(c,0)**.58 if c>=0 else cy+(back-cy)*(-c)**.9
            if c>0:
                relief=.0
                for side in [-1,1]:
                    relief+=.018*gaussian(x,side*.050,.036)*gaussian(z,1.773+.07*abs(x),.019)
                    relief-=.018*gaussian(x,side*.051,.025)*gaussian(z,1.744,.014)
                    relief+=.012*gaussian(x,side*.077,.026)*gaussian(z,1.711,.022)
                    relief-=.008*gaussian(x,side*.070,.021)*gaussian(z,1.676,.021)
                    relief+=.008*gaussian(x,side*.023,.012)*gaussian(z,1.711,.010)
                relief+=.049*gaussian(x,0,.023)*gaussian(z,1.719,.018)
                relief+=.023*gaussian(x,0,.017)*gaussian(z,1.748,.025)
                relief+=.009*gaussian(x,0,.050)*gaussian(z,1.670,.010)
                relief+=.011*gaussian(x,0,.055)*gaussian(z,1.641,.010)
                relief+=.013*gaussian(x,0,.047)*gaussian(z,1.613,.016)
                # Modest connected skin folds and frown creases, below the level of anatomical masses.
                relief-=.003*gaussian(x,0,.005)*gaussian(z,1.786,.032)
                fold_x=.023+(1.711-z)*.6
                relief+=.0035*gaussian(abs(x),fold_x,.004)*gaussian(z,1.686,.025)
                y-=relief*c**.4
            else:
                y+=.045*gaussian(z,1.772,.021)*(-c)**6
            vertices.append((x,y,z))
    for row in range(rows-1):
        for i in range(sides):
            j=row*sides+i;k=row*sides+(i+1)%sides;faces.append((j,k,k+sides,j+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((rows-1)*sides+i for i in range(sides))])
    head=mesh_object('Goblin head | continuous sculpt',vertices,faces)
    for side in [-1,1]:
        subtract(head,ellipsoid('Nostril opening',(side*.015,-.119,1.706),(.007,.011,.005)))
    subtract(head,ellipsoid('Real mouth opening',(0,-.111,1.655),(.054,.024,.0085)))
    # Low-frequency sculpt refinement; texture adds fine surface grain without distorting silhouette.
    m=head.modifiers.new('Reduce sculpt for animation','DECIMATE');m.ratio=.70;apply(head,m)
    skin=skin_material();head.data.materials.clear();head.data.materials.append(skin)
    uv=head.data.uv_layers.new(name='Restored face projection')
    mask=head.data.color_attributes.new(name='Face projection blend',type='FLOAT_COLOR',domain='CORNER')
    for poly in head.data.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            v=head.data.vertices[head.data.loops[li].vertex_index].co
            uv.data[li].uv=((430+1520*v.x)/1672,1-(110+(1.905-v.z)*1520)/941)
            frontal=max(0,min(1,(-v.y-.025)/.050))
            lateral=max(0,min(1,(.119-abs(v.x))/.025))
            w=frontal*lateral
            mask.data[li].color=(w,w,w,1)
    objects=[head]
    ear_skin=surface_material('Goblin ear olive rim',(.025,.040,.010),(.10,.13,.030),.5)
    ear_inner=surface_material('Goblin ear warm interior',(.037,.026,.009),(.12,.080,.030),.55)
    for side in [-1,1]:
        # Concave pinna with a continuous outer helix and inner cartilage folds.
        outline=[(.105,.015,1.704),(.126,.017,1.713),(.139,.034,1.753),(.151,.050,1.800),
            (.183,.078,1.895),(.146,.039,1.851),(.122,.015,1.811),(.102,.002,1.777)]
        outline=[(side*x,y,z) for x,y,z in outline]
        # Concentric concave surface with curved cartilage; no flat triangular fan as the final pinna.
        center=Vector((side*.126,.027,1.773));verts=[tuple(center)];faces=[]
        for ring in range(1,7):
            t=ring/6
            for p in outline:
                v=center.lerp(Vector(p),t)
                v.y+=.012*math.sin(math.pi*t)
                verts.append(tuple(v))
        for i in range(len(outline)):faces.append((0,1+i,1+(i+1)%len(outline)))
        for ring in range(5):
            for i in range(len(outline)):
                j=1+ring*len(outline)+i;k=1+ring*len(outline)+(i+1)%len(outline)
                faces.append((j,k,k+len(outline),j+len(outline)))
        ear=mesh_object('Goblin ear pinna',verts,faces,ear_inner)
        m=ear.modifiers.new('Pinna curvature','SUBSURF');m.levels=2;apply(ear,m)
        m=ear.modifiers.new('Pinna thickness','SOLIDIFY');m.thickness=.008;apply(ear,m)
        objects.append(ear)
        rim=tube('Ear helix',outline+[outline[0]],[.005,.007,.006,.004,.001,.004,.006,.007,.005],ear_skin,sides=12)
        objects.append(rim)
        objects.append(tube('Inner ear cartilage',[(side*.110,.000,1.728),(side*.128,.009,1.758),
            (side*.133,.018,1.790),(side*.156,.040,1.850)],[.005,.005,.004,.001],ear_skin,sides=10))
        objects.append(ellipsoid('Ear lobe',(side*.115,.008,1.719),(.015,.015,.020),ear_skin))
    dark=surface_material('Goblin mouth and nostril depth',(.002,.003,.001),(.015,.012,.005),.7)
    objects.append(ellipsoid('Mouth interior',(0,-.089,1.655),(.054,.008,.010),dark))
    tooth=surface_material('Goblin aged teeth and claws',(.19,.16,.075),(.50,.43,.23),.35)
    for lower in [False,True]:
        for i in range(8):
            x=(i-3.5)*.012;z=1.649 if lower else 1.662
            length=.007 if lower else .008
            if lower and i in [1,6]:length=.012
            x+=.003 if lower else 0
            if lower and i in [1,6]:
                objects.append(tube('Small lower canine',[(x,-.102+2*x*x,z),
                    (x,-.109+2*x*x,z+length)],[.0035,.001],tooth,sides=12))
            else:
                objects.append(ellipsoid('Lower tooth' if lower else 'Upper tooth',
                    (x,-.108+2*x*x,z+(length*.4 if lower else -length*.4)),
                    (.0034,.004,.0043),tooth,rotation=(0,(i%3-1)*.10,0),segments=16,rings=12))
    eye=surface_material('Goblin eye sclera ochre',(.13,.085,.020),(.36,.25,.060),.22)
    iris=surface_material('Goblin amber iris',(.21,.095,.004),(.70,.43,.035),.22)
    pupil=surface_material('Goblin dark pupils',(.001,.001,.001),(.005,.003,.001),.18)
    for side in [-1,1]:
        objects.append(ellipsoid('Eyeball',(side*.051,-.064,1.741),(.022,.022,.012),eye))
        objects.append(ellipsoid('Amber iris',(side*.051,-.084,1.741),(.009,.0025,.008),iris))
        objects.append(ellipsoid('Pupil',(side*.051,-.086,1.741),(.0035,.001,.0055),pupil))
        objects.append(tube('Upper eyelid',[(side*.030,-.079,1.743),(side*.040,-.088,1.749),
            (side*.055,-.089,1.751),(side*.073,-.073,1.744)],[.005,.0055,.005,.0035],ear_skin,sides=12))
        objects.append(tube('Lower eyelid',[(side*.030,-.075,1.740),(side*.044,-.081,1.732),
            (side*.061,-.080,1.732),(side*.073,-.073,1.744)],[.0035,.0035,.003,.0035],ear_skin,sides=12))
    gold=surface_material('Goblin worn brass jewelry',(.15,.095,.025),(.46,.31,.075),.3,.8)
    for x,z,radius in [(-.131,1.747,.013),(-.136,1.724,.015),(-.135,1.700,.016)]:
        bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.0025,
            major_segments=32,minor_segments=8,location=(x,-.003,z),rotation=(math.pi/2,.25,0))
        obj=bpy.context.object;obj.name='Right ear brass ring';obj.data.materials.append(gold);objects.append(obj)
    return objects

def build():
    (ROOT/'sculpt').mkdir(exist_ok=True);(ROOT/'review').mkdir(exist_ok=True)
    old=bpy.data.scenes.get(SCENE)
    if old:
        raise RuntimeError('Inspect existing head sculpt scene before an explicit rebuild')
    scene=bpy.data.scenes.new(SCENE);bpy.context.window.scene=scene
    objects=make_head()
    data=bpy.data.cameras.new('Goblin sculpt camera');data.type='ORTHO';data.ortho_scale=.55
    camera=bpy.data.objects.new('Goblin sculpt camera',data);scene.collection.objects.link(camera);scene.camera=camera
    for name,pos,power,size in [('Key',(-1,-2,3),55,1.4),('Fill',(1,-1,2),16,1.0),('Rim',(0,1,2.3),9,.8)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=size
        obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=pos;look_at(obj,(0,0,1.75))
    world=bpy.data.worlds.new('Goblin neutral studio');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs[0].default_value=(.25,.25,.25,1)
    world.node_tree.nodes.get('Background').inputs[1].default_value=.3;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    # Save the construction before render review, so interruption cannot lose the sculpt.
    camera.location=(0,-2,1.74);look_at(camera,(0,0,1.74))
    bpy.data.libraries.write(str(ROOT/'sculpt/head_sculpt_library.blend'),{scene},fake_user=True)
    for angle,label in [(0,'front'),(45,'three_quarter'),(90,'profile'),(180,'back')]:
        a=math.radians(angle);camera.location=(2*math.sin(a),-2*math.cos(a),1.74)
        look_at(camera,(0,0,1.74));scene.render.filepath=str(ROOT/'review'/f'head_v3_{label}.png')
        bpy.ops.render.render(write_still=True)
    camera.location=(0,-2,1.74);look_at(camera,(0,0,1.74))
    report={'objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),
        'faces':sum(len(o.data.polygons) for o in objects),'status':'First sculpt review, not accepted final model'}
    (ROOT/'sculpt/head_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':build()
