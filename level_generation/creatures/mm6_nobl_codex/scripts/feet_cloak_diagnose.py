import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/feet_cloak_20261011';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
co=np.array([v.co[:] for v in me.vertices])
def setact(n,f=0):
 r.animation_data.action=bpy.data.actions.get(n)
 if r.animation_data.action:r.animation_data.action_slot=r.animation_data.action.slots[0]
 else:
  for b in r.pose.bones:b.matrix_basis.identity()
 sc.frame_set(f);bpy.context.view_layer.update()
def camera(name,c,d,scale):
 cam=common.ortho_camera(name,Vector(c)+Vector(d),(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-Vector(d)).to_track_quat('-Z','Y')
 sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=750;sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
report={'pieces':{},'feet':{},'cape':{}}
for n in sorted(set(pv)):
 ids=np.where(pv==n)[0]
 if n<29:report['pieces'][str(n)]={'n':len(ids),'lo':co[ids].min(0).tolist(),'hi':co[ids].max(0).tolist()}
for side in 'LR':
 ids=np.where((pv==2)&(co[:,2]<.047)&(co[:,0]*(1 if side=='L' else -1)>0))[0]
 report['feet'][side]={'ids':ids.tolist(),'rest':co[ids].tolist(),'poses':{}}
 for name,f in [('none',0),('Standing',0),('Walking',0),('Walking',6),('Walking',12),('Walking',18),('Death',55)]:
  setact(name,f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();X=np.array([m.vertices[int(i)].co[:] for i in ids]);ev.to_mesh_clear()
  report['feet'][side]['poses'][name+str(f)]={'co':X.tolist(),'bones':{b.name:{'head':list(b.head),'quat':list(b.matrix.to_quaternion()),'deform':list((b.matrix@b.bone.matrix_local.inverted()).to_quaternion())} for b in r.pose.bones if b.name in [f'B_{side}_Foot',f'B_{side}_Toe0',f'B_{side}_Calf']}}
setact('Death',55)
upper=np.where((pv==0)&(co[:,2]>1.25)&(co[:,1]>0))[0]
report['cape']['upperweights']=[{'i':int(i),'co':co[i].tolist(),'w':{o.vertex_groups[g.group].name:g.weight for g in me.vertices[int(i)].groups if g.weight>.01}} for i in upper]
np.savez(out/'before_mesh.npz',co=co,piece=pv)
common.workbench_clay(sc,False);sc.display.shading.show_cavity=False
for ob in sc.objects:
 if ob.type=='MESH' and ob!=o:ob.hide_render=True
o.data.materials.clear()
for name,color in [('cape',(.3,.65,.3,1)),('body',(.6,.1,.1,1)),('trim',(.8,.8,.1,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;o.data.materials.append(m)
for f in me.polygons:f.material_index=0 if pv[f.vertices[0]]==0 else 1 if pv[f.vertices[0]] in [1,2] else 2
camera('corpse_parts',(0,-.65,.16),(0,0,2),1.1)
camera('corpse_parts_oblique',(0,-.65,.16),(0,1,2),1.1)
setact('none');camera('feet_rest',(0,-.04,.09),(0,-2,.03),.72)
setact('Standing');camera('feet_standing',(0,-.04,.09),(0,-2,.03),.72)
(out/'diagnosis.json').write_text(json.dumps(report,indent=1))
print('FEET_DIAG',json.dumps({s:{'n':len(v['ids']),'rest_z':[min(c[2] for c in v['rest']),max(c[2] for c in v['rest'])],'ranges':{n:[min(c[2] for c in a['co']),max(c[2] for c in a['co'])] for n,a in v['poses'].items()}} for s,v in report['feet'].items()}))
