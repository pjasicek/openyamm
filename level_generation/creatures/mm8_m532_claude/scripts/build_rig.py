"""Measured centaur hybrid rig: quadruped trunk/legs, human torso/hands, loose hair and tail ownership."""
from pathlib import Path
import bpy,bmesh,json,math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
body=bpy.data.objects['Centaur'];body.name='Body'
v=np.array([tuple(x.co) for x in body.data.vertices]);adj=[set()for _ in v]
for e in body.data.edges:
    a,b=e.vertices;adj[a].add(b);adj[b].add(a)
parts=[];todo=set(range(len(v)))
while todo:
    seed=todo.pop();stack=[seed];ids=[seed]
    while stack:
        ns=adj[stack.pop()]&todo;todo.difference_update(ns);stack.extend(ns);ids.extend(ns)
    parts.append(ids)
parts.sort(key=len,reverse=True);main=set(parts[0])
# The static preparation repaired the two damaged skin patches before fitting.
assert all(not e.is_loose for e in body.data.edges)
attr=body.data.attributes.new('component','INT','POINT')
for i,ids in enumerate(parts):
    for vi in ids:attr.data[vi].value=i
hands=json.loads((P/'work/hand_fit.json').read_text())
# Origin is between the four hoof contacts, rather than halfway along the trailing tail.
SHIFT=.40
for x in body.data.vertices:x.co.y+=SHIFT
v=np.array([tuple(x.co)for x in body.data.vertices])
def point(x,y,z):return Vector((x,y+SHIFT,z))
bones={}
def add(name,parent,head,tail):bones[name]=(parent,Vector(head),Vector(tail))
add('Root',None,(0,0,0),(0,0,.2))
add('HorsePelvis','Root',point(0,.2,1.15),point(0,-.25,1.15))
add('HorseSpine','HorsePelvis',point(0,-.25,1.15),point(0,-.75,1.2))
add('HorseChest','HorseSpine',point(0,-.75,1.2),point(0,-1,1.25))
add('Spine','HorseChest',point(0,-1,1.25),point(0,-.99,1.56))
add('Spine1','Spine',point(0,-.99,1.56),point(0,-.99,1.82))
add('Chest','Spine1',point(0,-.99,1.82),point(0,-.98,2.08))
add('Neck','Chest',point(0,-.98,2.08),point(0,-1.01,2.24))
add('Head','Neck',point(0,-1.01,2.24),point(0,-1.03,2.54))
for side,sg in [('L',1),('R',-1)]:
    h=hands[side];wr=Vector(h['wrist']);wr.y+=SHIFT;el=Vector(h['elbow']);el.y+=SHIFT
    shoulder=point(sg*.30,-1.0,2.0 if sg==1 else 2.02)
    add(side+'Shoulder','Chest',point(sg*.08,-1,2.01),shoulder)
    add(side+'Arm',side+'Shoulder',shoulder,el)
    add(side+'ForeArm',side+'Arm',el,wr)
    knuckle=Vector(h['digits']['Middle']['points'][0]);knuckle.y+=SHIFT
    add(side+'Hand',side+'ForeArm',wr,knuckle)
    for name,d in h['digits'].items():
        pts=[Vector(x)+Vector((0,SHIFT,0))for x in d['points']]
        if name=='Thumb':
            pts[0]=wr.lerp(pts[0],.35)
            pts[1]=pts[0].lerp(pts[-1],.45);pts[2]=pts[0].lerp(pts[-1],.75)
        for i in range(3):add(f'{side}{name}{i+1}',side+'Hand'if i==0 else f'{side}{name}{i}',pts[i],pts[i+1])
    add('FrontUpper_'+side,'HorseChest',point(sg*.21,-.98,1.06),point(sg*.21,-.95,.55))
    add('FrontLower_'+side,'FrontUpper_'+side,point(sg*.21,-.95,.55),point(sg*.215,-1.025,.16))
    add('FrontHoof_'+side,'FrontLower_'+side,point(sg*.215,-1.025,.16),point(sg*.215,-1.13,.055))
    add('HindUpper_'+side,'HorsePelvis',point(sg*.23,.23,1.15),point(sg*.21,.12,.86))
    add('HindLower_'+side,'HindUpper_'+side,point(sg*.21,.12,.86),point(sg*.23,.37,.48))
    add('HindCannon_'+side,'HindLower_'+side,point(sg*.23,.37,.48),point(sg*.24,.26,.16))
    add('HindHoof_'+side,'HindCannon_'+side,point(sg*.24,.26,.16),point(sg*.25,.14,.055))
tail=[point(0,.44,1.47),point(0,.65,1.55),point(0,.92,1.35),point(0,1.10,1.0),point(0,1.16,.67),point(0,1.13,.39)]
for i in range(5):add(f'Tail{i+1}','HorsePelvis'if i==0 else f'Tail{i}',tail[i],tail[i+1])
arm=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);body.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
for name,(parent,h,t)in bones.items():
    b=arm.edit_bones.new(name);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1))if abs((t-h).normalized().z)<.9 else Vector((0,-1,0)))
    if parent:b.parent=arm.edit_bones[parent]
    b.use_deform=not(name=='Root'or name.startswith('Tail')or any(f in name for f in ('Thumb','Index','Middle','Ring','Pinky')))
bpy.ops.object.mode_set(mode='OBJECT')
# Heat only the connected skin; accessory sheets cannot corrupt the solve.
skin=body.copy();skin.data=body.data.copy();bpy.context.collection.objects.link(skin)
bm=bmesh.new();bm.from_mesh(skin.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[x for x in bm.verts if x.index not in main],context='VERTS');bm.to_mesh(skin.data);bm.free()
for o in bpy.context.scene.objects:o.select_set(o in (skin,rig))
bpy.context.view_layer.objects.active=rig;bpy.ops.object.parent_set(type='ARMATURE_AUTO')
assert all(x.groups for x in skin.data.vertices),'Heat weights failed'
kd=KDTree(len(skin.data.vertices))
for x in skin.data.vertices:kd.insert(x.co,x.index)
kd.balance();sn={g.index:g.name for g in skin.vertex_groups}
for b in arm.bones:b.use_deform=b.name!='Root'
body.vertex_groups.clear();groups={n:body.vertex_groups.new(name=n)for n in bones if n!='Root'}
weights=[]
for pos in v:
    _,i,_=kd.find(pos);weights.append({sn[g.group]:g.weight for g in skin.data.vertices[i].groups if g.weight>.00001})
# Hair belongs to the head; tack follows skin underneath. The tail is one continuous chain across all its strips.
for pi,ids in enumerate(parts):
    coords=v[ids];raw_y=coords[:,1]-SHIFT
    if pi and coords[:,2].max()>2.3 and raw_y.max()<-.6:
        for i in ids:weights[i]={'Head':1.0}
    elif pi and raw_y.min()>.43:
        for i in ids:
            ds=[]
            for k in range(5):
                a,b=tail[k:k+2];d=b-a;t=np.clip((Vector(v[i])-a).dot(d)/d.length_squared,0,1);ds.append((np.linalg.norm(v[i]-np.array(a+d*t)),k,float(t)))
            _,k,t=min(ds);w={f'Tail{k+1}':1.0}
            if t>.65 and k<4:w={f'Tail{k+1}':1-(t-.65)/.7,f'Tail{k+2}':(t-.65)/.7}
            elif t<.35 and k>0:w={f'Tail{k+1}':.5+t/.7,f'Tail{k}':.5-t/.7}
            weights[i]=w
# Anatomical ownership excludes upper-arm influence from chest/back/neck and horse limbs from human torso.
for i in main:
    x,y,z=v[i]
    if z>1.32 and abs(x)<.23:
        w={n:a for n,a in weights[i].items()if not any(q in n for q in ('Arm','Hand','Shoulder','Front','Hind','HorsePelvis'))}
        if w:weights[i]=w
    if z<.14:
        side='L'if x>0 else'R';kind='Front'if y-SHIFT<-.6 else'Hind';weights[i]={f'{kind}Hoof_{side}':1.0}
# Finger ownership starts with connected digit components, then grows through their proximal web only.
for side,h in hands.items():
    wr=bones[side+'Hand'][1];owner={int(i):name for name,d in h['digits'].items()for i in d['vertices']}
    for _ in range(8):
        new={}
        for i,name in owner.items():
            start=bones[side+name+'1'][1];end=bones[side+name+'3'][2];axis=end-start
            for j in adj[i]:
                if j in owner or j in new:continue
                q=Vector(v[j])-start;t=q.dot(axis)/axis.length_squared
                if .05<t<1.15 and(q-axis*max(0,min(1,t))).length<.025:new[j]=name
        if not new:break
        owner.update(new)
    for i,name in owner.items():
        near=[]
        for k in range(1,4):
            _,a,b=bones[f'{side}{name}{k}'];d=b-a;t=np.clip((Vector(v[i])-a).dot(d)/d.length_squared,0,1)
            near.append((np.linalg.norm(v[i]-np.array(a+d*t)),k,float(t)))
        _,k,t=min(near);w={f'{side}{name}{k}':1.}
        if t>.65 and k<3:w={f'{side}{name}{k}':1-(t-.65)/.7,f'{side}{name}{k+1}':(t-.65)/.7}
        elif t<.35:w={f'{side}{name}{k}':.5+t/.7,(side+'Hand'if k==1 else f'{side}{name}{k-1}'):.5-t/.7}
        weights[i]=w
for i,w in enumerate(weights):
    items=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(a for _,a in items);assert total>0
    for n,a in items:groups[n].add([i],a/total,'REPLACE')
bpy.data.objects.remove(skin,do_unlink=True)
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
rig.show_in_front=True
assert len(arm.bones)<128
report={'bones':len(arm.bones),'vertices':len(body.data.vertices),'unweighted':sum(not x.groups for x in body.data.vertices),'max_influences':max(len(x.groups)for x in body.data.vertices),'origin_shift_y':SHIFT,'joint_positions':{n:{'parent':pa,'head':list(h),'tail':list(t)}for n,(pa,h,t)in bones.items()}}
assert report['unweighted']==0 and report['max_influences']<=4
(P/'work/rig_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',report['bones'],'bones;',report['unweighted'],'unweighted')
