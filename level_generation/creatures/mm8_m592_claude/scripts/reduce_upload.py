"""Protect face and claws, reduce the weighted torso, freeze triangles and prepare body/head paint inputs."""
from pathlib import Path
import bpy,bmesh,json,numpy as np,sys
from mathutils import kdtree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/full_actions.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();names=[g.name for g in body.vertex_groups];co=np.array([tuple(v.co) for v in body.data.vertices]);pv=np.array([v.value for v in body.data.attributes['piece'].data]);protect=body.vertex_groups.new(name='_protect');headv=(abs(co[:,0])<.30)&(co[:,1]<-.23)&(co[:,2]>1.04);headv|=(abs(co[:,0])<.23)&(co[:,1]<-.10)&(co[:,2]>1.42)
protected=[]
for v in body.data.vertices:
 hand=sum(e.weight for e in v.groups if any(t in names[e.group] for t in ('Hand','Finger')))>.25
 if hand or headv[v.index] or pv[v.index]!=0:protect.add([v.index],1,'REPLACE');protected.append(v.co.copy())
original=body.copy();original.data=body.data.copy();original.name='BodyHigh';bpy.context.collection.objects.link(original);original.hide_set(True);original.hide_render=True
tri=lambda ob:sum(len(f.vertices)-2 for f in ob.data.polygons)
before=tri(body)
for ob in bpy.context.view_layer.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body;d=body.modifiers.new('Silhouette reduction','DECIMATE');d.ratio=11000/before;d.use_collapse_triangulate=True;d.vertex_group='_protect';d.invert_vertex_group=True;d.vertex_group_factor=1000;bpy.ops.object.modifier_move_to_index(modifier=d.name,index=0);bpy.ops.object.modifier_apply(modifier=d.name);body.vertex_groups.remove(body.vertex_groups['_protect'])
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();kd=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance();error=max(kd.find(v)[2] for v in protected);assert error<.0002,error
me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);headv=((abs(co[:,0])<.30)&(co[:,1]<-.23)&(co[:,2]>1.04))|((abs(co[:,0])<.23)&(co[:,1]<-.10)&(co[:,2]>1.42));head=[sum(bool(headv[i]) for i in f.vertices)>=2 for f in me.polygons];attr=me.attributes.get('head') or me.attributes.new('head','INT','FACE');attr.data.foreach_set('value',[int(x) for x in head]);assert sum(head)>1000
# Limit skinning to the renderer's four influences after the twist ramps and region reduction.
for v in me.vertices:
 gs=sorted([(e.group,e.weight) for e in v.groups if e.weight>1e-6],key=lambda x:-x[1])[:4];total=sum(w for _,w in gs)
 for g in body.vertex_groups:g.remove([v.index])
 for g,w in gs:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('GuardianBody');mat.use_nodes=True;body.data.materials.clear();body.data.materials.append(mat);hm=bpy.data.materials.new('GuardianHead');hm.use_nodes=True;body.data.materials.append(hm)
for f,h in zip(me.polygons,head):f.material_index=int(h)
for uv in list(me.uv_layers):me.uv_layers.remove(uv)
me.uv_layers.new(name='UVMap')
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
for ishead in (False,True):
 for f in me.polygons:f.select=bool(head[f.index])==ishead
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.006,area_weight=.1,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.006,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
huv=me.uv_layers.new(name='HeadUV')
for a,b in zip(huv.data,me.uv_layers['UVMap'].data):a.uv=b.uv
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'));out=P/'texturing';out.mkdir(exist_ok=True)
for kind in ('body','head'):
 up=body.copy();up.data=body.data.copy();bpy.context.collection.objects.link(up);up.parent=None;up.modifiers.clear();up.vertex_groups.clear();up.data.materials.clear();neutral=bpy.data.materials.new('Neutral '+kind);neutral.use_nodes=True;up.data.materials.append(neutral)
 if kind=='head':
  bm=bmesh.new();bm.from_mesh(up.data);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[hd]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(up.data);bm.free()
 for f in up.data.polygons:f.material_index=0
 for ob in bpy.context.view_layer.objects:ob.select_set(ob==up)
 bpy.context.view_layer.objects.active=up;bpy.ops.export_scene.gltf(filepath=str(out/f'm592_{kind}_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_attributes=False);bpy.data.objects.remove(up,do_unlink=True)
report={'triangles_before':before,'triangles_after':tri(body),'protected_vertex_error_m':error,'head_triangles':sum(head),'bones':len(rig.data.bones),'maximum_influences':4,'head_uv':'Independent packed head layout; body Meshy UV transfer must preserve head faces.','master':'work/rig_reduced.blend'};(P/'review/reduction.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCTION',report,flush=True)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/reduced_body'),.85,2.6,views=('front','left','back','three_quarter'),resolution=(700,700));common.render_views(str(P/'review/reduced_head'),1.28,.8,views=('front','left','three_quarter'),resolution=(700,700))
for name,f in [('Attack',23),('Running',12),('Death',39)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);common.render_views(str(P/f'review/reduced_{name}'),.95,3.0,views=('front','left'),resolution=(650,650))
