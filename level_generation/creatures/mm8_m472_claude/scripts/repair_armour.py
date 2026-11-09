"""Rigid cuirass and fixed cord roots; preserve the existing hanging swing in world space."""
from pathlib import Path
import bpy,bmesh,json,shutil,sys,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from armour_mask import armour_mask
source=p/'work/rig_textured_uv_before_armour.blend'
if not source.exists():shutil.copy2(p/'work/rig_textured_uv.blend',source)
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
owner='B_Spine1';initial,_,_=armour_mask(body)
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
plate=bm.faces.layers.int.new('rigid_plate');lining=bm.faces.layers.int.new('armour_lining')
chosen={f for f in bm.faces if sum(initial[v.index] for v in f.verts)>=2}
# Keep the existing sleeves continuous beneath the rigid metal's edges.
lining_faces=set(chosen)
for f in chosen:f[plate]=1
result=bmesh.ops.duplicate(bm,geom=list(chosen))
duplicated={x for x in result['geom'] if isinstance(x,bmesh.types.BMFace)}
for f in chosen:f[plate]=0
assert duplicated and all(f[plate] for f in duplicated)
# Reuse an unmarked black-cloth patch from the existing atlas for the hidden lining.
image=bpy.data.images.load(str(p/'textures/necromancer_basecolor_1k.png'),check_existing=True)
normal=bpy.data.images.load(str(p/'textures/necromancer_normal_1k.png'),check_existing=True)
rgb=np.array(image.pixels[:]).reshape(image.size[1],image.size[0],4)[:,:,:3]
nrm=np.array(normal.pixels[:]).reshape(normal.size[1],normal.size[0],4)[:,:,:3]
valid=(rgb.max(2)<.11)&(rgb.min(2)>.012)
score=np.linalg.norm(nrm-np.array([.5,.5,1]),axis=2)+rgb.max(2);score[~valid]=100
row,col=np.unravel_index(np.argmin(score),score.shape);uv=bm.loops.layers.uv['UVMap']
for f in lining_faces:
    f[lining]=1
    for k,loop in enumerate(f.loops):loop[uv].uv=((col+.3+.15*(k%2))/image.size[0],(row+.3+.15*(k//2))/image.size[1])
# The flexible inner shirt closes the armholes throughout the cast.
for v in {v for f in lining_faces for v in f.verts}:
    v.co.x*=.92;v.co.y*=.92
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
rigid=bm.verts.layers.int.get('rigid_armour') or bm.verts.layers.int.new('rigid_armour')
inner=bm.verts.layers.int.new('inner_shirt')
for v in bm.verts:
    v[rigid]=int(any(f[plate] for f in v.link_faces))
    v[inner]=int(any(f[lining] for f in v.link_faces))
bm.to_mesh(body.data);bm.free()
co=np.array([tuple(v.co) for v in body.data.vertices]);piece=np.array([a.value for a in body.data.attributes['piece'].data]);mask=np.array([a.value for a in body.data.attributes['rigid_armour'].data],dtype=bool)
robe=np.array([a.value for a in body.data.attributes['garment_region'].data])==1
robe &= piece==0
inner=np.array([a.value for a in body.data.attributes['inner_shirt'].data],dtype=bool)
# Extend the skirt's connected region through the waist seam, excluding hanging cuffs.
adj=[set() for _ in co]
for edge in body.data.edges:
    a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
waist=set();todo=list(np.where(robe)[0])
while todo:
    i=todo.pop()
    if i in waist or piece[i]!=0 or co[i,2]>1.20:continue
    waist.add(i);todo.extend(adj[i]-waist)
waist=np.array([i in waist for i in range(len(co))])
cords=[f'Tassel_{piece}_{i}' for piece in (5,6) for i in (0,1)]
actions={a.name:a for a in bpy.data.actions};samples={}
def set_action(a):
    rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
for name,a in actions.items():
    set_action(a);samples[name]=[]
    for frame in range(int(a.frame_range[1])+1):
        scene.frame_set(frame);bpy.context.view_layer.update()
        samples[name].append({n:rig.pose.bones[n].matrix.to_3x3().copy() for n in cords})
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for piece_id in (5,6):rig.data.edit_bones[f'Tassel_{piece_id}_0'].parent=rig.data.edit_bones[owner]
bpy.ops.object.mode_set(mode='OBJECT')
for name,a in actions.items():
    set_action(a)
    for frame,rotations in enumerate(samples[name]):
        scene.frame_set(frame);bpy.context.view_layer.update();parent_matrices={owner:rig.pose.bones[owner].matrix.copy()}
        for n in cords:
            bone=rig.data.bones[n];parent=bone.parent.name
            inherited=parent_matrices[parent]@rig.data.bones[parent].matrix_local.inverted()@bone.matrix_local
            posed=rotations[n].to_4x4();posed.translation=inherited.translation
            pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(inherited.inverted()@posed).to_quaternion();pb.location=(0,0,0)
            pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
            parent_matrices[n]=posed
for v in body.data.vertices:
    i=v.index;old={body.vertex_groups[g.group].name:g.weight for g in v.groups};w=None
    # The lining under a rigid plate must share its transform, including at the collar.
    if mask[i] or inner[i] or piece[i]==7:w={owner:1.}
    elif piece[i]==2 and co[i,2]<1.51:
        # Keep the neck base inside the rigid collar while the head bends.
        t=float(np.clip((1.51-co[i,2])/.055,0,1));t=t*t*(3-2*t)
        w={n:x*(1-t) for n,x in old.items()};w[owner]=w.get(owner,0)+t
    elif piece[i]==0 and .83<co[i,2] and (waist[i] or inner[i]):
        t=float(np.clip((co[i,2]-.83)/.235,0,1));t=t*t*(3-2*t)
        if co[i,2]>1.20:
            u=float(np.clip((co[i,2]-1.20)/.18,0,1));t*=1-u*u*(3-2*u)
        w={n:x*(1-t) for n,x in old.items()};w[owner]=w.get(owner,0)+t
    elif piece[i] in (5,6):
        t=float(np.clip((co[i,2]-1.025)/.038,0,1));t=t*t*(3-2*t)
        w={n:x*(1-t) for n,x in old.items() if n.startswith('Tassel_')}
        total=sum(w.values())
        if total>0:w={n:x*(1-t)/total for n,x in w.items()}
        w[owner]=t if total>0 else 1.
    if w is not None:
        for group in body.vertex_groups:group.remove([i])
        for n,x in w.items():
            if x>1e-7:body.vertex_groups[n].add([i],x,'REPLACE')
# Keep the hanging portions outside the newly rigid torso and the robe it carries.
faces=[tuple(f.vertices) for f in body.data.polygons if all((mask|robe)[i] for i in f.vertices)]
for name,a in actions.items():
    set_action(a)
    for frame in range(int(a.frame_range[1])+1):
        scene.frame_set(frame);bpy.context.view_layer.update()
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        tree=BVHTree.FromPolygons([tuple(v.co) for v in mesh.vertices],faces);ev.to_mesh_clear()
        transform=rig.pose.bones[owner].matrix@rig.data.bones[owner].matrix_local.inverted()
        forward=(transform.to_3x3()@Vector((0,-1,0))).normalized()
        for piece_id in (5,6):
            names=[f'Tassel_{piece_id}_{i}' for i in (0,1)]
            points=[rig.pose.bones[names[0]].head.copy(),rig.pose.bones[names[1]].head.copy(),rig.pose.bones[names[1]].tail.copy()]
            root=points[0].copy();lengths=[rig.data.bones[n].length for n in names]
            for iteration in range(40):
                if name=='Death':
                    settle=float(np.clip((frame-24)/18,0,1))
                    points[1].z-=.004*settle;points[2].z-=.008*settle
                for segment in range(2):
                    for t in np.linspace(.2,1.,5):
                        q=points[segment].lerp(points[segment+1],float(t))
                        if (q-root).length<.035:continue
                        hit,normal,_,distance=tree.ray_cast(q+forward, -forward,2.)
                        if hit is None:continue
                        margin=.008+(.012*float(t) if segment==1 else 0.)
                        depth=(hit-q).dot(forward)+margin
                        if depth>0:
                            push=forward*min(depth,.025)
                            if segment==0:points[1]+=push/max(float(t),.2)
                            else:
                                points[1]+=push*(1-float(t));points[2]+=push*float(t)
                points[0]=root.copy()
                for j,length in enumerate(lengths):
                    direction=(points[j+1]-points[j]).normalized();points[j+1]=points[j]+direction*length
                    if points[j+1].z<.030:
                        dz=.030-points[j].z;horizontal=Vector((direction.x,direction.y,0)).normalized()
                        points[j+1]=points[j]+horizontal*math.sqrt(max(0,length*length-dz*dz))+Vector((0,0,dz))
            parent=rig.pose.bones[owner].matrix.copy()
            for j,n in enumerate(names):
                bone=rig.data.bones[n];local=bone.parent.matrix_local.inverted()@bone.matrix_local
                inherited=parent@local;direction=points[j+1]-inherited.translation
                swing=(inherited.to_3x3()@Vector((0,1,0))).rotation_difference(direction.normalized())
                posed=(swing.to_matrix()@inherited.to_3x3()).to_4x4();posed.translation=inherited.translation
                pb=rig.pose.bones[n];pb.rotation_quaternion=(inherited.inverted()@posed).to_quaternion();pb.keyframe_insert('rotation_quaternion',frame=frame);parent=posed

# Re-ground the visible fall after changing the rigid silhouette, as in finish_geometry.py.
a=actions['Death'];set_action(a);lows=[];matrices=[]
for f in range(int(a.frame_range[1])+1):
    scene.frame_set(f);bpy.context.view_layer.update();matrices.append(rig.pose.bones['B_Pelvis'].matrix.copy())
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();lows.append(min(v.co.z for v in mesh.vertices));ev.to_mesh_clear()
lifts=np.maximum(.003-np.array(lows),0)
lifts=np.maximum.reduce([np.roll(lifts,k)*(.5**abs(k)) for k in range(-2,3)])
assert lifts.max()<.08,float(lifts.max())
for f,(matrix,lift) in enumerate(zip(matrices,lifts)):
    scene.frame_set(f);matrix.translation.z+=float(lift);pb=rig.pose.bones['B_Pelvis'];pb.matrix=matrix;pb.keyframe_insert('location',frame=f)
print('ARMOUR_FLOOR_LIFT',float(lifts.max()))

chains=json.loads(scene['garment_chains'])
for c in chains:
    if c['kind']=='tassel':c['parent']=owner
scene['garment_chains']=json.dumps(chains)
attr=body.data.attributes.get('rigid_armour') or body.data.attributes.new('rigid_armour','INT','POINT');attr.data.foreach_set('value',mask.astype(int))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
# A rigid plate and attachment must be stationary in their owner's frame at every sampled pose.
anchors=((piece==5)|(piece==6))&(co[:,2]>=1.063);check=mask|inner|anchors|(piece==7);max_error=0.;report={}
for name,a in actions.items():
    set_action(a);worst=0.
    for frame in np.arange(0,float(a.frame_range[1])+.01,.5):
        scene.frame_set(int(frame),subframe=float(frame%1));bpy.context.view_layer.update()
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        back=rig.data.bones[owner].matrix_local@rig.pose.bones[owner].matrix.inverted()
        points=np.array([tuple(back@mesh.vertices[int(i)].co) for i in np.where(check)[0]])
        error=float(np.linalg.norm(points-co[check],axis=1).max());worst=max(worst,error);ev.to_mesh_clear()
    report[name]={'rigid_plate_and_root_max_error_mm':worst*1000};max_error=max(max_error,worst)
assert max_error<1e-5,max_error
out={'owner':owner,'armour_vertices':int(mask.sum()),'fixed_cord_root_vertices':int(anchors.sum()),'fixed_knot_vertices':int((piece==7).sum()),'contained_lining_vertices':int(inner.sum()),'max_error_mm':max_error*1000,'clips':report,'source':source.name}
(p/'review/armour_fix/rigidity.json').write_text(json.dumps(out,indent=2)+'\n');print('RIGIDITY',json.dumps(out))
