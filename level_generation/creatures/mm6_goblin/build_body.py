"""Original full-body goblin construction from the reviewed native/restored views; Blender MCP entry."""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import *
from sculpt_head import surface_material

SCENE='MM6 Goblin body studio'

def g(x,c,w):return math.exp(-((x-c)/w)**2)

def dense_sections(control,steps=5):
    result=[]
    for i in range(len(control)-1):
        a,b=control[i:i+2];prev=control[max(0,i-1)];nxt=control[min(len(control)-1,i+2)]
        for j in range(steps):
            t=j/steps;h=b[0]-a[0];row=[a[0]+h*t]
            for k in range(1,len(a)):
                m0=(b[k]-prev[k])/(b[0]-prev[0]);m1=(nxt[k]-a[k])/(nxt[0]-a[0])
                row.append((2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*h*m0+
                    (-2*t**3+3*t*t)*b[k]+(t**3-t*t)*h*m1)
            result.append(tuple(row))
    return result+[control[-1]]

def skin_surface():
    mat=surface_material('Body olive skin',(.025,.035,.008),(.10,.13,.027),.48)
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Subsurface Weight'].default_value=.035
    ref=n.new('ShaderNodeTexImage');ref.image=bpy.data.images.load(str(ROOT/'textures/olive_skin.png'),check_existing=True)
    ref.image.pack()
    coord=n.new('ShaderNodeAttribute');coord.attribute_name='SculptPosition'
    scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=3.0
    l.new(coord.outputs['Vector'],scale.inputs[0]);l.new(scale.outputs[0],ref.inputs[0])
    ref.projection='BOX';ref.projection_blend=.25
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.48,.60,.43,1);l.new(ref.outputs['Color'],tint.inputs[1])
    portrait=n.new('ShaderNodeTexImage');portrait.image=bpy.data.images.load(str(ROOT/'reference_restoration/turnaround_v1.png'),check_existing=True)
    uv=n.new('ShaderNodeUVMap');uv.uv_map='Body reference projection';l.new(uv.outputs[0],portrait.inputs[0])
    mask=n.new('ShaderNodeVertexColor');mask.layer_name='Body reference blend'
    mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(tint.outputs[0],mix.inputs[1])
    l.new(portrait.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    for node in n:
        if node.type=='TEX_NOISE':l.new(coord.outputs['Vector'],node.inputs['Vector'])
    return mat

def build_skin():
    parts=[]
    control=[(.87,0,0,.10,.075),(.94,0,0,.172,.111),(1.015,0,0,.164,.105),
        (1.09,0,0,.143,.088),(1.18,0,0,.162,.101),(1.28,0,0,.198,.118),
        (1.37,0,0,.230,.128),(1.43,0,.005,.215,.108),(1.49,0,.005,.105,.069),
        (1.53,0,.015,.071,.064),(1.59,0,.015,.065,.060)]
    def torso(v,a):
        x,y,z=v;c=math.cos(a)
        if c>0:
            relief=.0
            for s in [-1,1]:
                relief+=.022*g(x,s*.11,.073)*g(z,1.345,.047)
                for zz,amp in [(1.245,.013),(1.190,.012),(1.135,.010)]:relief+=amp*g(x,s*.048,.033)*g(z,zz,.022)
                relief+=.010*g(x,s*.135,.028)*g(z,1.19,.105)
            relief-=.005*g(x,0,.008)*g(z,1.26,.14)
            relief-=.006*g(x,0,.012)*g(z,1.102,.012)
            y-=relief*c
        else:
            y+=.013*g(abs(x),.09,.06)*g(z,1.30,.15)*(-c)
            y-=.006*g(x,0,.010)*g(z,1.25,.2)
        return (x,y,z)
    parts.append(loft('Torso anatomical surface',dense_sections(control,6),sides=64,deform=torso))
    finger_paths={}
    for side,label in [(-1,'R'),(1,'L')]:
        # Shoulder through wrist. Changes in section thickness give connected deltoid/biceps/forearm anatomy.
        sections=[(.94,side*.413,-.005,.032,.039),(1.005,side*.405,0,.042,.047),
            (1.10,side*.390,.009,.058,.061),(1.17,side*.366,.012,.047,.048),
            (1.245,side*.338,.004,.064,.067),(1.33,side*.302,0,.078,.075),
            (1.41,side*.267,.002,.091,.088),(1.47,side*.240,.005,.068,.068)]
        def arm_detail(v,a):
            x,y,z=v;c=math.cos(a)
            y-=.013*g(z,1.285,.063)*max(c,0)
            y+=.010*g(z,1.316,.073)*max(-c,0)
            return (x,y,z)
        parts.append(loft('Arm '+label,dense_sections(sections,5),sides=40,deform=arm_detail))
        # Palm silhouette and knuckles, with long individually tapered digits.
        if side>0:
            palm_sections=[(.832,.427,-.026,.041,.018),(.855,.426,-.026,.050,.026),
                (.887,.421,-.020,.043,.030),(.925,.417,-.011,.034,.034),(.962,.409,-.003,.036,.042)]
        else:
            palm_sections=[(.861,-.413,-.021,.025,.050),(.885,-.412,-.021,.028,.055),
                (.922,-.413,-.013,.031,.038),(.962,-.409,-.003,.036,.042)]
        palm=loft('Continuous palm and wrist '+label,dense_sections(palm_sections,6),sides=32)
        parts.append(palm)
        for i in range(4):
            x=side*(.395+i*.021)
            if side==1:
                length=[.124,.150,.141,.113][i]
                path=[(x,-.027,.857),(x+side*.012,-.033,.825),
                    (x+side*.018,-.057,.857-length*.70),(x+side*.010,-.080,.857-length)]
            else:
                # Fingers close around the sword grip; their contact is a later rig review gate.
                y=-.065+i*.022
                path=[(-.454,y,.886),(-.461,y-.006,.858),(-.438,y-.008,.847),(-.417,y-.004,.866)]
            parts.append(tube(f'{label} finger {i}',path,[.013,.012,.009,.006],sides=12,flatten=.85))
            finger_paths[f'finger_{i}.{label}']=path
        if side==1:path=[(.395,-.012,.908),(.370,-.022,.878),(.365,-.052,.847),(.374,-.070,.827)]
        else:path=[(-.394,-.019,.910),(-.405,-.045,.908),(-.421,-.054,.887)]
        parts.append(tube('Thumb '+label,path,[.017,.015,.009,.006] if side==1 else [.017,.014,.008],sides=14))
        finger_paths[f'thumb.{label}']=path
        leg=[(.105,side*.133,.022,.034,.047),(.185,side*.133,.022,.041,.052),
            (.295,side*.133,.025,.065,.066),(.395,side*.132,.011,.060,.064),
            (.49,side*.129,-.012,.052,.057),(.565,side*.128,0,.066,.070),
            (.69,side*.122,.012,.086,.083),(.84,side*.110,.005,.096,.092),(.965,side*.100,0,.082,.085)]
        def leg_detail(v,a):
            x,y,z=v;c=math.cos(a)
            y-=.016*g(z,.73,.12)*max(c,0)+.011*g(z,.53,.036)*max(c,0)
            return (x,y,z)
        parts.append(loft('Leg '+label,dense_sections(leg,5),sides=40,deform=leg_detail))
        parts.append(tube('Foot arch '+label,[(side*.133,.060,.090),(side*.133,.008,.080),
            (side*.133,-.068,.058),(side*.133,-.124,.045)],[.043,.056,.073,.059],sides=24,flatten=.68))
        parts.append(ellipsoid('Heel pad '+label,(side*.133,.032,.076),(.045,.051,.060)))
        for i in range(4):
            x=side*(.081+i*.034);length=[.143,.160,.146,.120][i]
            path=[(x,-.083,.072),(x,-.147,.059),(x,-.083-length,.040)]
            parts.append(tube('Toe '+label+str(i),path,[.022,.016,.010],sides=16,flatten=.85))
            parts.append(tube('Foot tendon '+label+str(i),[(side*.133,.015,.108),
                (x,-.080,.096),(x,-.147,.075)],[.005,.006,.004],sides=10))
            finger_paths[f'toe_{i}.{label}']=path
    skin=unify(parts,'Goblin body | connected skin',voxel=.0035,smooth=3,decimate=.35)
    mat=skin_surface();skin.data.materials.clear();skin.data.materials.append(mat)
    rest=skin.data.attributes.new(name='SculptPosition',type='FLOAT_VECTOR',domain='POINT')
    for v in skin.data.vertices:rest.data[v.index].vector=v.co
    uv=skin.data.uv_layers.new(name='Body reference projection')
    mask=skin.data.color_attributes.new(name='Body reference blend',type='FLOAT_COLOR',domain='CORNER')
    for poly in skin.data.polygons:
        for li in poly.loop_indices:
            v=skin.data.vertices[skin.data.loops[li].vertex_index].co
            uv.data[li].uv=((201+367*v.x)/1672,1-(797.4-370*v.z)/941)
            # Use restored torso pigment only on exposed matching surfaces; no armor painted onto limbs.
            w=max(0,min(1,(-v.y-.04)/.05))*max(0,min(1,(.19-abs(v.x))/.035))
            w*=max(0,min(1,(v.z-1.075)/.045))*max(0,min(1,(1.26-v.z)/.035))
            mask.data[li].color=(.72*w,.72*w,.72*w,1)
    return skin,finger_paths

def patch(name,outline,center,surface,mat):
    verts=[surface(*center)];faces=[];count=len(outline)
    for ring in range(1,7):
        t=ring/6
        for p in outline:verts.append(surface(center[0]+t*(p[0]-center[0]),center[1]+t*(p[1]-center[1])))
    for i in range(count):faces.append((0,1+i,1+(i+1)%count))
    for row in range(5):
        for i in range(count):
            j=1+row*count+i;k=1+row*count+(i+1)%count;faces.append((j,k,k+count,j+count))
    obj=mesh_object(name,verts,faces,mat);solidify(obj,.007,.0018)
    return obj

def build_costume(paths):
    metal=surface_material('Worn dark iron',(.013,.014,.015),(.062,.067,.071),.66,.48)
    edge=surface_material('Iron edge wear',(.07,.075,.075),(.19,.20,.20),.38,.7)
    brass=surface_material('Aged brass fittings',(.10,.054,.013),(.38,.24,.055),.36,.78)
    leather=surface_material('Brown leather',(.007,.0025,.001),(.035,.012,.003),.76)
    # Broad forging variations plus fine pitting, measured in rest-space meters rather than each part's bounds.
    n=metal.node_tree.nodes;l=metal.node_tree.links
    rest_coord=n.new('ShaderNodeAttribute');rest_coord.attribute_name='SculptPosition'
    for node in n:
        if node.type=='TEX_NOISE':l.new(rest_coord.outputs['Vector'],node.inputs['Vector'])
    pits=n.new('ShaderNodeTexNoise');pits.inputs['Scale'].default_value=420
    pits.inputs['Detail'].default_value=2;l.new(rest_coord.outputs['Vector'],pits.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.38;bump.inputs['Distance'].default_value=.0012
    l.new(pits.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
    n=leather.node_tree.nodes;l=leather.node_tree.links
    texture=n.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(ROOT/'textures/brown_leather.png'),check_existing=True)
    texture.image.pack();texture.projection='BOX';texture.projection_blend=.25
    coord=n.new('ShaderNodeAttribute');coord.attribute_name='SculptPosition'
    scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=5
    l.new(coord.outputs['Vector'],scale.inputs[0]);l.new(scale.outputs[0],texture.inputs[0])
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.40,.30,.22,1)
    l.new(texture.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    for node in n:
        if node.type=='TEX_NOISE':l.new(coord.outputs['Vector'],node.inputs['Vector'])
    claw=surface_material('Horn claws',(.11,.085,.027),(.36,.28,.105),.37)
    steel=surface_material('Scimitar steel',(.20,.21,.23),(.42,.44,.47),.28,.83)
    objects=[]
    def keep(o,bone):objects.append(weighted(o,bone));return o
    def rivet(point,bone,r=.004,mat=brass):return keep(ellipsoid('Armor rivet',point,(r,r*.65,r),mat,segments=12,rings=8),bone)
    def spike(point,direction,bone,length=.035):
        p=Vector(point);d=Vector(direction).normalized()
        return keep(tube('Forged armor spike',[p,p+d*length*.55,p+d*length],[.009,.0045,.0005],brass,sides=10),bone)
    outline=[(-.182,1.457),(-.117,1.427),(0,1.413),(.117,1.427),(.182,1.457),(.148,1.360),
        (.075,1.303),(0,1.275),(-.075,1.303),(-.148,1.360)]
    surface=lambda x,z:(x,-.153+.18*x*x+max(0,z-1.4)*.4,z)
    keep(patch('Chest gorget',outline,(0,1.371),surface,metal),'chest')
    keep(tube('Gorget forged rim',[surface(*p) for p in outline+[outline[0]]],[.003]*11,edge,sides=10),'chest')
    for x,z in outline:rivet((x*.92,surface(x,z)[1]-.005,(z-1.37)*.88+1.37),'chest')
    for x,z in [(-.09,1.385),(.09,1.385),(0,1.345)]:rivet((x,-.160,z),'chest',.007)
    for x,z in [(-.135,1.405),(-.118,1.360),(-.054,1.333),(.135,1.405),(.118,1.360),(.054,1.333),
        (-.047,1.396),(.047,1.396),(0,1.307)]:rivet((x,surface(x,z)[1]-.006,z),'chest',.0045,edge)
    for side,label in [(-1,'R'),(1,'L')]:
        # Upper-back plates remain separate as in the native rear view.
        outline=[(.018,1.459),(.135,1.467),(.184,1.394),(.157,1.345),(.027,1.36)]
        surf=lambda x,z:(side*x,.155*math.sqrt(max(.1,1-(x/.26)**2)),z)
        keep(patch('Upper back plate '+label,outline,(.09,1.410),surf,metal),'chest')
        for x,z in outline:rivet((side*x,surf(x,z)[1]+.005,z),'chest')
        # Shoulder cap, covering the upper deltoid with a rolled perimeter.
        verts=[];faces=[];rings=10;sides=40
        for row in range(rings):
            theta=.06+1.95*row/(rings-1)
            for i in range(sides):
                a=i*2*math.pi/sides
                xx=.266+.107*math.sin(theta)*math.cos(a)
                verts.append((side*xx,.107*math.sin(theta)*math.sin(a),
                    1.422+.095*math.cos(theta)-.48*(xx-.266)))
        for row in range(rings-1):
            for i in range(sides):
                j=row*sides+i;k=row*sides+(i+1)%sides;faces.append((j,k,k+sides,j+sides))
        cap=mesh_object('Shoulder cap '+label,verts,faces,metal);solidify(cap,.008,.002);keep(cap,'upper_arm.'+label)
        rim=verts[-sides:];keep(tube('Shoulder rim '+label,rim+[rim[0]],[.0035]*(sides+1),edge,sides=8),'upper_arm.'+label)
        for a in [-1.5,-.7,0,.7,1.5]:
            point=(side*(.266+.091*math.cos(a)),.091*math.sin(a),1.472-.48*.091*math.cos(a))
            spike(point,(side*math.cos(a),math.sin(a),.5),'upper_arm.'+label,.033)
        for i in range(0,sides,4):
            point=Vector(rim[i]);point.z+=.008;rivet(point,'upper_arm.'+label,.0035,edge)
        # Open-backed bracer and greave, each with real thickness and separate rear straps.
        for kind,zs,cxs,rs,cy,bone in [
            ('Forearm',[.980,1.015,1.10,1.17],[.409,.403,.390,.368],[.045,.049,.066,.059],.0,'forearm.'+label),
            ('Shin',[.13,.18,.29,.42,.49],[.133]*5,[.044,.049,.076,.069,.058],.012,'shin.'+label)]:
            verts=[];faces=[];n=28
            for row,(z,cx,r) in enumerate(zip(zs,cxs,rs)):
                for i in range(n):
                    a=-2.15+4.30*i/(n-1)
                    zz=z
                    if row==len(zs)-1:zz+=.025*max(0,math.cos(a))**3-.034*(abs(a)/2.15)**1.3
                    if row==0:zz+=.014*math.cos(a)
                    ridge=.007*math.exp(-(a/.30)**2)*math.sin(math.pi*row/(len(zs)-1))
                    verts.append((side*cx+r*math.sin(a),cy-r*math.cos(a)-ridge,zz))
            for row in range(len(zs)-1):
                for i in range(n-1):
                    j=row*n+i;faces.append((j,j+1,j+1+n,j+n))
            obj=mesh_object(kind+' guard '+label,verts,faces,metal);solidify(obj,.006,.002);keep(obj,bone)
            border=verts[:n]+[verts[row*n+n-1] for row in range(1,len(zs))]+list(reversed(verts[-n:-1]))+[
                verts[row*n] for row in reversed(range(1,len(zs)-1))]
            keep(tube(kind+' rolled edge '+label,border+[border[0]],[.0028]*(len(border)+1),edge,sides=8),bone)
            for row,(z,cx,r) in enumerate(zip(zs,cxs,rs)):
                if row not in [0,len(zs)-1]:spike((side*cx,cy-r-.003,z),(side*.35,-1,.1),bone,.030)
                for a in [-1.8,1.8]:rivet((side*cx+r*math.sin(a),cy-r*math.cos(a)-.003,z),bone,.0035)
            for z,cx,r in [(zs[0]+.016,cxs[0],rs[0]),(zs[-1]-.022,cxs[-1],rs[-1])]:
                sec=[(z-.012,side*cx,cy,r+.002,r+.002),(z+.012,side*cx,cy,r+.002,r+.002)]
                strap=loft(kind+' leather strap '+label,sec,leather,sides=40,cap=False);solidify(strap,.004,.001);keep(strap,bone)
            for row in range(len(zs)-1):
                z=(zs[row]+zs[row+1])*.5;cx=(cxs[row]+cxs[row+1])*.5;r=(rs[row]+rs[row+1])*.5
                for a in [-1.80,1.80]:rivet((side*cx+r*math.sin(a),cy-r*math.cos(a)-.003,z),bone,.003,edge)
        # Separate flared ankle plate, visibly overlapping the greave as in the source.
        ankle=loft('Flared ankle armor '+label,[(.102,side*.133,.006,.055,.071),
            (.155,side*.133,.015,.049,.061)],metal,sides=32,cap=False)
        solidify(ankle,.005,.0015);keep(ankle,'shin.'+label)
        for a in [-1.6,-.8,0,.8,1.6]:
            rivet((side*.133+.055*math.sin(a),.006-.072*math.cos(a),.12),'shin.'+label,.0035,edge)
    # Waist belt and individual leather lappets.
    belt=loft('Leather waist belt',[(.991,0,0,.175,.119),(1.042,0,0,.171,.115)],leather,sides=64,cap=False)
    solidify(belt,.009,.002);keep(belt,'pelvis')
    for i in range(22):
        a=i*2*math.pi/22;length=.205+.026*math.sin(i*2.7)+.018*math.cos(i*1.3);verts=[];faces=[]
        for row in range(6):
            t=row/5;z=.998-length*t
            for j in range(4):
                aa=a+(j/3-.5)*(.265-.020*t)+.025*math.sin(i*1.8)*t;rx=.176+.023*t;ry=.125+.025*t
                zz=z-(.015 if row==5 and j in [1,2] else 0)+.010*math.sin(i*2.1)*t*(j/3-.5)
                verts.append((rx*math.sin(aa),-ry*math.cos(aa),zz))
        for row in range(5):
            for j in range(3):k=row*4+j;faces.append((k,k+1,k+5,k+4))
        strip=mesh_object('Leather skirt strip %02d'%i,verts,faces,leather);solidify(strip,.005,.0012);keep(strip,'pelvis')
        rivet((.198*math.sin(a),-.151*math.cos(a),.998-length*.86),'pelvis',.005,edge)
        rivet((.185*math.sin(a),-.133*math.cos(a),.974),'pelvis',.004,edge)
    keep(tube('Belt buckle',[(-.027,-.128,1.004),(.028,-.128,1.004),(.029,-.128,1.033),
        (-.027,-.128,1.033),(-.027,-.128,1.004)],[.004]*5,brass,sides=10),'pelvis')
    keep(tube('Buckle pin',[(0,-.132,1.018),(.032,-.132,1.019)],[.0025,.002],brass,sides=8),'pelvis')
    bpy.ops.mesh.primitive_cube_add(size=1,location=(-.153,-.099,1.009))
    pouch=bpy.context.object;pouch.name='Belt pouch';pouch.scale=(.09,.058,.093)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    pouch.data.materials.append(leather)
    m=pouch.modifiers.new('Rounded stitched pouch corners','BEVEL');m.width=.013;m.segments=3;apply(pouch,m)
    keep(pouch,'pelvis')
    flap=patch('Pouch flap',[(-.195,1.048),(-.110,1.048),(-.112,1.006),(-.152,.990),(-.194,1.006)],
        (-.153,1.023),lambda x,z:(x,-.132,z),leather);keep(flap,'pelvis');rivet((-.153,-.139,1.006),'pelvis',.0045)
    for name,path in paths.items():
        if name.endswith('.R') and 'finger' in name:continue
        p=Vector(path[-1]);d=(p-Vector(path[-2])).normalized();length=.032 if 'toe' in name else .024
        keep(tube('Claw '+name,[p,p+d*length*.55+Vector((0,-.003,.001)),p+d*length+Vector((0,-.004,-.005))],
            [.008 if 'toe' in name else .005,.004,.0004],claw,sides=12), 'foot.'+name[-1] if 'toe' in name else name)
    # Sword is an independently attached rigid prop, held forward in the native standing direction.
    hx,hy,hz=-.437,-.032,.873
    keep(tube('Sword leather grip',[(hx,hy+.072,hz),(hx,hy-.075,hz)],[.013,.013],leather,sides=16),'weapon.R')
    for i in range(9):
        y=hy+.061-i*.015
        pts=[(hx+.014*math.cos(a),y,hz+.014*math.sin(a)) for a in [j*2*math.pi/16 for j in range(17)]]
        keep(tube('Grip winding',pts,[.0015]*len(pts),brass,sides=6),'weapon.R')
    keep(ellipsoid('Sword pommel',(hx,hy+.084,hz),(.022,.016,.022),brass),'weapon.R')
    guard=[(hx-.063,hy-.079,hz+.025),(hx-.040,hy-.083,hz+.013),(hx,hy-.088,hz),
        (hx+.040,hy-.083,hz-.013),(hx+.063,hy-.079,hz-.025)]
    keep(tube('Swept gold crossguard',guard,[.006,.006,.009,.006,.006],brass,sides=14),'weapon.R')
    keep(tube('Knuckle guard',[(hx,hy+.079,hz),(hx-.039,hy+.053,hz-.035),
        (hx-.055,hy-.015,hz-.044),(hx-.040,hy-.080,hz-.022)],[.004]*4,brass,sides=12),'weapon.R')
    outline=[(0,.017),(.20,.022),(.35,.030),(.45,.046),(.52,.070),(.565,.095),(.59,.115),
        (.575,.067),(.55,.026),(.52,.004),(.47,-.014),(.35,-.026),(0,-.030)]
    verts=[(hx+sign*.004,hy-.095-d,hz+z) for sign in [-1,1] for d,z in outline]
    n=len(outline);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    blade=mesh_object('Long curved scimitar blade',verts,faces,steel)
    m=blade.modifiers.new('Sharpened bevel','BEVEL');m.width=.0025;m.segments=2;apply(blade,m);keep(blade,'weapon.R')
    # Slight inward aim preserves the native front-view blade foreshortening without making it edge-on.
    from mathutils import Matrix
    pivot=Vector((hx,hy,hz));rotation=Matrix.Rotation(math.radians(18),4,'Z')
    transform=Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot)
    for obj in objects:
        if obj.get('attachment_bone')=='weapon.R':obj.matrix_world=transform @ obj.matrix_world
        rest=obj.data.attributes.new(name='SculptPosition',type='FLOAT_VECTOR',domain='POINT')
        for v in obj.data.vertices:rest.data[v.index].vector=obj.matrix_world @ v.co
    return objects

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Inspect existing body scene before rebuilding'
    source=bpy.data.scenes['MM6 Goblin head sculpt']
    scene=bpy.data.scenes.new(SCENE);bpy.context.window.scene=scene
    heads=[]
    for original in source.objects:
        if original.type!='MESH':continue
        obj=original.copy();obj.data=original.data.copy();scene.collection.objects.link(obj)
        transform=Matrix.Translation((0,0,1.52)) @ Matrix.Diagonal((1.16,1.10,1.15,1)) @ Matrix.Translation((0,0,-1.575))
        obj.matrix_world=transform @ obj.matrix_world
        weighted(obj,'head');heads.append(obj)
    skin,paths=build_skin();costume=build_costume(paths)
    (ROOT/'body_landmarks.json').write_text(json.dumps({'digit_paths':paths,'units':'meters; Z up, front -Y',
        'landmarks':{'pelvis':[0,0,.97],'chest':[0,0,1.37],'neck':[0,.015,1.50],'head':[0,0,1.635],
        'shoulder_R':[-.25,0,1.44],'elbow_R':[-.366,.012,1.17],'wrist_R':[-.413,-.005,.94],
        'hip_R':[-.10,0,.94],'knee_R':[-.129,-.012,.49],'ankle_R':[-.133,.022,.13]}},indent=2)+'\n')
    data=bpy.data.cameras.new('Goblin full body review');data.type='ORTHO';data.ortho_scale=2.18
    camera=bpy.data.objects.new('Goblin full body review',data);scene.collection.objects.link(camera);scene.camera=camera
    for name,pos,power,size in [('Key',(-3,-4,5),650,4),('Fill',(3,-2,3),240,3),('Rim',(0,3,4),320,3)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=pos;look_at(light,(0,0,1))
    scene.world=source.world.copy();scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    camera.location=(0,-5,.99);look_at(camera,(0,0,.99))
    bpy.data.libraries.write(str(ROOT/'sculpt/body_library.blend'),{scene},fake_user=True)
    for angle,label in [(0,'front'),(45,'three_quarter'),(90,'profile'),(180,'back')]:
        a=-math.radians(angle);camera.location=(5*math.sin(a),-5*math.cos(a),.99);look_at(camera,(0,0,.99))
        scene.render.filepath=str(ROOT/'review'/f'body_v4_{label}.png');bpy.ops.render.render(write_still=True)
    camera.location=(0,-5,.99);look_at(camera,(0,0,.99))
    report={'head_objects':len(heads),'costume_objects':len(costume),'body_vertices':len(skin.data.vertices),
        'all_vertices':sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH'),
        'revision':4,'status':'Full body visual iteration; unrigged, not accepted final'}
    (ROOT/'sculpt/body_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':build()
