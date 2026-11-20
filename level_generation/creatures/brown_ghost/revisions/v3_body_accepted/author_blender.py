"""Original rigged ghost, modeled in Blender from restored native sprite references."""
import bpy
import math
from mathutils import Vector, Matrix
from pathlib import Path
import json
from functools import lru_cache

ROOT = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
SCENE_NAME = 'Brown ghost sprite studio'
PI = math.pi

@lru_cache(maxsize=1)
def skull_mesh():
    return json.loads((ROOT/"sculpt/skull_mesh.json").read_text())

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
        self.profile_uv=[]
        self.group = "body"
    def vertex(self, v, uv=(0, 0)):
        self.v.append(tuple(v)); self.uv.append(uv); self.profile_uv.append(uv)
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
    def tube(self, pts, radius, mat=1, sides=10, aspect=1):
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
                self.vertex(p+r*(math.cos(a)*normal+aspect*math.sin(a)*binormal), (j/sides,i/max(1,len(pts)-1)))
        for i in range(len(pts)-1):
            for j in range(sides):
                k = base+i*sides+j; q = base+i*sides+(j+1)%sides
                self.face((k,q,q+sides,k+sides),mat)
        self.face(tuple(base+j for j in reversed(range(sides))),mat)
        self.face(tuple(base+(len(pts)-1)*sides+j for j in range(sides)),mat)

    def long_bone(self, start, end, radius, bow=0):
        """Narrow shaft with flared ends, rather than a constant-width cylinder."""
        start,end=Vector(start),Vector(end)
        steps=[0,.10,.23,.50,.77,.90,1]
        profile=[1.35,1.20,.78,.70,.82,1.20,1.30]
        pts=[start.lerp(end,t)+Vector((0,bow*math.sin(PI*t),0)) for t in steps]
        self.tube(pts,[radius*r for r in profile],aspect=.82)

def restored_body_materials(mats):
    """Stable surface UVs let cloth weave and bone patina follow the animated mesh."""
    cloth=mats[0];nodes,links=cloth.node_tree.nodes,cloth.node_tree.links
    image=bpy.data.images.load(str(ROOT/'reference_restoration/brown_shroud_weave_v1.png'),check_existing=True)
    image.pack()
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Procedural surface UV'
    tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT'
    links.new(uv.outputs['UV'],tex.inputs['Vector'])
    p=nodes.get('Principled BSDF');links.new(tex.outputs['Color'],p.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24
    bump.inputs['Distance'].default_value=.002
    links.new(tex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
    cloth['source']='Restored standing/hood views -> AI brown woven fabric swatch; sculpted geometric folds'
    bone=mats[1];nodes,links=bone.node_tree.nodes,bone.node_tree.links
    p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.65
    base=p.inputs['Base Color'].links[0].from_socket
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Procedural surface UV'
    split=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs[0],split.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(pos,value) in enumerate([(0,.62),(.16,1),(.82,1),(1,.62)]):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos)
        e.position=pos;e.color=(value,value,value,1)
    links.new(split.outputs['Y'],ramp.inputs[0])
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.65
    links.new(base,mix.inputs[1]);links.new(ramp.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])

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
        recoil=.035*math.sin(t-.5);curl=.45+.10*math.sin(t-.6)
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
    zscale = stretch*(1-.86*collapse)
    def z(h): return .08+h*zscale+lift
    def clothpoint(theta, h, r):
        # Long folds descend from the shoulders; subtle traveling waves animate loose hems.
        fold=.030*math.cos(theta*7+h*.40)+.006*math.sin(theta*19-h*.7)
        fold+=.018*math.sin(t-theta*1.8-h*1.3)*(1-h/2.2)**2
        return ((r+fold)*math.sin(theta)*(1+.35*collapse),
                -(r*.66+fold)*math.cos(theta)+.10+.035*math.sin(h*2+t)*(1-h/2.2),z(h))
    # One continuous shoulder-to-hem shroud, with a small chest opening and long torn folds.
    # Avoid the stacked triangular scales and separate stiff shoulder cape of the earlier mesh.
    cols,rows=96,36
    base=len(b.v)
    for row in range(rows+1):
        f=row/rows
        for col in range(cols+1):
            u=col/cols
            opening=.025+.64*f**3
            theta=opening+(2*PI-2*opening)*u
            hem=.025+.43*abs(math.sin(theta*4.5+.4))**.70+.16*abs(math.sin(theta*10.7))
            hem+=.20*math.sin(theta*1.7)**2
            shoulder_h=2.05-.30*abs(math.sin(theta))
            h=hem+(shoulder_h-hem)*f
            radius=.24+.18*math.sin(f*PI*.92)
            shoulder_r=.19+.25*abs(math.sin(theta))
            radius=radius*(1-f**7)+shoulder_r*f**7
            pt=clothpoint(theta,h,radius)
            tail='cloak_back' if pt[1]>.13 else ('cloak_L' if pt[0]>0 else 'cloak_R')
            b.group={'body':f,tail:1-f}
            b.vertex(pt,(u*2.4,f*2.2))
    for row in range(rows):
        for col in range(cols):
            wear=(col*71+row*97+col*row*13)%457
            if (row<11 and wear<11) or (11<=row<27 and wear<2):continue
            k=base+row*(cols+1)+col
            b.face((k,k+1,k+cols+2,k+cols+1),0)
    # The two front edges form a narrow V; below it the shroud hangs as one folded sheet.
    base=len(b.v);nc,nr=40,30
    for row in range(nr+1):
        f=row/nr
        for col in range(nc+1):
            u=col/nc
            hem=.025+.38*abs(math.sin(u*PI*3.5+.6))**.70+.14*abs(math.sin(u*PI*7))
            upper=1.28+.66*abs(2*u-1)**.72
            h=upper*(1-f)+hem*f
            x=(u-.5)*(.66-.20*f)+.025*math.sin(t-f*2)*f
            y=-.19-.035*math.cos(u*PI*8+f*.3)-.025*math.sin(f*PI)
            y-=.025*abs(2*u-1)**8
            tail='cloak_L' if x>0 else 'cloak_R'
            b.group={'body':1-f,tail:f}
            b.vertex((x,y,z(h)),(u*.9,f*2.2))
    for row in range(nr):
        for col in range(nc):
            wear=(col*89+row*53+col*row*17)%419
            if (row>20 and wear<8) or (8<row<=20 and wear<2):continue
            k=base+row*(nc+1)+col
            b.face((k,k+1,k+nc+2,k+nc+1),0)
    b.group='body'
    # The hood continues into a soft shoulder drape, hiding clavicles and upper arms.
    # Its slope accelerates toward the cuff; long folds replace a stiff flat cape edge.
    base=len(b.v);nc,nr=72,18
    for row in range(nr+1):
        f=row/nr
        for col in range(nc+1):
            u=col/nc;a=.35+.28*f+(2*PI-2*(.35+.28*f))*u
            fold=.018*math.sin(a*11+f*.5)+.009*math.sin(a*19-f)
            r=.17+.38*f+fold*f
            h=2.18-.58*f**1.5-.035*abs(math.sin(a))*f
            h+=.045*math.sin(a*9+.3)*f**8
            arm_follow=f**1.8*abs(math.sin(a))**3
            side_name='L' if math.sin(a)>0 else 'R'
            b.group={'body':1-arm_follow*.8,'upper_arm_'+side_name:arm_follow*.8}
            b.vertex(((r+.04*raised*arm_follow)*math.sin(a),-.025-r*.64*math.cos(a),
                      z(h)+.50*raised*arm_follow*(1-collapse)),(u*2.2,f*.85))
    for row in range(nr):
        for col in range(nc):
            k=base+row*(nc+1)+col
            b.face((k,k+1,k+nc+2,k+nc+1),0)
    b.group='body'
    b.joints['root']=((0,0,0),(0,0,.3))
    b.joints['body']=((0,.1,z(.9)),(0,.1,z(1.95)))
    for name,x,y in [('cloak_L',.28,0),('cloak_R',-.28,0),('cloak_back',0,.3)]:
        b.joints[name]=((x,y,z(1.5)),(x*(1+.35*collapse),y,z(.3)))
    # Anatomical thorax: curved flattened ribs wrap from spine into the sternum.
    # Most of the cage is under the cloth; only its narrow front is exposed in the standing guide.
    for j in range(12):
        b.ellipsoid((0,.055,z(1.24+j*.068)),(.039,.043,.028),1,7,12)
    for j in range(8):
        h=1.36+j*.074;width=.095+.067*math.sin((j+1)/9*PI)
        for side in [-1,1]:
            pts=[];radii=[]
            for k in range(19):
                a=k/18*(PI-.055)
                pts.append((side*(.014+width*math.sin(a)),.045+.18*math.cos(a),
                            z(h+.018*k/18-.048*math.sin(a))))
                radii.append(.015*(.72+.28*math.sin(a)))
            b.tube(pts,radii,aspect=.58)
    # The sternum is a flattened continuous plate with a small upper manubrium.
    b.ellipsoid((0,-.142,z(1.73)),(.026,.018,.19*zscale),1,16,12)
    b.ellipsoid((0,-.136,z(1.92)),(.036,.018,.038*zscale),1,8,12)
    b.tube([(0,-.14,z(1.56)),(0,-.142,z(1.48))],[.014,.004],aspect=.55)
    for side in [-1,1]:
        b.tube([(0,-.125,z(1.96)),(side*.09,-.115,z(1.98)),
                (side*.21,-.045,z(1.94)),(side*.34,.02,z(1.86))],
               [.022,.018,.019,.025],aspect=.70)
    # Skull retains its proportions while the robe collapses around it.
    head_z = z(2.24)-.06*collapse
    head_y = -.12-recoil*.15
    b.group='head'
    def hp(x,y,h):
        tilt=collapse*1.15+max(0,recoil)*.55
        return (x,y*math.cos(tilt)-h*math.sin(tilt)+head_y,y*math.sin(tilt)+h*math.cos(tilt)+head_z)
    b.joints['head']=(hp(0,0,-.2),hp(0,0,.28))
    # This is the connected, cavity-carved sculpture made in Blender from restored references.
    sculpture=skull_mesh();base=len(b.v)
    for co,uv,profile_uv in zip(sculpture['vertices'],sculpture['uv'],sculpture['profile_uv']):
        index=b.vertex(hp(*co),uv);b.profile_uv[index]=profile_uv
    for face,material_index in zip(sculpture['faces'],sculpture['materials']):
        b.face(tuple(base+i for i in face),material_index)
    # Open hood: face opening, rolled rim, deep rear volume.
    for lining in [False, True]:
        base = len(b.v); nr, nc = 12, 48
        for row in range(nr+1):
            f=row/nr; shrink=math.cos(f*PI/2)*(.95 if lining else 1)
            for col in range(nc):
                a=2*PI*col/nc
                x=.225*math.cos(a)*shrink*(1+.025*math.cos(a*5))
                hh=(.325*math.sin(a)+.007*math.sin(a*13))*shrink
                hh+=(.06*math.sin(PI*f)+.10*f)*max(0,math.sin(a))
                yy=-.035+.45*f+(.010*math.cos(a*9)-.07*max(0,math.sin(a))**2)*(1-f)
                hx=x*(1+.55*collapse);hy=yy*(1+.5*collapse);hz=(hh+.035)*(1-.78*collapse)
                tilt=max(0,recoil)*.55
                b.vertex((hx,head_y+hy*math.cos(tilt)-hz*math.sin(tilt),
                          head_z+hy*math.sin(tilt)+hz*math.cos(tilt)),(col/nc,f))
        for row in range(nr):
            for col in range(nc):
                k=base+row*nc+col;q=base+row*nc+(col+1)%nc
                b.face((k,q,q+nc,k+nc),2 if lining else 0)
    # Arms and five articulated bony fingers; asymmetric movement is intentionally slight
    # because the native family mirrors directions 5/6/7.
    for side in [-1,1]:
        shoulder=Vector((side*.35,.04,z(1.86)))
        elbow=Vector((side*(.47+.15*spread),-.07,z(1.53)+raised*.48))
        wrist=Vector((side*(.24+.52*spread),-.38-recoil*.25,z(1.50)+raised*.99))
        if collapse:
            elbow=Vector((side*(.65+.1*collapse),-.02,.09+.75*(1-collapse)))
            wrist=Vector((side*(.92+.15*collapse),-.2,.08+1.1*(1-collapse)))
        side_name='L' if side==1 else 'R'
        upper='upper_arm_'+side_name; fore='forearm_'+side_name; hand='hand_'+side_name
        b.joints[upper]=(tuple(shoulder),tuple(elbow))
        b.joints[fore]=(tuple(elbow),tuple(wrist))
        b.group=upper
        b.long_bone(shoulder,elbow,.023,bow=.018)
        b.group=fore
        b.ellipsoid(elbow,(.029,.026,.028),1,8,12)
        b.long_bone(elbow+Vector((side*.020,0,0)),wrist+Vector((side*.014,0,0)),.016,bow=.010)
        b.long_bone(elbow-Vector((side*.020,0,0)),wrist-Vector((side*.014,0,0)),.013,bow=-.011)
        reach=max(0,min(1,raised))
        direction=Vector((-side*.82,-.55,-.48)).lerp(Vector((-side*.08,-.24,1)),reach).normalized()
        lateral=Vector((side,0,0))
        lateral=(lateral-direction*lateral.dot(direction)).normalized()
        palm=wrist+direction*.105
        b.joints[hand]=(tuple(wrist),tuple(palm))
        b.group=hand
        # Small connected-looking carpal cluster and tapered metacarpals, with visible knuckle ends.
        for j in range(3):
            pos=wrist+direction*.025+lateral*(j-1)*.023
            b.ellipsoid(pos,(.018,.015,.019),1,7,10)
        for finger in range(5):
            offset=(finger-2)*.040
            knuckle=palm+lateral*offset
            b.group=hand
            b.long_bone(wrist+lateral*offset*.38,knuckle,.012)
            length=[.17,.30,.34,.31,.25][finger]
            fan=.22+.13*reach
            fd=(direction+lateral*(finger-2)*fan).normalized()
            # Relaxed fingers descend across the robe; raised attack fingers open into a long fan.
            middle=knuckle+fd*length*.55+Vector((0,-.012,.014*reach))
            tip=middle+fd*length*.40+Vector((0,-.030*curl,-.045*curl*(1-reach)))
            finger_name=f'finger_{finger+1}_{side_name}'
            b.joints[finger_name]=(tuple(knuckle),tuple(middle))
            b.joints[finger_name+'_tip']=(tuple(middle),tuple(tip))
            b.group=finger_name
            b.long_bone(knuckle,middle,.010)
            b.ellipsoid(knuckle,(.016,.014,.016),1,7,10)
            b.group=finger_name+'_tip'
            end_joint=middle.lerp(tip,.57)+Vector((0,-.006,0))
            b.long_bone(middle,end_joint,.008)
            b.ellipsoid(middle,(.012,.011,.012),1,7,10)
            b.tube([end_joint,end_joint.lerp(tip,.6),tip],[.009,.006,.0025])
        # Soft sleeve drapes over the upper arm and falls in long pointed strips behind the forearm.
        base=len(b.v);nc,nr=32,22
        for row in range(nr+1):
            f=row/nr
            for col in range(nc+1):
                u=col/nc
                top=shoulder.lerp(elbow,u/.64) if u<.64 else elbow.lerp(wrist,(u-.64)/.36*.36)
                top+=Vector((side*.023,-.025,.025))
                hem_wave=.18*abs(math.sin(u*PI*5+.8))**.70+.06*abs(math.sin(u*PI*11))
                drop=(.60+.25*math.sin(u*PI)+hem_wave)*(1-.94*collapse)
                v=top+Vector((side*(.018*math.sin(u*PI)+.04*f),
                    .065+.024*math.cos(u*PI*12+f*.5)+.025*math.sin(t-f)*f,-drop*f))
                b.group={upper:1-min(1,u*.75),fore:min(1,u*.75)}
                b.vertex(v,(u*.8,f*1.35))
        for row in range(nr):
            for col in range(nc):
                wear=(col*59+row*83+col*row*17)%307
                if row>12 and wear<7:continue
                k=base+row*(nc+1)+col
                b.face((k,k+1,k+nc+2,k+nc+1),0)
    return b

def build(preview_only=False,preview_pose=('s',0)):
    # Material preview need not re-evaluate the whole skinned mesh during every source-pose edit.
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID'
    old=bpy.data.scenes.get(SCENE_NAME)
    scene=bpy.data.scenes.new(SCENE_NAME+' rebuild')
    bpy.context.window.scene=scene
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    scene.name=SCENE_NAME
    mats=[material('Weathered umber shroud',(.026,.012,.006),(.125,.066,.032),18),
          material('Old ivory bones',(.19,.165,.105),(.49,.43,.285),17),
          material('Hood lining and socket shadow',(.003,.002,.001),(.018,.009,.003),9)]
    restored_body_materials(mats)
    projection_module={'__name__':'skull_projection'}
    exec(compile((ROOT/'skull_projection_material.py').read_text(),'skull_projection_material.py','exec'),projection_module)
    mats.append(projection_module['projected_skull_material'](mats[1]))
    poses=[(k,i/max(1,n-1)) for k,n in [('s',9),('a',13),('w',13),('n',9),('d',11),('x',1),('f',13)] for i in range(n)]
    if preview_only:poses=[preview_pose]
    base=geometry('s',0)
    mesh=bpy.data.meshes.new('Ghost original mesh')
    mesh.from_pydata(base.v,[],base.f);mesh.update()
    for mat in mats: mesh.materials.append(mat)
    for poly,mat in zip(mesh.polygons,base.m): poly.material_index=mat;poly.use_smooth=True
    uv=mesh.uv_layers.new(name='Procedural surface UV')
    for poly in mesh.polygons:
        for li in poly.loop_indices: uv.data[li].uv=base.uv[mesh.loops[li].vertex_index]
    profile_uv=mesh.uv_layers.new(name='Skull profile projection')
    for poly in mesh.polygons:
        for li in poly.loop_indices:profile_uv.data[li].uv=base.profile_uv[mesh.loops[li].vertex_index]
    mesh.uv_layers.active=uv;uv.active_render=True
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
        if frame%10==1:(ROOT/'review/status.txt').write_text(f'Fitting body pose {frame}/{len(poses)}')
        scene.frame_set(frame)
        data=geometry(kind,i)
        assert len(data.v)==len(base.v) and data.f==base.f
        # Absolute joint targets produce editable bone animation. Morph keys store
        # only the residual deformation after removing the sampled skin transform.
        targets={}
        for name,(head,tail) in data.joints.items():
            rest=armdata.bones[name];direction=Vector(tail)-Vector(head)
            # Swing from the rest orientation. A global Z-up tracking frame flips its roll
            # when a raised arm passes the vertical pole, twisting sleeves between anchors.
            rest_direction=rest.tail_local-rest.head_local
            swing=rest_direction.normalized().rotation_difference(direction.normalized())
            rotation=(swing @ rest.matrix_local.to_quaternion()).to_matrix().to_4x4()
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
    for data in [rig,obj.data.shape_keys]:
        for layer in data.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
    if not preview_only:
        # Regression check for the raised-arm roll discontinuity: exact anchors alone missed it.
        attack_frames=[f['frame'] for f in frames if f['kind']=='a']
        phase=17/30
        sample=attack_frames[0]+(attack_frames[-1]-attack_frames[0])*phase
        scene.frame_set(int(sample),subframe=sample-int(sample));bpy.context.view_layer.update()
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        intended=geometry('a',phase)
        surface_error=max((evaluated.data.vertices[i].co-Vector(co)).length for i,co in enumerate(intended.v))
        assert surface_error<.04,('Raised-arm interpolation',surface_error)
        (ROOT/'review/interpolation_validation.json').write_text(json.dumps({
            'source_frame':sample,'maximum_surface_error':surface_error,'limit':.04,'result':'PASS'},indent=2)+'\n')
    rig['animation_clips']='Source anchors are listed in poses.json; finish_blender.py creates seven named clips.'
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
    scene['authoring']='Revision 3: AI-restored native references; carved connected skull; 32-bone animation and cloth corrections'
    scene['restoration_reference']='reference_restoration/standing_views_v1.png; skull_detail_v1.png; action_poses_v2.png; death_fidget_v2.png'
    if not preview_only:(ROOT/'poses.json').write_text(json.dumps(frames,indent=2)+'\n')
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
    if not preview_only:bpy.data.libraries.write(str(ROOT/'brown_ghost.blend'),{scene},fake_user=True)
    return scene

if __name__=='__main__': build()
