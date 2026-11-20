"""Repair four open rock backs, reduce rigid pieces, fit a cap/jaw/rubble rig and unwrap once."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm8_m584_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_parts.blend'))
mat=bpy.data.materials.new('Boulder');mat.use_nodes=True;mat.diffuse_color=(.28,.27,.28,1)
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=.9
groups={};records=[]
for o in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
 idx=int(o.name[4:]);bm=bmesh.new();bm.from_mesh(o.data)
 boundary=[e for e in bm.edges if e.is_boundary]
 fill=bmesh.ops.holes_fill(bm,edges=boundary,sides=0) if boundary else {'faces':[]}
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.to_mesh(o.data);bm.free()
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 mod=o.modifiers.new('SilhouetteReduction','DECIMATE');mod.ratio=.65;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
 co=np.array([tuple(v.co) for v in o.data.vertices]);c=co.mean(0)
 owner='Cap' if c[2]>.85 else ('Jaw' if c[2]>.36 and c[1]<.35 else 'Base')
 sector=int(((math.atan2(c[1],c[0])+math.pi)/(2*math.pi)*8))%8
 layer=int(c[2]>1.45) if owner=='Cap' else 0
 group=f'{owner}_{layer}_{sector}'
 groups.setdefault(group,{'owner':owner,'pieces':[]})['pieces'].append(idx)
 o.vertex_groups.new(name=group).add(list(range(len(o.data.vertices))),1,'REPLACE')
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=True
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[idx]*len(o.data.vertices))
 records.append({'piece':idx,'group':group,'triangles':len(o.data.polygons),'sealed_edges':len(boundary)})
for o in bpy.data.objects:o.select_set(o.type=='MESH')
body=bpy.data.objects['Part00'];bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
# One continuous UV atlas; shell intersections are deliberate stone-on-stone overlaps.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.006,area_weight=.3,correct_aspect=True)
bpy.ops.object.mode_set(mode='OBJECT')
arm=bpy.data.armatures.new('BoulderRig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
def bone(name,point,parent=None):
 b=arm.edit_bones.new(name);b.head=point;b.tail=Vector(point)+Vector((0,.15,0));b.parent=arm.edit_bones.get(parent) if parent else None
 return b
bone('Root',(0,0,0));bone('Core',(0,0,.65),'Root');bone('Cap',(0,.48,.85),'Core');bone('Jaw',(0,.45,.40),'Core')
co=np.array([tuple(v.co) for v in body.data.vertices])
for name,g in groups.items():
 ids=[v.index for v in body.data.vertices if any(body.vertex_groups[w.group].name==name for w in v.groups)]
 c=co[ids].mean(0);g['center']=c.tolist();g['vertex_count']=len(ids)
 bone(name,c,'Core' if g['owner']=='Base' else g['owner'])
bpy.ops.object.mode_set(mode='OBJECT')
mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig;body.parent=rig
bpy.context.view_layer.update()
sock=bpy.data.objects.new('Socket_Mouth',None);bpy.context.collection.objects.link(sock)
sock.parent=rig;sock.parent_type='BONE';sock.parent_bone='Core';sock.matrix_world=Matrix.Translation((0,-.83,.84))
sock.empty_display_size=.04
for pb in rig.pose.bones:pb.rotation_mode='XYZ'
assert len(arm.bones)<64
assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in body.data.vertices)
report={'groups':groups,'pieces':records,'triangles':len(body.data.polygons),'bones':len(arm.bones),'unit_height_m':2,'rigid_weights':True}
(P/'work/rig_spec.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig.blend'))
print('RIG',report['triangles'],'triangles',report['bones'],'bones')
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/rig_neutral'),1,2.8,views=('front','left','back'),resolution=(800,800))
rig.pose.bones['Cap'].rotation_euler.x=math.radians(-25);rig.pose.bones['Jaw'].rotation_euler.x=math.radians(4)
bpy.context.view_layer.update()
common.render_views(str(P/'review/rig_gape'),1,2.8,views=('front','left','back'),resolution=(800,800))
