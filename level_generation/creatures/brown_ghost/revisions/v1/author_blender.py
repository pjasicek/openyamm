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
    t = i/8*2*PI
    lift, stretch, spread, raised, recoil, collapse = 0,1,0,0,0,0
    if kind == 'w':
        stretch = .61+.31*(.5-.5*math.cos(t)); lift = .36+.13*math.sin(t)
        spread = .42+.22*math.sin(t)
    elif kind == 'a':
        raised = [0,.35,.8,1,1,.65,.15,0][i]
        spread = .55
        stretch = 1-.24*raised; lift = .3*raised
    elif kind == 'n':
        recoil = [.35,.65,.45,-.18,-.1,0][i]
        spread = [0,0,.3,.9,.55,.1][i]
        stretch = 1-.24*max(recoil,0)
    elif kind == 'f':
        spread = [0,.2,.65,.85][i]; stretch = [1,.95,.8,.8][i]
    elif kind == 'd':
        collapse = [.52,.76,.91,1][i]; spread = 1; raised = max(0,1-collapse*1.3)
    elif kind == 'x':
        collapse = 1; spread = 1
    zscale = stretch*(1-.93*collapse)
    def z(h): return .08+h*zscale+lift
    def clothpoint(theta, h, r):
        fold = .028*math.cos(theta*15+h*3)+.013*math.sin(theta*29-h*5+t)
        return ((r+fold)*math.sin(theta)*(1+.35*collapse),
                -(r*.6+fold)*math.cos(theta)+.12+.08*math.sin(h*2+t)*(1-h/2), z(h))
    # Tattered open-front cloak, fixed perforations near lower edges.
    cols, rows = 88, 22
    base = len(b.v)
    for row in range(rows+1):
        f = row/rows
        for col in range(cols+1):
            u = col/cols; theta = .28+(2*PI-.56)*u
            hem = .025+.3*(.5+.5*math.sin(col*2.31))+.12*(.5+.5*math.sin(col*4.7))+.22*abs(math.sin(theta))
            h = hem+(1.97-hem)*f
            radius = .26+.22*math.sin(f*PI*.76)-.08*f**8
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
    # A sloping shoulder cowl joins the hood to the shroud.
    b.group='body'
    base=len(b.v)
    for row in range(9):
        f=row/8
        for col in range(49):
            a=.53+(2*PI-1.06)*col/48
            r=.235+.275*f
            b.vertex((r*math.sin(a),.10-r*.63*math.cos(a),z(2.10-.32*f)+.018*math.sin(a*12)*f),
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
    for j in range(6):
        h=1.49+j*.073; width=.14+.07*math.sin(j/6*PI)
        for side in [-1,1]:
            pts=[]
            for k in range(12):
                a=k/11*PI*.9
                pts.append((side*width*math.sin(a),.075-.23*math.sin(a*.8),z(h-.07*math.sin(a))))
            b.tube(pts,.016)
    b.tube([(0,-.12,z(1.52)),(0,-.15,z(1.85))],.026)
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
    b.ellipsoid(hp(0,.018,.08),(.168,.132,.205),1)
    # Recessed eye sockets, brow ridge and cheek arches.
    for side in [-1,1]:
        b.ellipsoid(hp(side*.074,-.112,.055),(.055,.031,.066),2)
        b.tube([hp(side*.025,-.125,.108),hp(side*.064,-.139,.13),hp(side*.12,-.112,.115)],.021)
        b.tube([hp(side*.14,-.08,.02),hp(side*.132,-.122,-.037),hp(side*.08,-.138,-.07)],.024)
    b.ellipsoid(hp(0,-.123,-.037),(.025,.023,.042),2,6,8)
    b.ellipsoid(hp(0,-.091,-.099),(.091,.058,.037),1,6,12)
    b.ellipsoid(hp(0,-.144,-.119),(.083,.01,.026),2,6,12)
    b.tube([hp(-.12,-.01,-.035),hp(-.102,-.081,-.159),hp(0,-.12,-.184),hp(.102,-.081,-.159),hp(.12,-.01,-.035)],.026)
    for j in range(7):
        b.ellipsoid(hp((j-3)*.023,-.155,-.098),(.009,.014,.024),1,6,8)
        b.ellipsoid(hp((j-3)*.022,-.141,-.153),(.009,.012,.015),1,6,8)
    # Open hood: face opening, rolled rim, deep rear volume.
    for lining in [False, True]:
        base = len(b.v); nr, nc = 12, 48
        for row in range(nr+1):
            f=row/nr; shrink=math.cos(f*PI/2)*(.95 if lining else 1)
            for col in range(nc):
                a=2*PI*col/nc
                x=.264*math.cos(a)*shrink*(1+.055*math.cos(a*5))
                hh=.335*math.sin(a)*shrink+.08*math.sin(PI*f)*max(0,math.sin(a))
                yy=-.15+.42*f+.025*math.cos(a*7)*(1-f)
                b.vertex((x*(1+.55*collapse),head_y+yy*(1+.5*collapse),
                          head_z+(hh+.035)*(1-.78*collapse)),(col/nc,f))
        for row in range(nr):
            for col in range(nc):
                k=base+row*nc+col;q=base+row*nc+(col+1)%nc
                b.face((k,q,q+nc,k+nc),2 if lining else 0)
    b.tube([( .264*math.cos(2*PI*j/48)*(1+.55*collapse),head_y+(-.15+.025*math.cos(2*PI*j/48*7))*(1+.5*collapse),
              head_z+(.335*math.sin(2*PI*j/48)+.035)*(1-.78*collapse)) for j in range(49)],.009,0)
    # Arms and five articulated bony fingers; asymmetric movement is intentionally slight
    # because the native family mirrors directions 5/6/7.
    for side in [-1,1]:
        shoulder=Vector((side*.38,.02,z(1.88)))
        elbow=Vector((side*(.45+.19*spread),-.10,z(1.51)+raised*.6))
        wrist=Vector((side*(.19+.66*spread),-.37,z(1.56)+raised*1.15))
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
        direction = (wrist-elbow).normalized()
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
            length=[.13,.22,.245,.215,.17][finger]
            bend=.055 if raised>.5 else -.06
            middle=knuckle+direction*length*.6+lateral*offset*.65+Vector((0,-.035,bend))
            tip=middle+direction*length*.38+lateral*offset*.45+Vector((0,.02,-.04))
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
                drop=(.4+.35*math.sin(u*PI)+.1*math.sin(col*2.6))*(1-.94*collapse)
                v=top+Vector((side*.04*math.sin(u*PI),.03+.065*math.sin(u*PI*9)*f,-drop*f))
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
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    scene=bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene=scene
    mats=[material('Weathered umber shroud',(.085,.035,.012),(.20,.092,.034),18),
          material('Old ivory bones',(.16,.13,.068),(.64,.53,.31),13),
          material('Hood lining and socket shadow',(.003,.002,.001),(.018,.009,.003),9)]
    poses=[(k,i) for k,n in [('s',1),('a',8),('w',8),('n',6),('d',4),('x',1),('f',4)] for i in range(n)]
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
        for name,(head,tail) in data.joints.items():
            rest=armdata.bones[name]
            direction=Vector(tail)-Vector(head)
            rotation=direction.to_track_quat('Y','Z').to_matrix().to_4x4()
            target=Matrix.Translation(Vector(head)) @ rotation
            target=target @ Matrix.Diagonal((1,direction.length/rest.length,1,1))
            pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
            pb.matrix=target
            bpy.context.view_layer.update()
            for field in ['location','rotation_quaternion','scale']: pb.keyframe_insert(data_path=field,frame=frame)
        bpy.context.view_layer.update()
        skin={name:rig.pose.bones[name].matrix @ armdata.bones[name].matrix_local.inverted() for name in base.joints}
        key=obj.shape_key_add(name=f'{kind}_{chr(97+i)}_cloth_corrective')
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
        suffix=f'{kind}{chr(97+i)}'
        frames.append({'pose':suffix,'frame':frame,'directions':list(range(5)) if kind in 'sawn' else [0]})
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
    scene.render.fps=8;scene.frame_start=1;scene.frame_end=len(poses)
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
