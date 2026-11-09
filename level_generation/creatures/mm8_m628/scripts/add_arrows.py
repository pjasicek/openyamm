"""Native bow-mounted spare arrows, a bevelled nocked arrow and an arrow-release socket."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/sources_complete.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bowrest=rig.data.bones['Bow'].matrix_local.copy()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones.new('Arrow');eb.head=(0,0,0);eb.tail=(0,1,0);eb.parent=rig.data.edit_bones['Bow']
eb=rig.data.edit_bones.new('Socket_Arrow');m=bowrest@Matrix.Translation((0,-.04,.065))
eb.head=m.translation;eb.tail=eb.head+m.to_3x3().col[1]*.1;eb.align_roll(m.to_3x3().col[2]);eb.parent=rig.data.edit_bones['Bow'];eb.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
vertices=[];faces=[];classes=[];pieces=[];bones=[]

def ringmesh(rings,cl,pid,bone,M):
    ids=[]
    for ring in rings:
        ids.append(len(vertices));vertices.extend([M@Vector(p)for p in ring]);pieces.extend([pid]*len(ring));bones.extend([bone]*len(ring))
    n=len(rings[0])
    fs=[tuple(ids[0]+j for j in reversed(range(n))),tuple(ids[-1]+j for j in range(n))]
    fs.extend((a+j,b+j,b+(j+1)%n,a+(j+1)%n)for a,b in zip(ids,ids[1:])for j in range(n))
    faces.extend(fs);classes.extend([cl]*len(fs))

def tube(stations,cl,pid,bone,M,n=8):
    ringmesh([[(math.cos(j*math.tau/n)*radius,math.sin(j*math.tau/n)*radius,z)for j in range(n)]
        for z,radius in stations],cl,pid,bone,M)

def arrow(M,pid,bone):
    tube([(0,.0034),(.60,.0034),(.625,.003)],10,pid,bone,M)
    tube([(.606,.0047),(.624,.0047)],9,pid,bone,M)
    ringmesh([[(x,y,z)for x,y in [(-w,0),(0,d),(w,0),(0,-d)]]
        for z,w,d in [(.618,.004,.003),(.634,.017,.004),(.697,.0003,.0003)]],9,pid,bone,M)
    for angle in [0,math.tau/3,math.tau*2/3]:
        R=M@Matrix.Rotation(angle,4,'Z')
        ringmesh([[(x,y,z)for x,z in [(.003,.012),(.018,.035),(.018,.105),(.003,.135)]]
            for y in [-.0006,.0006]],11,pid,bone,R)
    for z in [.008,.138]:tube([(z-.003,.0048),(z+.003,.0048)],8,pid,bone,M)
    tube([(-.006,.0043),(0,.0043)],8,pid,bone,M)

arrow(Matrix.Identity(4),4003,'Arrow')
for i in range(3):
    M=bowrest@Matrix.Translation((.040+i*.011,-.045,-.19+i*.010))@Matrix.Rotation(math.pi+.20,4,'X')@Matrix.Rotation(math.radians((i-1)*3),4,'Y')@Matrix.Scale(.70,4)
    arrow(M,4004,'Bow')
# Leather loops bridge the real lower limb to the parallel arrow bundle.
local=[rig.data.bones['Bow'].matrix_local.inverted()@v.co for v in body.data.vertices
    if body.data.attributes['piece'].data[v.index].value==4000]
for z in [-.29,-.49]:
    shaft=Vector((.051,-.045+(-.19-z)*math.tan(.20),z))
    band=[v for v in local if abs(v.z-z)<.018]
    assert band
    stave=Vector((0,sum(v.y for v in band)/len(band),z))
    centre=(shaft+stave)*.5;direction=(shaft-stave).normalized();cross=Vector((0,0,1)).cross(direction)
    length=(shaft-stave).length*.5+.027
    ringmesh([[tuple(centre+direction*(length*math.cos(j*math.tau/12))+cross*(.023*math.sin(j*math.tau/12))+Vector((0,0,dz)))
        for j in range(12)]for dz in [-.007,.007]],8,4004,'Bow',bowrest)
me=bpy.data.meshes.new('Arrows');me.from_pydata(vertices,[],faces);me.update()
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('Arrows',me);scene.collection.objects.link(ob)
me.attributes.new('piece','INT','POINT').data.foreach_set('value',pieces)
me.attributes.new('material_class','INT','FACE').data.foreach_set('value',classes)
for name in ['Arrow','Bow']:ob.vertex_groups.new(name=name).add([i for i,n in enumerate(bones)if n==name],1,'REPLACE')
me.materials.append(bpy.data.materials['BowClay'])
for f in me.polygons:f.use_smooth=classes[f.index] in [8,10]
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
for name in ['Arrow','Socket_Arrow']:rig.pose.bones[name].rotation_mode='QUATERNION'
scene['arrow_length']=.697
assert sum(len(f)-2 for f in faces)<1200
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'))
print('ARROWS',sum(len(f)-2 for f in faces),'triangles')
