"""Revision 02: retain topology/UVs/weights, put stronger limbs beneath the trunk."""
import bpy, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/revision02/previous/mm6_wyrm.blend'))
rig=bpy.data.objects['Wyrm_Rig'];mesh=bpy.data.objects['Wyrm'];sc=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for o in list(bpy.data.objects):
 if o.name.startswith('Wyrm_Remains'):bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
old={b.name:b.matrix_local.copy() for b in rig.data.bones}
lengths={b.name:b.length for b in rig.data.bones}
uv=np.array([l.uv[:] for l in mesh.data.uv_layers.active.data])
coords=np.array([v.co[:] for v in mesh.data.vertices]);names={g.index:g.name for g in mesh.vertex_groups}
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
changed={}
for side,sign in [('L',1),('R',-1)]:
 for chain,xs,thickness in [(['UpperArm','ForeArm','FrontPaw'],[.036,.042,.043,.044],[1.12,1.25,1.0]),
                           (['Thigh','Shin','HindPaw'],[.035,.037,.036,.049],[1.10,1.18,1.0])]:
  for i,name in enumerate(chain):
   name+='_'+side;b=rig.data.edit_bones[name];b.head.x=sign*xs[i];b.tail.x=sign*xs[i+1]
   b.align_roll(Vector((0,-1,0)));changed[name]=thickness[i]
bpy.ops.object.mode_set(mode='OBJECT')
transforms={name:rig.data.bones[name].matrix_local @ Matrix.Diagonal((thick,rig.data.bones[name].length/lengths[name],thick,1)) @ old[name].inverted() for name,thick in changed.items()}
for v in mesh.data.vertices:
 co=v.co.copy();delta=Vector()
 for g in v.groups:
  name=names[g.group]
  if name in transforms:delta+=g.weight*(transforms[name]@co-co)
 v.co=co+delta
# Keep the contact sole on the paw instead of letting forearm weights drag its heel through the floor.
sole_vertices=0
for v in mesh.data.vertices:
 if v.co.z>=.035:continue
 for lower,paw in [('ForeArm_'+side,'FrontPaw_'+side) for side in 'LR']+[('Shin_'+side,'HindPaw_'+side) for side in 'LR']:
  weights={names[g.group]:g.weight for g in v.groups}
  if weights.get(lower,0)+weights.get(paw,0)<.95:continue
  u=max(0,min(1,(.035-v.co.z)/.021));u=u*u*(3-2*u)
  transfer=weights.get(lower,0)*u
  if transfer>1e-6:
   mesh.vertex_groups[paw].add([v.index],weights.get(paw,0)+transfer,'REPLACE')
   remaining=weights.get(lower,0)-transfer
   if remaining<1e-6:mesh.vertex_groups[lower].remove([v.index])
   else:mesh.vertex_groups[lower].add([v.index],remaining,'REPLACE')
   sole_vertices+=1
  v.co.z=max(0,v.co.z)
mesh.data.update();bpy.context.view_layer.update()
assert np.array_equal(uv,np.array([l.uv[:] for l in mesh.data.uv_layers.active.data]))
assert len(mesh.data.polygons)==14413
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in mesh.data.vertices)
report={'revision':'02','triangles':len(mesh.data.polygons),'uvs_unchanged':True,'weights':'Retained except smooth lower-leg to paw transfer at the contact soles','sole_weight_vertices':sole_vertices,
 'front_ankle_spacing_m':abs(rig.data.bones['FrontPaw_L'].head_local.x-rig.data.bones['FrontPaw_R'].head_local.x),
 'previous_front_ankle_spacing_m':abs(old['FrontPaw_L'].translation.x-old['FrontPaw_R'].translation.x),
 'radial_thickness_factors':changed,'max_vertex_move_m':float(np.linalg.norm(np.array([v.co[:] for v in mesh.data.vertices])-coords,axis=1).max())}
(P/'review/revision02/anatomy.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/revision02_rest.blend'))
print(json.dumps(report))
