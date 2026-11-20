"""Fit the Wyrm to measured mesh sections; heat skin, then rigid connected mouth pieces."""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'))
mesh = bpy.data.objects['Wyrm']
co = np.array([v.co[:] for v in mesh.data.vertices])
part = np.array([a.value for a in mesh.data.attributes['part'].data])

# Centreline and joint pivots from work/rest_co.npy section medians, not sprite pixel angles.
chains = {
    'Spine': (None, [(0,-.13,.19),(0,-.215,.172),(0,-.285,.17),(0,-.332,.187)]),
    'Neck': ('Spine3',[(0,-.332,.187),(0,-.347,.238),(0,-.371,.29),(0,-.437,.331)]),
    'Head': ('Neck3',[(0,-.437,.331),(0,-.496,.322)]),
    'Jaw': ('Head',[(0,-.449,.315),(0,-.497,.310)]),
    'Tail': ('Spine1',[(0,-.09,.189),(0,-.02,.15),(0,.035,.109),(0,.09,.071),
             (0,.145,.049),(0,.20,.035),(0,.255,.026),(0,.31,.021),(0,.36,.024),(0,.405,.039),(0,.46,.064)]),
}
names = {'Spine':['Spine1','Spine2','Spine3'],'Neck':['Neck1','Neck2','Neck3'],
         'Head':['Head'],'Jaw':['Jaw'],'Tail':[f'Tail{i}' for i in range(1,11)]}
for side,sign in [('L',1),('R',-1)]:
    chains['Front_'+side] = ('Spine3',[(sign*.046,-.330,.159),(sign*.065,-.322,.100),
                           (sign*.084,-.384,.020),(sign*.085,-.425,.012)])
    chains['Hind_'+side] = ('Spine1',[(sign*.046,-.137,.183),(sign*.061,-.153,.110),
                          (sign*.066,-.094,.067),(sign*.079,-.143,.014)])
    # The last segment is the hock-to-foot chain; preserve the complete clawed foot on its bone.
    names['Front_'+side] = [f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPaw_{side}']
    names['Hind_'+side] = [f'Thigh_{side}',f'Shin_{side}',f'HindPaw_{side}']
arm = bpy.data.armatures.new('Wyrm_Rig');rig = bpy.data.objects.new('Wyrm_Rig',arm)
bpy.context.scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for key,(parent,points) in chains.items():
    previous=arm.edit_bones.get(parent) if parent else None
    for i,name in enumerate(names[key]):
        b=arm.edit_bones.new(name);b.head=points[i];b.tail=points[i+1];b.parent=previous
        b.align_roll(Vector((0,0,1)) if key in ['Spine','Neck','Head','Jaw','Tail'] else Vector((0,-1,0)))
        previous=b
bpy.ops.object.mode_set(mode='OBJECT')
mesh.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty=[v.index for v in mesh.data.vertices if not v.groups or sum(g.weight for g in v.groups)<1e-5]
assert all(part[i]!=0 for i in empty), f'Heat weights failed on main body: {len(empty)} vertices'

def set_weights(ids, weights):
    for g in mesh.vertex_groups:g.remove(ids)
    for n,w in weights.items():
        if w>1e-6:mesh.vertex_groups[n].add(ids,float(w),'REPLACE')

# Rigid separated teeth, eyeballs and chin ornaments must not distort with neck heat weights.
tree=kdtree.KDTree(int((part==0).sum()))
for i in np.flatnonzero(part==0):tree.insert(Vector(co[i]),int(i))
tree.balance()
for k in np.unique(part):
    if k==0:continue
    ids=np.flatnonzero(part==k).tolist()
    anchor=min((tree.find(Vector(co[i])) for i in ids),key=lambda r:r[2])[1]
    v=mesh.data.vertices[anchor]
    weights={mesh.vertex_groups[g.group].name:g.weight for g in v.groups}
    if k in (1,2):weights={'Jaw':1.0}
    elif 3<=k<=9:weights={'Head':1.0}
    set_weights(ids,weights)

# Restrict jaw flexion to the lower lip; upper muzzle and horns stay on Head.
for i in np.flatnonzero((part==0)&(co[:,1]<-.451)&(co[:,2]>.295)):
    x,y,z=co[i]
    threshold=.316+.10*(y+.46)
    if z<threshold:set_weights([int(i)],{'Jaw':1.0})
    else:set_weights([int(i)],{'Head':1.0})

# Mouth FX/launch point follows the skull instead of the actor origin.
socket=bpy.data.objects.new('Socket_Mouth',None);bpy.context.scene.collection.objects.link(socket)
socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Head'
bpy.context.view_layer.update();socket.matrix_world.translation=(0,-.501,.317)

assert all(sum(g.weight for g in v.groups)>1e-5 for v in mesh.data.vertices)
report={'bones':len(arm.bones),'vertices':len(mesh.data.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.data.polygons),
        'unweighted':0,'joints':chains,'max_influences':max(len(v.groups) for v in mesh.data.vertices)}
(P/'work/rig_report.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['bones']<128
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',json.dumps({k:v for k,v in report.items() if k!='joints'}))

# Local stress probes use the shared posing helper.
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1200;sc.render.resolution_y=800
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.66,.7,.65)
sc.display.shading.show_cavity=True;sc.display.shading.background_type='VIEWPORT';sc.display.shading.background_color=(.15,.15,.15)
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.1
for label,changes,target,loc,scale in [
 ('jaw',[('Jaw','X',28)],(0,-.457,.339),(.30,-.66,.43),.19),
 ('neck',[('Neck1','Z',20),('Neck2','X',20),('Head','Z',-10)],(0,-.12,.21),(1,-1,.65),1.1),
 ('stride',[('UpperArm_L','X',-25),('ForeArm_L','X',35),('Thigh_R','X',25),('Shin_R','X',-35)],(0,-.12,.21),(1,-1,.65),1.1),
 ('tail',[(f'Tail{i}','Z',12) for i in range(1,11)],(0,.02,.18),(1,-1,.8),1.1)]:
    posing.reset(rig)
    for n,axis,degrees in changes:posing.rotate_world(rig,n,axis,degrees)
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    sc.render.filepath=str(P/'review'/f'stress_{label}.png');bpy.ops.render.render(write_still=True)
