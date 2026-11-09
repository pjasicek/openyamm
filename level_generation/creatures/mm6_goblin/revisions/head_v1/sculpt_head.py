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
    mat=surface_material('Goblin olive skin | restored reference pigment',(.09,.115,.029),(.26,.28,.075),.48)
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
    # Compact continuous cranial and facial envelope with a tapering crown.
    sections=[(1.575,0,-.005,.036,.051),(1.595,0,-.015,.065,.069),
        (1.625,0,0,.079,.080),(1.660,0,.010,.092,.079),(1.700,0,.015,.105,.083),
        (1.735,0,.012,.113,.089),(1.770,0,.016,.113,.103),(1.810,0,.022,.108,.105),
        (1.850,0,.025,.085,.089),(1.879,0,.029,.054,.065),(1.905,0,.030,.007,.012)]
    base=loft('Continuous goblin cranial envelope',sections,sides=64);parts.append(base)
    # Jaw, muzzle and cheek transitions merge into the continuous face rather than remain separate beads.
    parts.append(ellipsoid('Projecting mandible',(0,-.042,1.613),(.074,.064,.040)))
    parts.append(ellipsoid('Upper muzzle',(0,-.087,1.674),(.065,.041,.028)))
    parts.append(ellipsoid('Lower lip and chin',(0,-.089,1.636),(.064,.043,.027)))
    parts.append(ellipsoid('Nasal bridge',(0,-.088,1.751),(.026,.037,.040)))
    parts.append(ellipsoid('Broad nasal tip',(0,-.124,1.716),(.026,.030,.023)))
    for side in [-1,1]:
        parts.append(ellipsoid('Nostril wing',(side*.022,-.110,1.711),(.018,.026,.014)))
        parts.append(ellipsoid('Malar cheek',(side*.079,-.052,1.707),(.034,.039,.042),rotation=(0,side*.3,0)))
        parts.append(ellipsoid('Heavy sloped brow',(side*.050,-.078,1.777),(.055,.039,.027),rotation=(0,-side*.16,0)))
        parts.append(tube('Nasolabial fold',[(side*.027,-.099,1.704),(side*.041,-.103,1.688),
            (side*.058,-.090,1.667)],[.009,.007,.006],sides=12))
    parts.append(ellipsoid('Swept occipital ridge',(0,.108,1.790),(.074,.089,.047)))
    # Taper the occiput into its native backward-projecting profile point.
    parts.append(tube('Occipital taper',[(0,.095,1.79),(0,.17,1.765),(0,.205,1.756)],
        [.048,.025,.002],sides=24,flatten=.7))
    head=unify(parts,'Goblin head | continuous sculpt',voxel=.0025,smooth=5)
    for side in [-1,1]:
        subtract(head,ellipsoid('Orbital recess',(side*.051,-.092,1.741),(.030,.040,.019),rotation=(0,-side*.05,0)))
        subtract(head,ellipsoid('Nostril opening',(side*.018,-.137,1.705),(.009,.015,.007)))
    subtract(head,ellipsoid('Real mouth opening',(0,-.127,1.655),(.060,.041,.012)))
    # Low-frequency sculpt refinement; texture adds fine surface grain without distorting silhouette.
    m=head.modifiers.new('Reduce sculpt for animation','DECIMATE');m.ratio=.42;apply(head,m)
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
    ear_skin=surface_material('Goblin ear olive rim',(.065,.085,.024),(.22,.24,.063),.5)
    ear_inner=surface_material('Goblin ear warm interior',(.09,.059,.025),(.24,.17,.063),.55)
    for side in [-1,1]:
        # Concave pinna with a continuous outer helix and inner cartilage folds.
        outline=[(.105,.015,1.704),(.126,.017,1.713),(.139,.034,1.753),(.151,.050,1.800),
            (.183,.078,1.895),(.146,.039,1.851),(.122,.015,1.811),(.102,.002,1.777)]
        outline=[(side*x,y,z) for x,y,z in outline]
        center=(side*.126,.033,1.773);verts=[center]+outline
        faces=[(0,1+i,1+(i+1)%len(outline)) for i in range(len(outline))]
        ear=mesh_object('Goblin ear pinna',verts,faces,ear_inner)
        m=ear.modifiers.new('Pinna thickness','SOLIDIFY');m.thickness=.008;apply(ear,m)
        objects.append(ear)
        rim=tube('Ear helix',outline+[outline[0]],[.005,.007,.006,.004,.001,.004,.006,.007,.005],ear_skin,sides=12)
        objects.append(rim)
        objects.append(tube('Inner ear cartilage',[(side*.110,.000,1.728),(side*.128,.009,1.758),
            (side*.133,.018,1.790),(side*.156,.040,1.850)],[.005,.005,.004,.001],ear_skin,sides=10))
        objects.append(ellipsoid('Ear lobe',(side*.115,.008,1.719),(.015,.015,.020),ear_skin))
    dark=surface_material('Goblin mouth and nostril depth',(.002,.003,.001),(.015,.012,.005),.7)
    objects.append(ellipsoid('Mouth interior',(0,-.091,1.655),(.059,.014,.015),dark))
    tooth=surface_material('Goblin aged teeth and claws',(.19,.16,.075),(.50,.43,.23),.35)
    for lower in [False,True]:
        for i in range(8):
            x=(i-3.5)*.0135;z=1.646 if lower else 1.666
            length=.010 if lower else .012
            if lower and i in [1,6]:length=.019
            objects.append(tube('Lower tooth' if lower else 'Upper tooth',
                [(x,-.117+2*x*x,z),(x,-.125+2*x*x,z+(length if lower else -length))],
                [.005,.001],tooth,sides=10))
    eye=surface_material('Goblin eye sclera ochre',(.13,.085,.020),(.36,.25,.060),.22)
    iris=surface_material('Goblin amber iris',(.21,.095,.004),(.70,.43,.035),.22)
    pupil=surface_material('Goblin dark pupils',(.001,.001,.001),(.005,.003,.001),.18)
    for side in [-1,1]:
        objects.append(ellipsoid('Eyeball',(side*.051,-.078,1.741),(.025,.024,.017),eye))
        objects.append(ellipsoid('Amber iris',(side*.051,-.100,1.741),(.011,.004,.010),iris))
        objects.append(ellipsoid('Pupil',(side*.051,-.103,1.741),(.0045,.0018,.007),pupil))
        objects.append(tube('Lower eyelid',[(side*.077,-.081,1.741),(side*.067,-.096,1.729),
            (side*.049,-.099,1.727),(side*.029,-.084,1.735)],[.004,.004,.004,.003],ear_skin,sides=10))
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
    for name,pos,power,size in [('Key',(-1,-2,3),95,1.4),('Fill',(1,-1,2),35,1.0),('Rim',(0,1,2.3),50,.8)]:
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
        look_at(camera,(0,0,1.74));scene.render.filepath=str(ROOT/'review'/f'head_v1_{label}.png')
        bpy.ops.render.render(write_still=True)
    camera.location=(0,-2,1.74);look_at(camera,(0,0,1.74))
    report={'objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),
        'faces':sum(len(o.data.polygons) for o in objects),'status':'First sculpt review, not accepted final model'}
    (ROOT/'sculpt/head_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':build()
