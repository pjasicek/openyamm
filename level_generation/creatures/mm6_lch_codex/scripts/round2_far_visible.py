"""Silhouette-only protected collapse at actual actor pixel heights; clips never edited."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';W=P/'work/round2';sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/triangle_reduction/baseline/work/rig_textured.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];bones={b.name for b in rig.data.bones}
for ob in list(bpy.data.objects):
    if ob not in (body,rig):bpy.data.objects.remove(ob,do_unlink=True)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());coords=np.array([tuple(v.co)for v in ev.data.vertices]);lo=coords.min(0);hi=coords.max(0);center=(lo+hi)/2;human_height=hi[2]-lo[2]
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(1,1,1);sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=False
sc.display.render_aa='32';sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('SilhouetteCamera');cd.type='ORTHO';cam=bpy.data.objects.new('SilhouetteCamera',cd);sc.collection.objects.link(cam);sc.camera=cam
SIZES=[700,550,220,88];RES=[896,704,320,160];refs={};curve=[];selected=[]

def tris(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
def rigid(ob):
    names=[]
    for v in ob.data.vertices:
        weight=[(ob.vertex_groups[w.group].name,w.weight)for w in v.groups if ob.vertex_groups[w.group].name in bones and w.weight>1e-7]
        assert len(weight)==1 and abs(weight[0][1]-1)<1e-5,weight
        names.append(weight[0][0])
    assert all(names[e.vertices[0]]==names[e.vertices[1]]for e in ob.data.edges)
def render(ob,label,level):
    dest=R/'silhouette'/label/f'lod{level}';dest.mkdir(parents=True,exist_ok=True)
    sc.render.resolution_x=sc.render.resolution_y=RES[level];cd.ortho_scale=human_height*RES[level]/SIZES[level]
    masks=[]
    for k in range(8):
        a=k*math.pi/4;cam.location=Vector(center)+Vector((math.sin(a),-math.cos(a),0))*6
        cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest/f'{k}.png');bpy.ops.render.render(write_still=True)
        im=bpy.data.images.load(sc.render.filepath,check_existing=False);pixels=np.empty(RES[level]*RES[level]*4,np.float32);im.pixels.foreach_get(pixels);bpy.data.images.remove(im)
        masks.append(pixels.reshape(RES[level],RES[level],4)[:,:,3]>.5)
    if label=='baseline':refs[level]=masks;return None
    views=[{'intersection':int((a&b).sum()),'union':int((a|b).sum()),'iou':float((a&b).sum()/(a|b).sum())}for a,b in zip(refs[level],masks)]
    pooled=sum(v['intersection']for v in views)/sum(v['union']for v in views);minimum=min(v['iou']for v in views)
    result={'views':views,'pooled_iou':pooled,'min_iou':minimum,'pass':minimum>=.99 if level==0 else pooled>=.97 and (minimum>=.95 if level==3 else True)}
    (dest/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');return result
for level in range(4):render(body,'baseline',level)
(R/'camera.json').write_text(json.dumps({'projection':'orthographic','actor_height_px':SIZES,'canvas_px':RES,'height_m':human_height,'center_m':center.tolist(),'yaw_degrees':list(range(0,360,45))},indent=2)+'\n')

def protection(ob,level):
    g=ob.vertex_groups.get('ReductionAllowed')or ob.vertex_groups.new(name='ReductionAllowed');pid=ob.data.attributes['piece']
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());pos=np.array([tuple(v.co)for v in ev.data.vertices]);edge_ids=set()
    for k,mask in enumerate(refs[level]):
        edge=mask & (~np.roll(mask,1,0)|~np.roll(mask,-1,0)|~np.roll(mask,1,1)|~np.roll(mask,-1,1))
        a=k*math.pi/4;right=np.array([math.cos(a),math.sin(a),0]);delta=pos-center;scale=SIZES[level]/human_height
        px=np.rint(RES[level]/2+delta@right*scale).astype(int);py=np.rint(RES[level]/2+delta[:,2]*scale).astype(int)
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:
                x=np.clip(px+dx,0,RES[level]-1);y=np.clip(py+dy,0,RES[level]-1);edge_ids.update(np.where(edge[y,x])[0].tolist())
    contact={3,4,7,8,16,17,20,21,26,27,28,30,31,35}
    joints=[rig.data.bones[f'B_{s}_{j}'].head_local for s in 'LR'for j in ['UpperArm','Forearm','Thigh','Calf']]
    for v in ob.data.vertices:
        bone=next(ob.vertex_groups[w.group].name for w in v.groups if ob.vertex_groups[w.group].name in bones and w.weight>.5)
        value=.05 if v.index in edge_ids else 1.
        if pid.data[v.index].value>=100 and v.co.y<-.015 or any(k in bone for k in ['Hand','Finger']):value=min(value,.15)
        if any((v.co-j).length<.025 for j in joints):value=min(value,.03)
        if level==0 and pid.data[v.index].value in contact:value=0.
        g.add([v.index],value,'REPLACE')
    return g.name

def collapse(source,ratio,level):
    ob=source.copy();ob.data=source.data.copy();sc.collection.objects.link(ob);source.hide_render=True;ob.hide_render=False
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    group=protection(ob,level);mod=ob.modifiers.new('SilhouetteCollapse','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;mod.vertex_group=group;mod.vertex_group_factor=.0001 if level==0 else .000005
    bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name);ob.data.validate(clean_customdata=False);rigid(ob)
    ob.name='BodyCandidate';return ob

def save_selected(ob,level,label,metric):
    old=body.name;body.name='SourceHidden';ob.name='Body'
    path=W/f'lod{level}_selected.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));ob.name='BodyCandidate';body.name=old
    row={'level':level,'blend':str(path.relative_to(P)),'triangles':tris(ob),'silhouette':metric,'render':f'review/triangle_rebake/silhouette/{label}/lod{level}'}
    selected.append(row);return row

# Drop completely occluded pieces, retaining the outer silhouette and every weighted joint.
from mathutils.bvhtree import BVHTree
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data;me.calc_loop_triangles();pv=[x.value for x in me.attributes['piece'].data]
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[t.vertices for t in me.loop_triangles],all_triangles=True)
visible=set();viscount={};dirs=[Vector((math.sin(k*math.pi/8)*math.cos(z),math.cos(k*math.pi/8)*math.cos(z),math.sin(z)))for z in [-.5,0,.5]for k in range(16)]
for t in me.loop_triangles:
 center=sum((me.vertices[i].co for i in t.vertices),Vector())/3
 for d in dirs:
  if d.dot(t.normal)<=0:continue
  hit=tree.ray_cast(center+d*5,-d,6)
  if hit[0]is not None and (hit[0]-center).length<.0001:
   visible.add(pv[t.vertices[0]]);viscount[pv[t.vertices[0]]]=viscount.get(pv[t.vertices[0]],0)+1;break
print('VISIBLE_PIECES',sorted(visible),'HIDDEN',sorted(set(pv)-visible),flush=True)
ob=body.copy();ob.data=body.data.copy();sc.collection.objects.link(ob);body.hide_render=True;ob.hide_render=False
bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]not in visible],context='VERTS');bm.to_mesh(ob.data);bm.free()
print('VISIBLE_TRIS',tris(ob),flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
results=[]
for level,cap in [(1,3458),(2,1572),(3,628)]:
 for factor in [.01,.1,1]:
  candidate=ob.copy();candidate.data=ob.data.copy();sc.collection.objects.link(candidate);ob.hide_render=True;candidate.hide_render=False
  bpy.ops.object.select_all(action='DESELECT');candidate.select_set(True);bpy.context.view_layer.objects.active=candidate
  group=protection(candidate,level);mod=candidate.modifiers.new('VisibleCollapse','DECIMATE');mod.ratio=cap/tris(candidate);mod.use_collapse_triangulate=True;mod.vertex_group=group;mod.vertex_group_factor=factor
  bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name);rigid(candidate)
  label=f'visible{level}_{factor}';metric=render(candidate,label,level)
  body.name='SourceHidden';candidate.name='Body';path=W/f'{label}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));candidate.name='Candidate';body.name='Body'
  row={'level':level,'triangles':tris(candidate),'blend':str(path.relative_to(P)),'factor':factor,'metrics':metric};results.append(row);print('VISIBLE_TRIAL',row,flush=True)
  bpy.data.objects.remove(candidate,do_unlink=True)
(R/'visible_far.json').write_text(json.dumps(results,indent=2)+'\n')
