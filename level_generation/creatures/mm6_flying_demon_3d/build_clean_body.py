"""Local derivative geometry; retain the repaired bind and skin away from changed anatomy."""
import json, math
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Matrix, Vector

P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'source/walking_demon_master.blend'))
scene=bpy.context.scene;scene.name='MM6_Flying_Demon'
body=next(o for o in scene.objects if o.get('material_role')=='body')
rig=next(o for o in scene.objects if o.type=='ARMATURE')
scene.render.fps=48
for o in scene.objects:
 for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
  if owner and owner.animation_data: owner.animation_data_clear()
for b in rig.pose.bones: b.matrix_basis=Matrix.Identity(4)
body.name='Flying_Demon_Body';rig.name='Flying_Demon_Rig'
rig.parent.name='Flying_Demon_Visibility'
source=np.load(P/'work/source_geometry.npz')
vertices=source['vertices'];weights=source['weights'];names=list(source['names']);colors=source['colors']
inspection=json.loads((P/'work/source_inspection.json').read_text())
tail_names=[f'Bone_{i:03d}' for i in range(20,14,-1)]
tail_weight=weights[:,[names.index(n) for n in tail_names]].sum(1)
tail_mask=(tail_weight>.32)&(vertices[:,1]>-.075)
clasp_ids=set(inspection['components'][3]['vertex_ids'])
assert len(clasp_ids)==249
remove=set(np.flatnonzero(tail_mask))|clasp_ids
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
before_boundary={e for e in bm.edges if e.is_boundary}
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(remove)],context='VERTS')
new_edges=[e for e in bm.edges if e.is_boundary and e not in before_boundary]
assert new_edges and all(e.calc_length()<.13 for e in new_edges)
caps=bmesh.ops.holes_fill(bm,edges=new_edges,sides=0)['faces']
uvlayer=bm.loops.layers.uv.active
cap_vertices={v for f in caps for v in f.verts}
cap_x=[v.co.x for v in cap_vertices];cap_z=[v.co.z for v in cap_vertices]
for face in caps:
 for loop in face.loops:
  co=loop.vert.co;loop[uvlayer].uv=(2.575+.04*(co.x-min(cap_x))/(max(cap_x)-min(cap_x)),2.66+.15*(co.z-min(cap_z))/(max(cap_z)-min(cap_z)))
 face.material_index=0
bmesh.ops.triangulate(bm,faces=caps)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free()

# The harness is part of the torso surface. Smooth only its raised green strips,
# preserving their surrounding skin boundary instead of remeshing the whole body.
# Original vertex IDs are retained explicitly through deletion to locate that patch.
survivors=[i for i in range(len(vertices)) if i not in remove]
assert len(survivors)==len(body.data.vertices)
harness=(colors[:,1]>colors[:,0]*1.22)&(colors[:,1]>colors[:,2]*1.07)&(vertices[:,2]>1.15)&(vertices[:,2]<1.51)
harness_ids={j for j,i in enumerate(survivors) if harness[i]}
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
selected={bm.verts[i] for i in harness_ids}
for _ in range(4):selected.update({e.other_vert(v) for v in list(selected) for e in v.link_edges})
fixed={v for v in selected if any(e.other_vert(v) not in selected for e in v.link_edges)}
for iteration in range(35):
 bmesh.ops.smooth_vert(bm,verts=list(selected-fixed),factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(body.data);bm.free()

# Slim soft tissue around each existing bind axis; bone lengths/joint centres stay fixed.
for v in body.data.vertices:
 original=survivors[v.index];co=v.co.copy();delta=Vector()
 for side in ('Left','Right'):
  for part,factor in [('Arm',.78),('ForeArm',.78),('UpLeg',.77),('Leg',.84)]:
   name='mixamorig:'+side+part;weight=weights[original,names.index(name)]
   if part=='ForeArm':
    weight+=sum(weights[original,names.index(f'Demon_{side}_ForearmTwist{i}')] for i in range(3))
   if weight<1e-5: continue
   b=rig.data.bones[name];a=b.head_local
   endpoint=rig.data.bones['mixamorig:'+side+('Hand' if part=='ForeArm' else 'Leg' if part=='UpLeg' else 'Foot' if part=='Leg' else 'ForeArm')].head_local
   axis=(endpoint-a).normalized();radial=co-a-axis*(co-a).dot(axis)
   delta+=radial*(factor-1)*min(1,weight)
  foot_weight=weights[original,names.index('mixamorig:'+side+'Foot')]
  if foot_weight>.02:
   foot=rig.data.bones['mixamorig:'+side+'Foot'];delta.x+=(co.x-foot.head_local.x)*(-.26)*foot_weight
 v.co+=delta
for component in inspection['components'][1:3]:
 for original in component['vertex_ids']:
  v=body.data.vertices[survivors.index(original)]
  center=Vector((-.107 if v.co.x<0 else .095,-.255,1.56))
  v.co=center+Vector(((v.co.x-center.x)*.72,(v.co.y-center.y)*.78,(v.co.z-center.z)*.59))
for uv in body.data.uv_layers.active.data: uv.uv=uv.uv-Vector((2,2)) if uv.uv.x>2 else uv.uv*.60+Vector((.02,.02))
body.data.update()
hips=body.vertex_groups['mixamorig:Hips']
tail_indices={body.vertex_groups[n].index for n in tail_names}
for v in body.data.vertices:
 w=sum(g.weight for g in v.groups if g.group in tail_indices)
 if w>0:
  current=next((g.weight for g in v.groups if g.group==hips.index),0)
  hips.add([v.index],current+w,'REPLACE')
spine=body.vertex_groups['mixamorig:Spine1']
clasp_group=body.vertex_groups['Bone_024'].index
for v in body.data.vertices:
 w=next((g.weight for g in v.groups if g.group==clasp_group),0)
 if w:
  current=next((g.weight for g in v.groups if g.group==spine.index),0);spine.add([v.index],current+w,'REPLACE')
for name in tail_names+['Bone_024','Bone_023']:
 if name in body.vertex_groups: body.vertex_groups.remove(body.vertex_groups[name])

bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name in tail_names+['Bone_024','Bone_023']:
 if name in rig.data.edit_bones: rig.data.edit_bones.remove(rig.data.edit_bones[name])
wing_points={}
for side,sign in [('Left',1),('Right',-1)]:
 root=Vector((sign*.105,.005,1.365));elbow=Vector((sign*.16,.030,1.65));wrist=Vector((sign*.19,.035,1.94))
 ends=[Vector((sign*x,y,z)) for x,y,z in [(1.24,.095,2.01),(.92,.10,1.81),(.66,.12,1.56),(.36,.10,1.33)]]
 wing_points[side]=(root,elbow,wrist,ends)
 for name,head,tail,parent in [
  (f'Wing_{side}_Root',root,elbow,'mixamorig:Spine2'),
  (f'Wing_{side}_Upper',elbow,wrist,f'Wing_{side}_Root'),
  *[(f'Wing_{side}_Finger{i+1}',wrist,end,f'Wing_{side}_Upper') for i,end in enumerate(ends)]]:
  b=rig.data.edit_bones.new(name);b.head=head;b.tail=tail;b.parent=rig.data.edit_bones[parent];b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')

def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.73
 return m
skin=material('Flying_Demon_Clay',(.24,.10,.22));ivory=material('Flying_Demon_Ivory',(.73,.69,.55));web=material('Flying_Demon_Membrane',(.11,.065,.085))
body.data.materials[0]=skin
body.data.materials[3]=ivory
spike_groups={body.vertex_groups[name].index for name in ['Bone_040','Bone_041','Bone_035','Bone_036'] if name in body.vertex_groups}
spike_ids={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in spike_groups)>.82}
for j,i in enumerate(survivors):
 c=colors[i];x,y,z=vertices[i]
 if z>1.40 and abs(x)>.12 and c[0]>.75 and c[1]>.65 and c[0]>c[2]*1.10: spike_ids.add(j)
for component in inspection['components'][9:]:
 if component['vertices']<40 and not any('Head' in n or n=='Bone_025' for n,w in component['weights']):
  spike_ids.update(survivors.index(i) for i in component['vertex_ids'] if i in survivors)
for face in body.data.polygons:
 if all(i in spike_ids for i in face.vertices): face.material_index=3
# Keep the original valid chest topology. Intrinsic smoothing removes the
# raised harness profile without flattening its folded boundary onto one plane.
removed_chest_faces=0
before_validation=len(body.data.polygons)
body.data.validate(verbose=True,clean_customdata=False)
removed_duplicates=before_validation-len(body.data.polygons)
assert removed_duplicates==1,removed_duplicates
for face in body.data.polygons:face.use_smooth=True
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
iris=body.data.materials[1].copy();iris.name='Flying_Demon_Blue_Eyes'
for node in iris.node_tree.nodes:
 if node.type=='BSDF_PRINCIPLED':
  node.inputs['Base Color'].default_value=(.005,.32,.8,1)
  node.inputs['Emission Color'].default_value=(.005,.28,.7,1);node.inputs['Emission Strength'].default_value=.45
body.data.materials[1]=iris

def make_mesh(name,positions,faces,uvs,groups,mat,role):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(positions,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.parent=rig;obj['material_role']=role
 mesh.materials.append(mat);uv=mesh.uv_layers.new(name='UVMap')
 for poly in mesh.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices: uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 for index,weights_for_vertex in enumerate(groups):
  for group,weight in weights_for_vertex.items():
   vg=obj.vertex_groups.get(group) or obj.vertex_groups.new(name=group);vg.add([index],weight,'REPLACE')
 modifier=obj.modifiers.new('Native Wing Skin','ARMATURE');modifier.object=rig
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 return obj

def tube(points,radii,bone,uvbox,name,mat):
 positions=[];uvs=[];groups=[];faces=[];sides=10
 for i,p in enumerate(points):
  tangent=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
  x=tangent.cross(Vector((0,1,0))).normalized();y=tangent.cross(x).normalized()
  for j in range(sides+1):
   angle=j*2*math.pi/sides;positions.append(tuple(p+radii[i]*(x*math.cos(angle)+y*math.sin(angle))))
   u,v,w,h=uvbox;uvs.append((u+w*j/sides,v+h*(.045+.91*i/(len(points)-1))));groups.append({bone:1})
 for i in range(len(points)-1):
  for j in range(sides):
   a=i*(sides+1)+j;faces.append((a,a+1,a+sides+2,a+sides+1))
 faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*(sides+1)+j for j in range(sides))])
 obj=make_mesh(name,positions,faces,uvs,groups,mat,'horn' if 'Horn' in name else 'wing_strut')
 caps=[f for f in obj.data.polygons if len(f.vertices)>4]
 assert len(caps)==2
 u,v,w,h=uvbox;uv=obj.data.uv_layers.active.data
 for i,cap in enumerate(caps):
  for j,li in enumerate(cap.loop_indices):
   a=j*2*math.pi/len(cap.vertices);uv[li].uv=(u+w*(.5+.022*math.cos(a)),v+h*((.02 if i==0 else .98)+.018*math.sin(a)))
 return obj

for side,sign in [('Left',1),('Right',-1)]:
 points=[Vector((sign*x,y,z)) for x,y,z in [(.073,-.215,1.64),(.095,-.20,1.69),(.112,-.215,1.75),(.104,-.25,1.80),(.079,-.28,1.83)]]
 tube(points,[.027,.025,.019,.011,.001], 'mixamorig:Head',(.03 if sign==1 else .18,.66,.12,.30),f'Flying_Horn_{side}',ivory)
 root,elbow,wrist,ends=wing_points[side]
 positions=[];faces=[];uvs=[];groups=[]
 radial=10;angular=8;contour=ends+[root];grid={}
 # Shared front/back topology with a closed edge. The membrane is curved in depth.
 for layer in range(2):
  for sector in range(4):
   for j in range(angular+1):
    t=j/angular;end=contour[sector].lerp(contour[sector+1],t)
    end=wrist+(end-wrist)*(1-.23*math.sin(math.pi*t))
    for i in range(radial+1):
     u=i/radial;p=wrist.lerp(end,u);p.y+=(-.028*math.sin(math.pi*u)*math.sin(math.pi*t)+(layer-.5)*.006)
     key=(layer,sector*angular+j,i)
     if key not in grid:
      grid[key]=len(positions);positions.append(tuple(p))
      local_x=(abs(p.x)-.10)/1.16;local_z=(p.z-1.30)/.75
      umin=.65 if sign==1 else .825;vmin=.505 if layer==0 else .015
      uvs.append((umin+.155*local_x,vmin+.46*local_z))
      g={f'Wing_{side}_Upper':1-u}
      g[f'Wing_{side}_Finger{sector+1}']=u*(1-t)
      b=f'Wing_{side}_Finger{sector+2}' if sector<3 else f'Wing_{side}_Root'
      g[b]=g.get(b,0)+u*t;groups.append({k:v for k,v in g.items() if v>1e-8})
  for j in range(4*angular):
   for i in range(radial):
    q=(grid[layer,j,i],grid[layer,j+1,i],grid[layer,j+1,i+1],grid[layer,j,i+1])
    faces.append(q if layer==0 else tuple(reversed(q)))
 for j in range(4*angular): faces.append((grid[0,j,radial],grid[1,j,radial],grid[1,j+1,radial],grid[0,j+1,radial]))
 for j in (0,4*angular):
  for i in range(radial): faces.append((grid[0,j,i],grid[0,j,i+1],grid[1,j,i+1],grid[1,j,i]))
 obj=make_mesh(f'Flying_Wing_{side}',positions,faces,uvs,groups,web,'wing')
 # Collapse duplicate fan centres and seams at equal UVs, not opposing membrane sides.
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 for part,a,b in [('Root',root,elbow),('Upper',elbow,wrist),*[(f'Finger{i+1}',wrist,e) for i,e in enumerate(ends)]]:
  points=[a.lerp(b,t) for t in [0,.2,.4,.6,.8,1]]
  for k,p in enumerate(points): p.y-=.014*math.sin(k*math.pi/5)
  tube(points,[.012,.011,.010,.008,.005,.0015],f'Wing_{side}_{part}',(.32 if sign==1 else .42,.66,.08,.15),f'Wing_Strut_{side}_{part}',web)

for o in scene.objects:
 if o.name.startswith('Demon_Death_Plume') or o.name.startswith('Demon_Ash'):
  o.hide_render=True;o.hide_set(True)
body['derivative_source']='selected walking-demon master; local anatomical corrections'
report={'removed_tail_vertices':int(tail_mask.sum()),'removed_clasp_vertices':249,'tail_cap_faces':len(caps),'replaced_folded_chest_faces':removed_chest_faces,'duplicate_chest_faces_removed':removed_duplicates,
 'smoothed_harness_vertices':len(harness_ids),'new_wing_joints':12,
 'limb_radius_factors':{'arm':.78,'forearm':.78,'thigh':.77,'shin':.84,'foot_width':.74},
 'rest_chain_lengths_unchanged':True,'additional_digit':'retained inherited depth inference',
 'uv_layout':'Original body charts at (0.02,0.02) scaled 0.60; unique front/back wing charts in right strip; horn and strut charts above body.'}
(P/'work/model_changes_clean_chest.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anatomy_clean_chest.blend'),compress=True)
print('Built Flying Demon derivative',report,flush=True)
