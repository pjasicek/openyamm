"""Native crossbow carry and aim fitting on the retained source-frame rig."""
import bpy, sys, json, math, os
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_pilot.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update()
# Meshy's distal hand weights included forearm influences; retain that blend only at the wrist seam.
for v in body.data.vertices:
    piece=body.data.attributes['piece'].data[v.index].value
    if piece not in (7,8):continue
    side='L' if piece==7 else 'R';wr=rig.data.bones[f'B_{side}_Hand'].head_local
    if (v.co-wr).length<.03:continue
    own=[(body.vertex_groups[g.group].name,g.weight) for g in v.groups if 'Hand' in body.vertex_groups[g.group].name or 'Finger' in body.vertex_groups[g.group].name]
    total=sum(w for n,w in own);assert total>0
    for g in body.vertex_groups:g.remove([v.index])
    for n,w in own:body.vertex_groups[n].add([v.index],w/total,'REPLACE')
# Shoulder shells rotate with lift but do not inherit the upper arm's axial roll.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side in 'LR':
    upper=rig.data.edit_bones[f'B_{side}_UpperArm']
    b=rig.data.edit_bones.new(f'B_{side}_Pauldron');b.head=upper.head;b.tail=upper.tail;b.roll=upper.roll
    b.parent=rig.data.edit_bones[f'B_{side}_Clavicle']
b=rig.data.edit_bones.new('Crossbow');b.head=(0,0,0);b.tail=(0,.15,0);b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
owners=json.loads((P/'work/piece_ownership.json').read_text())
for side,piece in [('R',15),('L',16)]:
    ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==piece or (body.data.attributes['piece'].data[v.index].value>=36 and owners[str(body.data.attributes['piece'].data[v.index].value)]==f'B_{side}_UpperArm')]
    for g in body.vertex_groups:g.remove(ids)
    g=body.vertex_groups.new(name=f'B_{side}_Pauldron');g.add(ids,1,'REPLACE')
# Long hair follows the torso below the neck, with a continuous root blend.
for v in body.data.vertices:
    piece=body.data.attributes['piece'].data[v.index].value
    if piece not in (1,6,10,13):continue
    t=max(0,min(1,(v.co.z-.82)/.30));t=t*t*(3-2*t)
    for g in body.vertex_groups:g.remove([v.index])
    body.vertex_groups['B_Head'].add([v.index],t,'REPLACE')
    body.vertex_groups['B_Spine2'].add([v.index],1-t,'REPLACE')
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
REST={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def basis(a,n):
    a=Vector(a).normalized();n=Vector(n);n=(n-a*n.dot(a)).normalized()
    return Matrix((a,n,a.cross(n))).transposed()
LOCAL={s:basis(G[s]['handle_axis_hand_local'],G[s]['palm_normal_hand_local']) for s in 'RL'}
def hand_rotation(s,R):
    # Index side of the trigger grip points up; support palm faces the stock underside.
    a,n=((0,0,1),(-1,0,0)) if s=='R' else ((-.60,.80,0),(0,0,1))
    return R@basis(a,n)@LOCAL[s].transposed()
parts=[]
def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
wood=mat('Crossbow wood',(.21,.075,.025));brass=mat('Crossbow bronze',(.55,.33,.10));cord=mat('Crossbow cord',(.07,.055,.035))
def rod(a,b,r,m,segments=8):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y')
    o.data.materials.append(m);parts.append(o);return o
def box(center,size,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Stock softened corners','BEVEL');bevel.width=.004;bevel.segments=1
    bpy.ops.object.modifier_apply(modifier=bevel.name);o.data.materials.append(m);parts.append(o)
box((0,.15,.095),(.044,.50,.045),wood)
rod((0,0,-.075),(0,0,.09),.009,wood,10)
rod((.036,.042,.025),(-.036,.138,.025),.012,wood,10)
for x,y in ((.036,.042),(-.036,.138)):
    rod((x,y,.025),(0,y,.08),.006,brass,8)
def bow_limb(points):
    verts=[];faces=[]
    for i,p in enumerate(points):
        d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        n=Vector((-d.y,d.x,0)).normalized()*.006
        h=.024-.010*i/(len(points)-1)
        verts.extend([Vector(p)+sx*n+Vector((0,0,sz*h)) for sx,sz in ((-1,-1),(1,-1),(1,1),(-1,1))])
        if i:
            for j in range(4):faces.append(((i-1)*4+j,(i-1)*4+(j+1)%4,i*4+(j+1)%4,i*4+j))
    faces.extend([(3,2,1,0),tuple(range(len(verts)-4,len(verts)))])
    mesh=bpy.data.meshes.new('Forged bow limb');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('Forged bow limb',mesh);scene.collection.objects.link(obj);mesh.materials.append(brass);parts.append(obj)
for sign in (-1,1):
    pts=[(0,.34,.10),(sign*.09,.33,.105),(sign*.18,.29,.11),(sign*.26,.23,.105),(sign*.30,.20,.095)]
    bow_limb(pts)
    rod(pts[-1],(0,-.015,.122),.002,cord,6)
    rod((sign*.04,.40,.09),(sign*.04,.47,.09),.006,brass)
rod((-.04,.47,.09),(.04,.47,.09),.006,brass)
rod((0,-.045,.125),(0,.43,.125),.0035,wood)
rod((0,.43,.125),(0,.46,.125),.007,brass)
for y in (-.075,.025,.31):box((0,y,.095),(.050,.016,.052),brass)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();prop=parts[0];prop.name='Crossbow'
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
def apply_pose(center,R,aim):
    for n,m in REST.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
    stats={}
    for s in 'RL':
        if s=='R' or aim:
            H=hand_rotation(s,R);C=Vector(center)+R@Vector((0,0,0) if s=='R' else (0,.09,.025))
            wrist=C-H@Vector(G[s]['handle_centre_hand_local'])
        else:
            H=rig.data.bones['B_L_Hand'].matrix_local.to_3x3();wrist=Vector((.34,-.02,.66))
        pole=Vector((.5 if s=='L' else -.5,.03,.75))
        snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
        S=armik.W(rig,f'B_{s}_UpperArm').translation
        axis=(wrist-S).normalized();base=(pole-S);base=(base-axis*base.dot(axis)).normalized()
        best=None
        for phi in range(-180,180,10):
            for n in (f'B_{s}_UpperArm',f'B_{s}_Forearm',f'B_{s}_Hand'):rig.pose.bones[n].matrix_basis=snap[n]
            bpy.context.view_layer.update()
            reach=armik.solve(rig,s,wrist,S+Quaternion(axis,math.radians(phi))@base,H)
            sw,tw=armik.wrist_cost(rig,s,H)
            ua=rig.pose.bones[f'B_{s}_UpperArm'];ur=ua.rotation_quaternion.angle
            cost=sw+sw*sw*.02+.25*abs(tw)+.08*abs(phi)
            if best is None or cost<best[0]:best=(cost,phi,{n:rig.pose.bones[n].matrix_basis.copy() for n in (f'B_{s}_UpperArm',f'B_{s}_Forearm',f'B_{s}_Hand')})
        for n,m in best[2].items():rig.pose.bones[n].matrix_basis=m
        bpy.context.view_layer.update()
        for n,q in G[s]['finger_local'].items():
            rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q
        bpy.context.view_layer.update()
        stats[s]={'reach':reach,'wrist':list(wrist),'swing_twist':armik.wrist_cost(rig,s,H),'phi':best[1]}
    for s in 'RL':
        fb,hb=rig.data.bones[f'B_{s}_Forearm'],rig.data.bones[f'B_{s}_Hand']
        ax=(fb.matrix_local.inverted()@hb.head_local).normalized()
        dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion() @ (fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
        _,tw=armik.split_swing_twist(dq,ax)
        rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(ax,tw*.6)
        ub=rig.data.bones[f'B_{s}_UpperArm'];ax=(ub.matrix_local.inverted()@fb.head_local).normalized()
        _,tw=armik.split_swing_twist(rig.pose.bones[ub.name].rotation_quaternion,ax)
        rig.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-tw*.5)
    for s in 'LR':
        cb=rig.data.bones[f'B_{s}_Clavicle'];ub=rig.data.bones[f'B_{s}_UpperArm'];fb=rig.data.bones[f'B_{s}_Forearm']
        C=armik.W(rig,cb.name)@cb.matrix_local.inverted()
        ref=C.to_3x3()@(fb.head_local-ub.head_local)
        cur=armik.W(rig,fb.name).translation-armik.W(rig,ub.name).translation
        q=Quaternion().slerp(ref.rotation_difference(cur),.40)
        m=armik.W(rig,f'B_{s}_Pauldron')
        armik.set_world(rig,f'B_{s}_Pauldron',armik.rot_world(m,q.to_matrix()@C.to_3x3()@ub.matrix_local.to_3x3()))
    bpy.context.view_layer.update()
    prop.matrix_world=R.to_4x4();prop.matrix_world.translation=center
    return stats
out={}
common.workbench_clay(scene);body.data.materials.clear();body.data.materials.append(mat('Body clay',(.52,.53,.56)))
if not os.environ.get('M632_BUILD'):
    for name,center,pitch,aim in [('carry',(-.36,-.32,.73),25,False),('aim',(-.08,-.29,1.10),-4,True),('recoil',(-.08,-.26,1.13),-25,True)]:
        R=Matrix.Rotation(math.radians(pitch),3,'X')@Matrix.Rotation(math.pi,3,'Z')
        out[name]=apply_pose(center,R,aim)
        common.render_views(str(P/f'review/pose_{name}'),.70,1.6,('front','left','three_quarter','back'),resolution=(640,800))
        if name=='aim':bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pose_fit.blend'))
    (P/'work/pose_fit.json').write_text(json.dumps(out,indent=2));print('POSE FIT',out)
