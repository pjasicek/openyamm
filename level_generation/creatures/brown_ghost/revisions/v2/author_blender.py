"""Original procedural ghost, authored through Blender MCP. No imported model or image textures."""
import bpy
import math
from mathutils import Vector, Matrix
from pathlib import Path
import json

ROOT = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
SCENE_NAME = 'Brown ghost sprite studio'
PI = math.pi

def material(name, dark, light, scale):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*light, 1)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n.get('Principled BSDF')
    p.inputs['Roughness'].default_value = .92
    noise = n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 4
    uv = n.new('ShaderNodeTexCoord')
    l.new(uv.outputs['UV'], noise.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .2
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .8
    ramp.color_ramp.elements[1].color = (*light, 1)
    l.new(noise.outputs['Fac'], ramp.inputs[0])
    l.new(ramp.outputs[0], p.inputs['Base Color'])
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .17
    bump.inputs['Distance'].default_value = .006
    fine = n.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 160
    fine.inputs['Detail'].default_value = 2
    l.new(uv.outputs['UV'], fine.inputs['Vector'])
    l.new(fine.outputs['Fac'], bump.inputs['Height'])
    l.new(bump.outputs[0], p.inputs['Normal'])
    return m

class MeshBuilder:
    def __init__(self):
        self.v, self.f, self.m, self.uv = [], [], [], []
        self.weights, self.joints = [], {}
        self.group = "body"
    def vertex(self, v, uv=(0, 0)):
        self.v.append(tuple(v)); self.uv.append(uv)
        self.weights.append({self.group: 1} if isinstance(self.group,str) else dict(self.group))
        return len(self.v)-1
    def face(self, ids, mat):
        self.f.append(tuple(ids)); self.m.append(mat)
    def ellipsoid(self, pos, size, mat=1, rings=10, sides=16):
        base = len(self.v)
        for i in range(rings+1):
            a = PI*i/rings
            for j in range(sides):
                b = 2*PI*j/sides
                self.vertex((pos[0]+size[0]*math.sin(a)*math.cos(b),
                             pos[1]+size[1]*math.sin(a)*math.sin(b),
                             pos[2]+size[2]*math.cos(a)), (j/sides, i/rings))
        for i in range(rings):
            for j in range(sides):
                k = base+i*sides+j; q = base+i*sides+(j+1)%sides
                self.face((k, q, q+sides, k+sides), mat)
    def tube(self, pts, radius, mat=1, sides=8):
        base = len(self.v)
        for i, point in enumerate(pts):
            p = Vector(point)
            tangent = Vector(pts[min(i+1,len(pts)-1)]) - Vector(pts[max(i-1,0)])
            tangent.normalize()
            normal = tangent.cross(Vector((0,1,0)))
            if normal.length < .01: normal = tangent.cross(Vector((1,0,0)))
            normal.normalize(); binormal = tangent.cross(normal).normalized()
            r = radius[i] if isinstance(radius, list) else radius
            for j in range(sides):
                a = 2*PI*j/sides
                self.vertex(p+r*(math.cos(a)*normal+math.sin(a)*binormal), (j/sides,i/max(1,len(pts)-1)))
        for i in range(len(pts)-1):
            for j in range(sides):
                k = base+i*sides+j; q = base+i*sides+(j+1)%sides
                self.face((k,q,q+sides,k+sides),mat)
        self.face(tuple(base+j for j in reversed(range(sides))),mat)
        self.face(tuple(base+(len(pts)-1)*sides+j for j in range(sides)),mat)

# Geometry has invariant topology. Named shape keys retain every sampled animation pose.
def geometry(kind, i):
    b = MeshBuilder()
    phase=i
    t=phase*2*PI
    def envelope(knots):
        for (ta,va),(tb,vb) in zip(knots,knots[1:]):
            if phase<=tb:
                f=max(0,min(1,(phase-ta)/(tb-ta)));f=f*f*(3-2*f)
                return va+(vb-va)*f
        return knots[-1][1]
    lift, stretch, spread, raised, recoil, collapse = 0,1,.18,.04,0,0
    curl=.7
    if kind=='s':
        lift=.025*math.sin(t);spread=.18+.045*math.sin(t)
        recoil=.035*math.sin(t-.5);curl=.72+.12*math.sin(t-.6)
    elif kind=='w':
        stretch=.80+.14*(.5-.5*math.cos(t));lift=.19+.11*math.sin(t)
        spread=.40+.18*math.sin(t-.5);raised=.12+.07*math.sin(t-.8)
        curl=.67+.18*math.sin(t+.5)
    elif kind=='a':
        raised=envelope([(0,.04),(.22,-.12),(.50,.94),(.62,1),(.78,.12),(1,.04)])
        spread=envelope([(0,.18),(.22,.02),(.50,.68),(.62,.75),(.78,1.05),(1,.18)])
        recoil=envelope([(0,0),(.3,.3),(.6,.12),(.78,-.35),(1,0)])
        stretch=1-.16*max(0,raised);lift=.18*max(0,raised)
        curl=envelope([(0,.7),(.3,1),(.53,.25),(.76,.95),(1,.7)])
    elif kind=='n':
        recoil=envelope([(0,0),(.20,.65),(.42,.47),(1,0)])
        spread=envelope([(0,.18),(.28,.75),(.5,.45),(1,.18)])
        stretch=1-.17*max(recoil,0);curl=.72+.22*math.sin(phase*PI)
    elif kind=='f':
        spread=.18+.48*math.sin(phase*PI)**2
        raised=.04+.28*math.sin(phase*PI)**2
        recoil=.09*math.sin(t);curl=.7-.3*math.sin(phase*PI)**2
    elif kind=='d':
        recoil=envelope([(0,0),(.16,.55),(.32,.4),(.5,0),(1,0)])
        collapse=envelope([(0,0),(.2,0),(.38,.2),(.60,.73),(.82,.94),(1,1)])
        raised=.5*math.sin(phase*PI);spread=.18+.82*math.sin(phase*PI/2)
        curl=.7-.5*phase
    elif kind=='x':
        collapse=1;spread=1;raised=0;curl=.2
    zscale = stretch*(1-.93*collapse)
    def z(h): return .08+h*zscale+lift
    def clothpoint(theta, h, r):
        fold = .043*math.cos(theta*13+h*2.3)+.022*math.sin(theta*23-h*4+t-.6*h)
        fold += .035*math.sin(t-theta*1.8-h*2)*(1-h/2)**2
        return ((r+fold)*math.sin(theta)*(1+.35*collapse),
                -(r*.6+fold)*math.cos(theta)+.12+.08*math.sin(h*2+t)*(1-h/2), z(h))
    # Tattered open-front cloak, fixed perforations near lower edges.
    cols, rows = 88, 22
    base = len(b.v)
    for row in range(rows+1):
        f = row/rows
        for col in range(cols+1):
            u = col/cols
            opening=.045+.52*f**3
            theta=opening+(2*PI-2*opening)*u
            tooth=(col%8)/8
            hem=.03+.48*abs(2*tooth-1)+.18*(.5+.5*math.sin(col*.71))+.13*abs(math.sin(theta))
            h = hem+(1.97-hem)*f
            radius = .31+.32*math.sin(f*PI*.87)-.07*f**8
            p = clothpoint(theta,h,radius)
            # Front lapels taper away from the rib cage at the shoulders.
            p = (p[0]*(1+.1*f**3),p[1],p[2])
            tail = "cloak_back" if p[1]>.15 else ("cloak_L" if p[0]>0 else "cloak_R")
            b.group={"body":f,tail:1-f}
            b.vertex(p,(u*3,f*2))
    for row in range(rows):
        for col in range(cols):
            if row < 4 and (col*13+row*7)%41 == 0: continue
            k=base+row*(cols+1)+col
            b.face((k,k+1,k+cols+2,k+cols+1),0)
    # Overlapping ripped cloth panels produce the broad, broken mid-body silhouette.
    for layer in range(3):
        for panel in range(11):
            opening=[.80,.62,.42][layer]
            theta=opening+panel*(2*PI-2*opening)/10
            upper=1.87-layer*.36
            bottom=max(.03,upper-.73-.18*math.sin(panel*2.7+layer))
            base=len(b.v);nr,nc=8,6
            for row in range(nr+1):
                f=row/nr
                for col in range(nc+1):
                    u=col/nc
                    width=.54*(1-.90*f**1.7)
                    angle=theta+(u-.5)*width+.24*math.sin(theta)*f
                    h=upper+(bottom-upper)*f+.08*math.sin(col*2.4)*f**5
                    r=.43+.14*math.sin(h*PI/2)+.025*layer+.19*f
                    pt=clothpoint(angle,h,r)
                    pt=(pt[0],pt[1]-.025,pt[2])
                    tail='cloak_back' if pt[1]>.15 else ('cloak_L' if pt[0]>0 else 'cloak_R')
                    b.group={'body':1-f*.7,tail:f*.7}
                    b.vertex(pt,(panel*.27+u*.22,layer*.6+f*.7))
            for row in range(nr):
                for col in range(nc):
                    if row>5 and col==panel%5:continue
                    k=base+row*(nc+1)+col
                    b.face((k,k+1,k+nc+2,k+nc+1),0)
    # Front cloth closes below the ribs with a V-shaped opening, not a long central slit.
    base=len(b.v);nc,nr=24,12
    for row in range(nr+1):
        f=row/nr
        for col in range(nc+1):
            u=col/nc;hem=.035+.26*abs(2*((col%6)/6)-1)
            upper=1.22+.48*abs(2*u-1)
            h=upper*(1-f)+hem*f
            x=(u-.5)*(.82-.30*f)+.025*math.sin(t-f*2)*f
            y=-.26-.05*math.cos(u*PI*9)-.09*math.sin(f*PI)
            tail='cloak_L' if x>0 else 'cloak_R'
            b.group={'body':1-f,tail:f}
            b.vertex((x,y,z(h)),(u,f))
    for row in range(nr):
        for col in range(nc):
            if row>9 and col in [5,16]:continue
            k=base+row*(nc+1)+col
            b.face((k,k+1,k+nc+2,k+nc+1),0)
    # A sloping shoulder cowl joins the hood to the shroud.
    b.group='body'
    base=len(b.v)
    for row in range(9):
        f=row/8
        for col in range(49):
            a=.53+(2*PI-1.06)*col/48
            r=.20+.40*f
            b.vertex((r*math.sin(a),-.02-r*.63*math.cos(a),z(2.13-.32*f-.08*abs(math.sin(a)))+.04*math.sin(a*9)*f**3),
                     (col/48*3, f*.4))
    for row in range(8):
        for col in range(48):
            k=base+row*49+col
            b.face((k,k+1,k+50,k+49),0)
    b.joints['root']=((0,0,0),(0,0,.3))
    b.joints['body']=((0,.1,z(.9)),(0,.1,z(1.95)))
    for name,x,y in [('cloak_L',.28,0),('cloak_R',-.28,0),('cloak_back',0,.3)]:
        b.joints[name]=((x,y,z(1.5)),(x*(1+.35*collapse),y,z(.3)))
    # Spine, ribs, sternum and collar bones visible in the front opening.
    for j in range(9):
        b.ellipsoid((0,.07,z(1.28+j*.083)),(.049,.055,.038),1,6,10)
    for j in range(9):
        h=1.35+j*.067; width=.13+.105*math.sin((j+1)/10*PI)
        for side in [-1,1]:
            pts=[]
            for k in range(12):
                a=k/11*PI*.9
                pts.append((side*width*math.sin(a),.075-.23*math.sin(a*.8),z(h-.09*math.sin(a))))
            b.tube(pts,.013)
    b.tube([(0,-.12,z(1.32)),(0,-.15,z(1.85))],.026)
    for side in [-1,1]:
        b.tube([(0,-.12,z(1.9)),(side*.16,-.1,z(1.96)),(side*.35,.01,z(1.91))],.032)
    # Skull retains its proportions while the robe collapses around it.
    head_z = z(2.24)-.06*collapse
    head_y = -.12-recoil*.15
    b.group='head'
    b.joints['head']=((0,head_y,head_z-.2),(0,head_y,head_z+.28))
    def hp(x,y,h):
        tilt=collapse*1.15
        return (x,y*math.cos(tilt)-h*math.sin(tilt)+head_y,y*math.sin(tilt)+h*math.cos(tilt)+head_z)
    b.ellipsoid(hp(0,.066,.095),(.139,.117,.209),1,rings=12,sides=16)
    for side in [-1,1]:
        outline=[(.026,.055),(.032,.095),(.12,.123),(.135,.057),(.101,.006),(.040,.005)]
        outer=[hp(side*x,-.135,h) for x,h in outline]
        inner=[hp(side*(.077+(x-.077)*.88),-.074,.057+(h-.057)*.86) for x,h in outline]
        ids=[b.vertex(v) for v in outer+inner]
        for k in range(6):b.face((ids[k],ids[(k+1)%6],ids[6+(k+1)%6],ids[6+k]),1)
        b.face(tuple(ids[6:]),2)
        b.tube([hp(side*.025,-.15,.084),hp(side*.075,-.158,.117),hp(side*.134,-.133,.13)],
               [.012,.017,.010])
        b.tube([hp(side*.139,-.055,.035),hp(side*.148,-.099,-.012),hp(side*.104,-.13,-.063)],
               [.025,.018,.012])
        b.tube([hp(side*.102,-.12,-.065),hp(side*.075,-.145,-.117)],.017)
    # Triangular nasal aperture and extended, hollow upper jaw.
    nasal=[b.vertex(hp(x,-.153,h)) for x,h in [(0,.029),(-.025,-.064),(.026,-.064)]]
    b.face(nasal,2)
    b.tube([hp(-.04,-.14,-.058),hp(-.035,-.151,-.105),hp(.035,-.151,-.105),hp(.04,-.14,-.058)],.014)
    b.ellipsoid(hp(0,-.102,-.134),(.074,.034,.049),2,6,12)
    b.tube([hp(-.123,.003,-.04),hp(-.093,-.065,-.186),hp(-.043,-.12,-.211),
            hp(.043,-.12,-.211),hp(.093,-.065,-.186),hp(.123,.003,-.04)],.018)
    for j in range(8):
        x=(j-3.5)*.016
        top=-.108+.002*math.sin(j*3)
        bottom=top-.035-(.009 if j in [1,6] else 0)
        if j!=5:b.tube([hp(x,-.154,top),hp(x,-.157,bottom)],[.007,.004],1,5)
        if j not in [2,6]:b.tube([hp(x,-.14,-.184),hp(x,-.148,-.158)],[.007,.004],1,5)
    # Open hood: face opening, rolled rim, deep rear volume.
    for lining in [False, True]:
        base = len(b.v); nr, nc = 12, 48
        for row in range(nr+1):
            f=row/nr; shrink=math.cos(f*PI/2)*(.95 if lining else 1)
            for col in range(nc):
                a=2*PI*col/nc
                x=.218*math.cos(a)*shrink*(1+.07*math.cos(a*5))
                hh=(.30*math.sin(a)+.135*max(0,math.sin(a))**9)*shrink
                hh+=.06*math.sin(PI*f)*max(0,math.sin(a))
                yy=-.215+.62*f+.028*math.cos(a*7)*(1-f)
                b.vertex((x*(1+.55*collapse),head_y+yy*(1+.5*collapse),
                          head_z+(hh+.035)*(1-.78*collapse)),(col/nc,f))
        for row in range(nr):
            for col in range(nc):
                k=base+row*nc+col;q=base+row*nc+(col+1)%nc
                b.face((k,q,q+nc,k+nc),2 if lining else 0)
    # Arms and five articulated bony fingers; asymmetric movement is intentionally slight
    # because the native family mirrors directions 5/6/7.
    for side in [-1,1]:
        shoulder=Vector((side*.43,.04,z(1.9)))
        elbow=Vector((side*(.54+.17*spread),-.07,z(1.53)+raised*.48))
        wrist=Vector((side*(.22+.57*spread),-.38-recoil*.25,z(1.65)+raised*.84))
        if collapse:
            elbow=Vector((side*(.65+.1*collapse),-.02,.09+.75*(1-collapse)))
            wrist=Vector((side*(.92+.15*collapse),-.2,.08+1.1*(1-collapse)))
        side_name='L' if side==1 else 'R'
        upper='upper_arm_'+side_name; fore='forearm_'+side_name; hand='hand_'+side_name
        b.joints[upper]=(tuple(shoulder),tuple(elbow))
        b.joints[fore]=(tuple(elbow),tuple(wrist))
        b.group=upper
        b.tube([shoulder,elbow],.033)
        b.group=fore
        b.ellipsoid(elbow,(.044,.039,.042),1,6,10)
        b.tube([elbow+Vector((side*.022,0,0)),wrist+Vector((side*.013,0,0))],.02)
        b.tube([elbow-Vector((side*.022,0,0)),wrist-Vector((side*.013,0,0))],.015)
        direction = Vector((-side*(.75-.5*raised),-.75,.05+.7*raised)).normalized()
        lateral=Vector((side,0,0))
        if abs(direction.dot(lateral))>.85: lateral=Vector((0,0,1))
        lateral=(lateral-direction*lateral.dot(direction)).normalized()
        palm=wrist+direction*.1
        b.joints[hand]=(tuple(wrist),tuple(palm))
        b.group=hand
        for finger in range(5):
            offset=(finger-2)*.038
            knuckle=palm+lateral*offset
            b.group=hand
            b.tube([wrist+lateral*offset*.4,knuckle],.014)
            length=[.15,.265,.29,.25,.20][finger]
            bend=.055+.09*curl
            middle=knuckle+direction*length*.6+lateral*offset*.65+Vector((0,-.035,bend))
            tip=middle+direction*length*(.30-.15*curl)+lateral*offset*.27+Vector((0,-.03,-.07-.10*curl))
            finger_name=f'finger_{finger+1}_{side_name}'
            b.joints[finger_name]=(tuple(knuckle),tuple(middle))
            b.joints[finger_name+'_tip']=(tuple(middle),tuple(tip))
            b.group=finger_name
            b.tube([knuckle,middle],[.016,.012])
            b.group=finger_name+'_tip'
            b.tube([middle,tip],[.012,.004])
            b.ellipsoid(knuckle,(.019,.018,.018),1,6,8)
        # Ragged hanging sleeve, pleated drape connecting shoulder to forearm.
        base=len(b.v); nc,nr=24,10
        for row in range(nr+1):
            f=row/nr
            for col in range(nc+1):
                u=col/nc
                top=shoulder.lerp(elbow,u*1.4) if u<.71 else elbow.lerp(wrist,(u-.71)/.29*.55)
                drop=(.42+.45*math.sin(u*PI)+.22*abs(2*((col%6)/6)-1))*(1-.94*collapse)
                v=top+Vector((side*(.045*math.sin(u*PI)+.13*f),.03+.08*math.sin(u*PI*9+t-f)*f,-drop*f))
                b.group={upper:1-min(1,u*.75),fore:min(1,u*.75)}
                b.vertex(v,(u*2,f))
        for row in range(nr):
            for col in range(nc):
                if row>7 and col%9==3: continue
                k=base+row*(nc+1)+col
                b.face((k,k+1,k+nc+2,k+nc+1),0)
    return b

def build():
    old=bpy.data.scenes.get(SCENE_NAME)
    scene=bpy.data.scenes.new(SCENE_NAME+' rebuild')
    bpy.context.window.scene=scene
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    scene.name=SCENE_NAME
    mats=[material('Weathered umber shroud',(.026,.012,.006),(.125,.066,.032),18),
          material('Old ivory bones',(.09,.08,.05),(.42,.38,.25),13),
          material('Hood lining and socket shadow',(.003,.002,.001),(.018,.009,.003),9)]
    poses=[(k,i/max(1,n-1)) for k,n in [('s',9),('a',13),('w',13),('n',9),('d',11),('x',1),('f',13)] for i in range(n)]
    base=geometry('s',0)
    mesh=bpy.data.meshes.new('Ghost original mesh')
    mesh.from_pydata(base.v,[],base.f);mesh.update()
    for mat in mats: mesh.materials.append(mat)
    for poly,mat in zip(mesh.polygons,base.m): poly.material_index=mat;poly.use_smooth=True
    uv=mesh.uv_layers.new(name='Procedural surface UV')
    for poly in mesh.polygons:
        for li in poly.loop_indices: uv.data[li].uv=base.uv[mesh.loops[li].vertex_index]
    obj=bpy.data.objects.new('Brown ghost | animated cloth and skeleton',mesh)
    scene.collection.objects.link(obj)
    armdata=bpy.data.armatures.new('Ghost skeleton')
    rig=bpy.data.objects.new('Ghost RIG',armdata)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,tail) in base.joints.items():
        bone=armdata.edit_bones.new(name);bone.head=head;bone.tail=tail
    for bone in armdata.edit_bones:
        name=bone.name
        parent='body'
        if name=='root': continue
        if name=='body': parent='root'
        elif name.startswith('forearm_'): parent='upper_arm_'+name[-1]
        elif name.startswith('hand_'): parent='forearm_'+name[-1]
        elif name.startswith('finger_'):
            parent=name[:-4] if name.endswith('_tip') else 'hand_'+name[-1]
        bone.parent=armdata.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in armdata.bones:bone.inherit_scale='NONE'
    rig.show_in_front=True;armdata.display_type='OCTAHEDRAL'
    obj.parent=rig
    for name in base.joints: obj.vertex_groups.new(name=name)
    for index,weights in enumerate(base.weights):
        for name,weight in weights.items():
            if weight>0: obj.vertex_groups[name].add([index],weight,'REPLACE')
    modifier=obj.modifiers.new('Skeletal deformation','ARMATURE');modifier.object=rig
    solid=obj.modifiers.new('Cloth edge thickness','SOLIDIFY');solid.thickness=.004;solid.offset=0
    obj.shape_key_add(name='Basis')
    frames=[]
    for frame,(kind,i) in enumerate(poses,1):
        scene.frame_set(frame)
        data=geometry(kind,i)
        assert len(data.v)==len(base.v) and data.f==base.f
        # Absolute joint targets produce editable bone animation. Morph keys store
        # only the residual deformation after removing the sampled skin transform.
        targets={}
        for name,(head,tail) in data.joints.items():
            rest=armdata.bones[name];direction=Vector(tail)-Vector(head)
            rotation=direction.to_track_quat('Y','Z').to_matrix().to_4x4()
            target=Matrix.Translation(Vector(head)) @ rotation
            targets[name]=target @ Matrix.Diagonal((1,direction.length/rest.length,1,1))
        for name,target in targets.items():
            rest=armdata.bones[name];pb=rig.pose.bones[name]
            parent_args={}
            if rest.parent:
                parent_args={'parent_matrix':targets[rest.parent.name],'parent_matrix_local':rest.parent.matrix_local}
            pb.rotation_mode='QUATERNION';previous=pb.rotation_quaternion.copy()
            pb.matrix_basis=rest.convert_local_to_pose(target,rest.matrix_local,invert=True,**parent_args)
            if previous.dot(pb.rotation_quaternion)<0:pb.rotation_quaternion.negate()
            for field in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=field,frame=frame)
        bpy.context.view_layer.update()
        error=max(abs(rig.pose.bones[name].matrix[row][col]-target[row][col])
                  for name,target in targets.items() for row in range(4) for col in range(4))
        assert error<.00002,(kind,i,error)
        skin={name:targets[name] @ armdata.bones[name].matrix_local.inverted() for name in base.joints}
        key=obj.shape_key_add(name=f'{kind}_{frame:03d}_cloth_corrective')
        inverses={}
        for vertex,co,weights in zip(key.data,data.v,base.weights):
            signature=tuple(weights.items())
            if signature not in inverses:
                transform=Matrix(((0,0,0,0),)*4)
                for name,weight in weights.items(): transform+=skin[name]*weight
                inverses[signature]=transform.inverted_safe()
            vertex.co=inverses[signature] @ Vector(co)
        for f,value in [(1,0),(max(1,frame-1),0),(frame,1),(frame+1,0),(len(poses)+1,0)]:
            key.value=value;key.keyframe_insert(data_path='value',frame=f)
        suffix=f'{kind}_{frame:03d}'
        frames.append({'pose':suffix,'kind':kind,'phase':i,'frame':frame,'directions':list(range(5)) if kind in 'sawn' else [0]})
        scene.timeline_markers.new(suffix,frame=frame)
    # Both actions share the same clip ranges. They must play together.
    rig.animation_data.action.name='Ghost skeletal animation samples'
    obj.data.shape_keys.animation_data.action.name='Ghost cloth corrective samples'
    rig['animation_clips']='Standing 1; Attack 2-9; Float 10-17; Hit 18-23; Dying 18,19,24-27; Corpse 28; Fidget 29-32'
    rig['controls']='root/body/head; upper_arm/forearm/hand L/R; ten finger chains; cloak_L/R/back'
    # One directional studio camera; turntable rotations are applied during export.
    camdata=bpy.data.cameras.new('Orthographic sprite camera');camdata.type='ORTHO';camdata.ortho_scale=4.05
    cam=bpy.data.objects.new('Orthographic sprite camera',camdata);scene.collection.objects.link(cam)
    cam.location=(0,-10,1.91);cam.rotation_euler=(PI/2,0,0);scene.camera=cam
    def light(name,position,power,size,color):
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
        o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=position
        o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
    light('Soft upper-left key',(-3,-4,6),450,4,(1,.87,.69))
    light('Gentle frontal fill',(3,-4,2.8),110,3,(.76,.84,1))
    light('Cloth edge light',(1,2,4),280,3,(1,.78,.53))
    world=bpy.data.worlds.new('Transparent sprite world');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs[0].default_value=(.3,.3,.3,1)
    world.node_tree.nodes.get('Background').inputs[1].default_value=.35;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=len(poses)
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.frame_set(1)
    scene['reference']='assets_dev/engine/sprites/m242*.bmp; sprite groups m243/m244/m245'
    scene['authoring']='Original mesh/materials; 32-bone armature animation plus cloth corrective shape keys; author_blender.py'
    (ROOT/'poses.json').write_text(json.dumps(frames,indent=2)+'\n')
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
    bpy.data.libraries.write(str(ROOT/'brown_ghost.blend'),{scene},fake_user=True)
    return scene

if __name__=='__main__': build()
