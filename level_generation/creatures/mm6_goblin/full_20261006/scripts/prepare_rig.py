"""Preserve corrected anatomy, repair demonstrated rig gaps, and assemble the native sword."""
import bpy,bmesh,json,math
from collections import Counter
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');ROOT=OUT.parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/body_corrected_v1.blend'))
body=bpy.data.objects['GoblinBody_Corrected']
# Close views and disconnected distal cross-sections revealed four long fingers plus a thumb.
# Excise the extra posterior digit and close only the new local palm opening.
bm=bmesh.new();bm.from_mesh(body.data);deform=bm.verts.layers.deform.verify();core=body.vertex_groups['Component_0'].index;skirt=body.vertex_groups['Component_15'].index
# The clay comparison still exposed a human-like brow/nose despite the earlier skull correction.
# Sculpt the existing connected facial surface into the selected heavy-browed, snub-nosed goblin.
for v in bm.verts:
    if core not in v[deform]:continue
    x,y,z=v.co
    if 1.32<z<1.60 and y<-.075 and abs(x)<.16:
        brow=sum(math.exp(-((x-sign*.057)/.038)**2-((z-1.490)/.027)**2) for sign in (-1,1))
        v.co.y-=.035*brow;v.co.z-=.005*brow
        cheek=math.exp(-((abs(x)-.093)/.036)**2-((z-1.428)/.046)**2)
        v.co.x+=math.copysign(.012*cheek,x);v.co.y-=.012*cheek
        if y<-.143 and abs(x)<.049:
            nose=math.exp(-((z-1.431)/.025)**2);v.co.x*=1+.48*nose;v.co.y-=.012*nose
            v.co.y+=.010*math.exp(-((z-1.465)/.022)**2)*math.exp(-(x/.025)**2)
        muzzle=math.exp(-((z-1.379)/.025)**2)*math.exp(-(x/.071)**2)
        chin=math.exp(-((z-1.346)/.020)**2)*math.exp(-(x/.066)**2)
        v.co.y-=.012*muzzle+.015*chin
# Close review traced the remaining chin ridge to duplicated skin seams and an overly pointed patch.
for v in bm.verts:
    if core in v[deform] and abs(v.co.x)<.06 and 1.325<v.co.z<1.368 and v.co.y<-.14:
        w=math.exp(-(v.co.x/.041)**2-((v.co.z-1.345)/.019)**2)
        target=-.175-.012*math.exp(-(v.co.x/.05)**2)
        v.co.y=v.co.y*(1-w)+target*w
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if core in v[deform] and abs(v.co.x)<.13 and 1.30<v.co.z<1.56 and v.co.y<-.06],dist=.00001)
# Replace the small generated chin spur with one clean skin patch, keeping the jaw and lip outline.
chin_patch=[v for v in bm.verts if core in v[deform] and abs(v.co.x)<.042 and 1.325<v.co.z<1.365 and v.co.y<-.153]
bmesh.ops.delete(bm,geom=chin_patch,context='VERTS')
chin_edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.x)<.09 and 1.30<v.co.z<1.39 and v.co.y<-.12 for v in e.verts)]
for f in bmesh.ops.holes_fill(bm,edges=chin_edges,sides=0)['faces']:f.material_index=0;f.smooth=True
# The tiny disconnected chin tooth is absent from native frames and selected appearance.
chin_group=body.vertex_groups['Component_64'].index
bmesh.ops.delete(bm,geom=[v for v in bm.verts if chin_group in v[deform]],context='VERTS')
# The remaining chin projection belongs to the connected lower denture, not the isolated fragment.
lower_teeth=body.vertex_groups['Component_5'].index
bmesh.ops.delete(bm,geom=[v for v in bm.verts if lower_teeth in v[deform] and v.co.z<1.376],context='VERTS')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
removed=[]
for sign in (-1,1):
    chosen=[v for v in bm.verts if core in v[deform] and sign*v.co.x>.55 and v.co.y>.015 and v.co.z<.719]
    removed.append(len(chosen));bmesh.ops.delete(bm,geom=chosen,context='VERTS')
    boundary=[e for e in bm.edges if e.is_boundary and all(sign*v.co.x>.52 and v.co.z<.76 for v in e.verts)]
    assert boundary,'Missing new palm boundary'
    new=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces'];assert new,'Palm repair failed'
    for f in new:f.material_index=0;f.smooth=True
    for v in bm.verts:
        if core in v[deform] and sign*v.co.x>.52 and v.co.z<.785 and v.co.y>.006:
            v.co.y-=(v.co.y-.006)*.6*min(1,max(0,(.785-v.co.z)/.06))
# Replace Meshy's fused ragged garment with twelve clean leather strips matching the selected guide.
leather_slot=next(i for i,m in enumerate(body.data.materials) if m and 'leather' in m.name)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if skirt in v[deform]],context='VERTS')
for panel in range(12):
    center=-math.pi+(panel+.5)*math.tau/12;verts={}
    for layer in range(2):
        for row,(height,radius) in enumerate(zip([.836,.785,.697,.624],[.201,.222,.244,.245])):
            for column in range(3):
                phi=center+(column-1)*(.5*math.tau/12-.010)
                z=height+(.020 if column!=1 else -.004) if row==3 else height
                r=radius-layer*.0035
                v=bm.verts.new((math.sin(phi)*r,.025-math.cos(phi)*r,z));v[deform][skirt]=1;verts[layer,row,column]=v
    def face(keys,smooth=True):
        f=bm.faces.new([verts[k] for k in keys]);f.material_index=leather_slot;f.smooth=smooth
    for layer in range(2):
        for row in range(3):
            for column in range(2):
                keys=[(layer,row,column),(layer,row,column+1),(layer,row+1,column+1),(layer,row+1,column)]
                face(keys if layer==0 else list(reversed(keys)))
    for column in [0,2]:
        for row in range(3):face([(0,row,column),(1,row,column),(1,row+1,column),(0,row+1,column)],False)
    for row in [0,3]:
        for column in range(2):face([(0,row,column),(0,row,column+1),(1,row,column+1),(1,row,column)],False)
def sector(face):
    c=face.calc_center_median();return int(((math.atan2(c.x,-(c.y-.025))+math.pi)%(math.tau))/math.tau*12)
seams=[]
# Duplicate seam vertices must inherit their own linked panel, rather than the same angular bin.
panel_groups=[body.vertex_groups.new(name=f'NativePanel_{i:02d}').index for i in range(12)]
for v in bm.verts:
    if skirt in v[deform]:
        votes=Counter(sector(f) for f in v.link_faces)
        if votes:v[deform][panel_groups[votes.most_common(1)[0][0]]]=1
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work/body_corrected_v2.blend'))

bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/rig_import.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');raw=next(o for o in bpy.context.scene.objects if o.name=='char1')
for b in arm.pose.bones:b.custom_shape=None
for o in list(bpy.context.scene.objects):
    if o not in (arm,raw):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);raw.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
arm.name='Goblin_Rig';arm.animation_data_clear()
tree=KDTree(len(raw.data.vertices))
for i,v in enumerate(raw.data.vertices):tree.insert(raw.matrix_world@v.co,i)
tree.balance()
with bpy.data.libraries.load(str(OUT/'work/body_corrected_v2.blend'),link=False) as (src,dst):dst.objects=['GoblinBody_Corrected']
body=dst.objects[0];bpy.context.scene.collection.objects.link(body);body.name='Goblin_Body'
members={g.name:{v.index for v in body.data.vertices if any(w.group==g.index for w in v.groups)} for g in body.vertex_groups}
bone_groups={b.name:body.vertex_groups.new(name=b.name) for b in arm.data.bones}
for v in body.data.vertices:
    source=raw.data.vertices[tree.find(body.matrix_world@v.co)[1]]
    for g in source.groups:bone_groups[raw.vertex_groups[g.group].name].add([v.index],g.weight,'REPLACE')
bpy.data.objects.remove(raw,do_unlink=True)
body.parent=arm;body.matrix_parent_inverse=arm.matrix_world.inverted();body.modifiers.new('Skin','ARMATURE').object=arm
bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
bones=arm.data.edit_bones
# Blender's importer used centimeter extras as bone display lengths. Use actual child joint centers.
for b in bones:
    direction=(b.tail-b.head).normalized();children=list(b.children)
    length=min((c.head-b.head).length for c in children if (c.head-b.head).length>.002) if children else .035
    b.tail=b.head+direction*length
for side,sign in [('Right',-1),('Left',1)]:
    for name,pos in [('Arm',(sign*.257,.062,1.219)),('ForeArm',(sign*.382,.031,.993)),('Hand',(sign*.568,-.015,.786))]:
        b=bones[side+name];shift=Vector(pos)-b.head;b.head+=shift;b.tail+=shift
    bones[side+'Arm'].tail=bones[side+'ForeArm'].head;bones[side+'ForeArm'].tail=bones[side+'Hand'].head
    bones[side+'Hand'].tail=Vector((sign*.602,-.072,.701))
    # Distal toe tips stay rigid with the complete plantigrade foot.
    bones[side+'Foot'].tail=bones[side+'ToeBase'].head

def add(name,head,tail,parent,dorsal=None):
    b=bones.new(name);b.head=head;b.tail=tail;b.parent=bones[parent]
    if dorsal:b.align_roll(Vector(dorsal))
    return b

digits={}
for side,sign in [('Right',-1),('Left',1)]:
    suffix='R' if sign<0 else 'L';digits[suffix]=[]
    for label,y in [('Index',-.134),('Middle',-.080),('Ring',-.020)]:
        cloud=[v.co for v in body.data.vertices if v.index in members['Component_0'] and sign*v.co.x>.55 and abs(v.co.y-y)<.026 and v.co.z<.68]
        assert cloud,'Missing physical digit'
        tipz=min(v.z for v in cloud);tip=sum((v for v in cloud if v.z<tipz+.012),Vector())/sum(v.z<tipz+.012 for v in cloud)
        base=Vector((sign*(.587 if label=='Index' else .607),y,.708));points=[base,base.lerp(tip,.34),base.lerp(tip,.70),tip]
        names=[]
        for j in range(3):
            name=f'Digit.{suffix}.{label}.{j+1:02d}';add(name,points[j],points[j+1],side+'Hand' if j==0 else names[-1],(sign,0,0));names.append(name)
        digits[suffix].append({'label':label,'names':names,'base':list(base),'tip':list(tip),'rest_palm_normal':[-sign,0,0]})
    thumbpoints=[Vector((sign*.551,-.099,.747)),Vector((sign*.511,-.143,.711)),Vector((sign*.497,-.173,.680))]
    thumb=[]
    for j in range(2):
        name=f'Digit.{suffix}.Thumb.{j+1:02d}';add(name,thumbpoints[j],thumbpoints[j+1],side+'Hand' if j==0 else thumb[-1],(sign,0,0));thumb.append(name)
    digits[suffix].append({'label':'Thumb','names':thumb,'base':list(thumbpoints[0]),'tip':list(thumbpoints[-1]),'rest_palm_normal':[-sign,0,0]})
    # Additional twist is scoped to the demonstrated forearm-pronation requirement.
    add('ForearmTwist.'+suffix,bones[side+'ForeArm'].head.lerp(bones[side+'Hand'].head,.52),bones[side+'Hand'].head,side+'ForeArm')
for side,sign in [('Right',-1),('Left',1)]:
    add('ArmorShoulder.'+('R' if sign<0 else 'L'),bones[side+'Arm'].head,bones[side+'Arm'].head+Vector((sign*.1,0,0)),side+'Shoulder')
add('Jaw',(0,.038,1.371),(0,-.17,1.349),'Head')
for i in range(12):
    angle=-math.pi+(i+.5)*math.tau/12;rad=Vector((math.sin(angle),-math.cos(angle),0))
    add(f'Skirt.{i:02d}',rad*.201+Vector((0,.025,.836)),rad*.245+Vector((0,.025,.624)),'Hips')
grip=Vector((-.565,-.074,.694));add('Weapon.R',grip,grip+Vector((0,-.20,0)),'RightHand')
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.pose.bones:b.rotation_mode='QUATERNION'

def weights(index,entries):
    for g in list(body.data.vertices[index].groups):
        name=body.vertex_groups[g.group].name
        if name in arm.data.bones:body.vertex_groups[name].remove([index])
    total=sum(entries.values());assert total>0
    for name,weight in entries.items():
        if weight<=1e-6:continue
        g=body.vertex_groups.get(name) or body.vertex_groups.new(name=name);g.add([index],weight/total,'REPLACE')

ownership={}
for group,indices in members.items():
    if group in ('Component_0','Component_3','Component_7','Component_15') or group.startswith('NativePanel_'):continue
    if not indices:continue
    center=sum((body.data.vertices[i].co for i in indices),Vector())/len(indices)
    side='Right' if center.x<0 else 'Left'
    if group.startswith('EarHoop') or center.z>1.32:owner='Head'
    elif group.startswith('RearPlate') or center.z>1.10:owner='Spine'
    elif center.z>.78 and abs(center.x)<.22:owner='Hips'
    elif abs(center.x)>.38:owner=side+'ForeArm'
    elif center.z>.30:owner=side+'Leg'
    else:owner=side+'Foot'
    # Shoulder cap and its spikes articulate as one rigid assembly around the actual shoulder.
    if group in ('Component_4','Component_8') or 1.16<center.z<1.32 and abs(center.x)>.15:owner=side+'Arm'
    if group in ('Component_13','Component_33','Component_19','Component_27','Component_40','Component_42','Component_49','Component_51','Component_54','Component_60'):owner=side+'Leg'
    if owner in ('RightArm','LeftArm'):owner='ArmorShoulder.'+('R' if owner=='RightArm' else 'L')
    ownership[group]=owner
    for i in indices:weights(i,{owner:1})
for i in members['Component_15']:
    v=body.data.vertices[i].co;sector=next(j for j in range(12) if i in members[f'NativePanel_{j:02d}']);fraction=min(1,max(0,(.833-v.z)/.020))
    weights(i,{'Hips':1-fraction,f'Skirt.{sector:02d}':fraction})
for side,sign in [('Right',-1),('Left',1)]:
    suffix='R' if sign<0 else 'L'
    for i in members['Component_0']:
        v=body.data.vertices[i].co
        if sign*v.x<.48 or v.z>.81:continue
        if v.z>.743:
            f=min(1,max(0,(.812-v.z)/.070));weights(i,{side+'Hand':f,side+'ForeArm':1-f});continue
        thumb=sign*v.x<.552 and v.y<-.09
        digit=digits[suffix][-1] if thumb else min(digits[suffix][:-1],key=lambda d:abs(v.y-d['base'][1]))
        if not thumb and v.z>.716:weights(i,{side+'Hand':1});continue
        names=digit['names'];a=Vector(digit['base']);b=Vector(digit['tip']);t=max(0,min(.999,(v-a).dot(b-a)/(b-a).length_squared));position=t*len(names)
        j=min(len(names)-1,int(position));blend=position-j
        if j==0 and t<.14:
            w=min(1,t/.14);weights(i,{side+'Hand':1-w,names[0]:w})
        else:weights(i,{names[j]:1-blend,names[min(j+1,len(names)-1)]:blend} if j<len(names)-1 else {names[-1]:1})
    # Meshy's weights were centered on its old wrist; fit them to the corrected joints.
    shoulder=arm.data.bones[side+'Arm'].head_local;elbow=arm.data.bones[side+'ForeArm'].head_local;wrist=arm.data.bones[side+'Hand'].head_local
    chain_axis=(wrist-shoulder).normalized();fore_axis=(wrist-elbow).normalized();fore_length=(wrist-elbow).length
    def smooth(value):
        value=max(0,min(1,value));return value*value*(3-2*value)
    for i in members['Component_0']:
        v=body.data.vertices[i].co
        if sign*v.x<.285 or v.z<.743 or v.z>1.265:continue
        elbow_blend=smooth(((v-elbow).dot(chain_axis)+.040)/.080)
        hand_blend=smooth(((v-wrist).dot(fore_axis)+.105)/.060)
        fore_weight=elbow_blend*(1-hand_blend)
        along=max(0,min(1,(v-elbow).dot(fore_axis)/fore_length));twist_share=fore_weight*max(0,min(1,(along-.20)/.80))
        weights(i,{side+'Arm':(1-elbow_blend)*(1-hand_blend),side+'ForeArm':fore_weight-twist_share,'ForearmTwist.'+suffix:twist_share,side+'Hand':hand_blend})
    for part in (('Component_3' if sign>0 else 'Component_7'),):
        for i in members[part]:
            if body.data.vertices[i].co.z<.205:weights(i,{side+'Foot':1})
# Central torso vertices must not follow arms or clavicles; this caused a large back-face collapse.
spine_joints=[('Hips',arm.data.bones['Hips'].head_local.z),('Spine02',arm.data.bones['Spine02'].head_local.z),('Spine01',arm.data.bones['Spine01'].head_local.z),('Spine',arm.data.bones['Spine'].head_local.z)]
for i in members['Component_0']:
    v=body.data.vertices[i].co
    if abs(v.x)<.22 and .81<v.z<1.285:
        if v.z<=spine_joints[0][1]:entries={'Hips':1}
        elif v.z>=spine_joints[-1][1]:entries={'Spine':1}
        else:
            for (lower,z0),(upper,z1) in zip(spine_joints,spine_joints[1:]):
                if z0<=v.z<=z1:
                    t=(v.z-z0)/(z1-z0);entries={lower:1-t,upper:t};break
        weights(i,entries)
# Blend the pelvis into each actual thigh, without cross-leg influences or an abrupt height seam.
for i in members['Component_0']:
    v=body.data.vertices[i].co
    if abs(v.x)<.28 and .64<v.z<.88:
        side='Right' if v.x<.004 else 'Left'
        joint=arm.data.bones[side+'UpLeg'].head_local
        fraction=smooth((joint.z+.055-v.z)/.13)*smooth((abs(v.x-.004)-.014)/.060)
        weights(i,{'Hips':1-fraction,side+'UpLeg':fraction})
for i in members['Component_0']:
    v=body.data.vertices[i].co
    if v.y<-.074 and 1.315<v.z<1.372 and abs(v.x)<.082:
        w=min(.85,max(0,(1.372-v.z)/.025));weights(i,{'Head':1-w,'Jaw':w})
for name in ('Component_5','Component_23','Component_64'):
    for i in members.get(name,set()):
        v=body.data.vertices[i].co;weights(i,{'Jaw':1} if name=='Component_5' else {'Head':1})

# A verified existing stepped curved blade with a gold knuckle bow matches the native profile.
bpy.ops.import_scene.gltf(filepath=str(ROOT/'meshy_restart_20260923/sword_attack_01/corsair_goblin_sword.glb'))
swordparts=[o for o in bpy.context.selected_objects if o.type=='MESH'];assert swordparts
for o in swordparts:o.matrix_world=Matrix.Translation(grip)@Matrix.Rotation(math.pi,4,'Z')@o.matrix_world
bpy.context.view_layer.objects.active=swordparts[0];bpy.ops.object.join();sword=bpy.context.object;sword.name='Goblin_Sword'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);g=sword.vertex_groups.new(name='Weapon.R');g.add(list(range(len(sword.data.vertices))),1,'REPLACE');sword.parent=arm;sword.matrix_parent_inverse=arm.matrix_world.inverted();sword.modifiers.new('Rigid weapon','ARMATURE').object=arm
for m in sword.data.materials:
    if m and 'ruby' in m.name.lower():m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.55,.33,.09,1)
counts=[sum(g.weight>1e-5 and body.vertex_groups[g.group].name in arm.data.bones for g in v.groups) for v in body.data.vertices]
sums=[sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in arm.data.bones) for v in body.data.vertices]
assert max(counts)<=4 and max(abs(s-1) for s in sums)<.001
report={'base_revision':'body_corrected_v2','extra_digit_vertices_removed':removed,'native_digit_contract':'three long fingers plus thumb per hand','digit_controls':digits,'armor_ownership':ownership,'skirt_seam_edges_split':len(seams),'skirt_replacement':'12 separate 3.5 mm leather strips; 528 triangles; belt and pouch retained','bones':len(arm.data.bones),'max_body_influences':max(counts),'max_weight_sum_error':max(abs(s-1) for s in sums),'body_triangles':len(body.data.polygons),'sword_triangles':sum(len(f.vertices)-2 for f in sword.data.polygons),'stock_clips_role':'diagnostic only; no native Run','sword_source':'meshy_restart_20260923/sword_attack_01/corsair_goblin_sword.glb','sword_grip_center_rest':list(grip),'user_artistic_acceptance':'not_recorded'}
(OUT/'review/rig/repairs.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.object.select_all(action='DESELECT')
for o in (arm,body,sword):o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work/rig_corrected_v1.blend'))
print(json.dumps(report),flush=True)
