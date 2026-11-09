"""Topology-only measured reduction from the accepted rig. One background Blender, four threads."""
import bpy,bmesh,sys,math,json,subprocess,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];LEVEL=int(os.environ['LCH_LOD']);ROOT=P/'review/triangle_reduction';R=ROOT/f'adaptive_subpixel_lod{LEVEL}';R.mkdir(exist_ok=True);W=P/f'work/round1/adaptive_subpixel_lod{LEVEL}';W.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'baseline/work/rig_textured.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for ob in list(bpy.data.objects):
    if ob not in (body,rig):bpy.data.objects.remove(ob,do_unlink=True)
# Bind actual accepted texture images explicitly; the UV authoring blend carries placeholder materials.
for slot,label in enumerate(['lch','lch_head']):
    mat=body.data.materials[slot];mat.use_nodes=True;nt=mat.node_tree
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/f'textures/{label}_basecolor_1k.png'))
    nt.nodes.active=tex;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');nt.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
normal_source=body.copy();normal_source.data=body.data.copy();normal_source.modifiers.clear();scene.collection.objects.link(normal_source);normal_source.hide_render=True;normal_source.name='AcceptedNormals'
# A high influence means eligible for collapse; critical regions have zero influence.
g=body.vertex_groups.new(name='ReductionAllowed');protected=set();soft=set();face_protect=set()
me=body.data;pid=me.attributes['piece'];bones={b.name for b in rig.data.bones}
for v in me.vertices:
    bn=next(body.vertex_groups[w.group].name for w in v.groups if body.vertex_groups[w.group].name in bones)
    # Face, teeth, eyes, hands and joint caps are protected. Back cranium can simplify.
    if any(x in bn for x in ('Hand','Finger')) or pid.data[v.index].value>101:face_protect.add(v.index)
    if pid.data[v.index].value>=100 and v.co.y<-.015:face_protect.add(v.index)
    for name in ['B_'+sd+'_'+joint for sd in 'LR' for joint in ['UpperArm','Forearm','Thigh','Calf']]:
        if (v.co-rig.data.bones[name].head_local).length<.025:protected.add(v.index)
# UV seam endpoints get higher collapse cost; per-corner UV layers are carried by BMesh.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.normal_update()
uv_layers=[bm.loops.layers.uv.get(n)for n in ['UVMap','HeadUV']]
for e in bm.edges:
    if not e.is_manifold:
        protected.update(v.index for v in e.verts);continue
    for uv_layer in uv_layers:
        for vertex in e.verts:
            uv=[loop[uv_layer].uv for face in e.link_faces for loop in face.loops if loop.vert==vertex]
            if (uv[0]-uv[1]).length>1e-5:soft.update(v.index for v in e.verts)
bm.free()
fixed=set(protected)
# Protect the actual visible silhouettes, rather than every hidden local normal discontinuity.
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();coords=np.array([tuple(body.matrix_world@v.co)for v in posed.vertices]);ev.to_mesh_clear()
distances_map=np.load(ROOT/f'silhouette_lod{LEVEL}.npz')['distance'];focal=480/math.tan(math.radians(35)/2);screen_distance=json.loads((ROOT/'camera.json').read_text())['distance_m'][LEVEL]
for k in range(8):
    angle=k*math.pi/4;target=np.array([0,.15,.9]);eye=target+np.array([math.sin(angle),-math.cos(angle),0])*screen_distance
    forward=(target-eye)/screen_distance;right=np.cross(forward,[0,0,1]);delta=coords-eye
    px=np.rint(480+focal*(delta@right)/(delta@forward)).astype(int);py=np.rint(959-(480+focal*delta[:,2]/(delta@forward))).astype(int)
    valid=(px>=0)&(px<960)&(py>=0)&(py<960);ids=np.where(valid)[0]
    protected.update(ids[np.abs(distances_map[k,py[ids],px[ids]])<=1.01].tolist())
for v in me.vertices:g.add([v.index],0. if v.index in fixed else (.03 if v.index in protected else (.15 if v.index in face_protect or v.index in soft else 1.)),'REPLACE')
(R/'protection.json').write_text(json.dumps({'vertices':len(me.vertices),'hard_protected':len(protected),'weighted_face':len(face_protect),'groups':'25 mm joint caps and open boundaries hard protected; 8-view switch-distance silhouette weighted 0.03; face, eyes/teeth/crown, hands/fingers and UV seams weighted 0.15; no held props; rigid disconnected pieces retain single-bone weights'},indent=2))
# Quantitative texture review uses the same studio renderer as the accepted clip sheets.
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_cavity=False;scene.display.shading.show_shadows=False
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.display.render_aa='32';scene.view_settings.view_transform='Standard'
camdata=bpy.data.cameras.new('Round1Camera');camdata.type='PERSP';camdata.lens_unit='FOV';camdata.angle=math.radians(35)
cam=bpy.data.objects.new('Round1Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(0)
lo=Vector((1e9,)*3);hi=-lo
for v in body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices:
    lo=Vector(map(min,lo,v.co));hi=Vector(map(max,hi,v.co))
diameter=(hi-lo).length;focal=480/math.tan(math.radians(35)/2)
distances=[4.4]+[diameter*.5+focal*diameter/px for px in [500,200,80]]
(R/'camera.json').write_text(json.dumps({'resolution':[960,960],'vertical_fov_degrees':35,'distance_m':distances,'switch_pixels':[None,500,200,80],'bounds_diameter_m':diameter,'views_degrees':list(range(0,360,45)),'reference':'accepted unreduced LOD0 at each same camera','thresholds':{'min_binary_iou':.995,'min_object_roi_ssim':.98},'renderer':'Workbench textured studio, 32 sample alpha'},indent=2))

def triangles(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
def render_set(ob,step,level):
    dest=R/f'step_{step:02}/lod{level}';dest.mkdir(exist_ok=True,parents=True)
    tmp=ob.copy();tmp.data=ob.data.copy();scene.collection.objects.link(tmp);ob.hide_render=True
    head=tmp.data.attributes['head'];uv=tmp.data.uv_layers['UVMap'];huv=tmp.data.uv_layers['HeadUV']
    for face in tmp.data.polygons:
        if head.data[face.index].value:
            for li in face.loop_indices:uv.data[li].uv=huv.data[li].uv
    tmp.data.uv_layers.active=uv
    for k in range(8):
        ang=k*math.pi/4;target=Vector((0,.15,.9));cam.location=target+Vector((math.sin(ang),-math.cos(ang),0))*distances[level]
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/f'{k}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(tmp,do_unlink=True);ob.hide_render=False
    if step==0:return {'min_iou':1.,'min_ssim':1.,'pass':True}
    subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_metrics.py'),str(dest),str(R/f'step_00/lod{level}')],check=True)
    return json.loads((dest/'metrics.json').read_text())

def check_rigid(ob):
    names=[]
    for v in ob.data.vertices:
        weights=[(ob.vertex_groups[w.group].name,w.weight)for w in v.groups if ob.vertex_groups[w.group].name in bones and w.weight>1e-7]
        assert len(weights)==1 and abs(weights[0][1]-1)<1e-5,weights
        names.append(weights[0][0])
    assert all(names[e.vertices[0]]==names[e.vertices[1]]for e in ob.data.edges)


# Lock only geometry responsible for a measured visual loss, then retry the same triangle target.
# This retains the strict image thresholds without freezing broad pixel-wide bands at far distances.
prototype=body;prototype.name='AcceptedPrototype';prototype.hide_render=True
faces=[tuple(f.vertices)for f in prototype.data.polygons]
original_tree=BVHTree.FromPolygons([tuple(v)for v in coords],faces)
locked=set();curve=[];last_count=triangles(prototype);chosen=None
prototype.hide_render=False
render_set(prototype,0,LEVEL);prototype.hide_render=True
for step in range(1,28):
    target=round(last_count*.9);best_loss=None;stagnant=0;accepted=False
    for trial in range(16):
        key=step*100+trial
        current=prototype.copy();current.data=prototype.data.copy();scene.collection.objects.link(current);current.name='Body';current.hide_render=False
        if locked:current.vertex_groups['ReductionAllowed'].add(sorted(locked),0.,'REPLACE')
        bpy.ops.object.select_all(action='DESELECT');current.select_set(True);bpy.context.view_layer.objects.active=current
        mod=current.modifiers.new('AdaptiveCollapse','DECIMATE');mod.ratio=target/triangles(prototype);mod.use_collapse_triangulate=True
        mod.vertex_group='ReductionAllowed';mod.vertex_group_factor=.000001
        bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name)
        normal=current.modifiers.new('AcceptedNormals','DATA_TRANSFER');normal.object=normal_source
        normal.use_loop_data=True;normal.data_types_loops={'CUSTOM_NORMAL'};normal.loop_mapping='POLYINTERP_NEAREST'
        bpy.ops.object.modifier_move_up(modifier=normal.name);bpy.ops.object.modifier_apply(modifier=normal.name)
        check_rigid(current)
        metric=render_set(current,key,LEVEL)
        row={'step':step,'trial':trial,'target':target,'triangles':triangles(current),'locked_vertices':len(locked),'metrics':metric,'rigid_weight_gate':'pass','render':str((R/f'step_{key:02}/lod{LEVEL}').relative_to(P))}
        curve.append(row)
        if metric['pass'] and triangles(current)<last_count:
            dest=W/f'step_{step:02}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));row['blend']=str(dest.relative_to(P));chosen=dict(row);chosen['protected_indices']=sorted(locked);last_count=triangles(current);accepted=True
        (R/'curve.json').write_text(json.dumps({'level':LEVEL,'curve':curve,'selected':chosen},indent=2)+'\n')
        print('ADAPTIVE_STEP',LEVEL,step,trial,row['triangles'],metric['min_iou'],metric['min_ssim'],metric['pass'],len(locked),flush=True)
        if accepted:
            bpy.data.objects.remove(current,do_unlink=True);break
        if triangles(current)>=last_count:
            bpy.data.objects.remove(current,do_unlink=True);break
        faulty=json.loads((R/f'step_{key:02}/lod{LEVEL}/bad_pixels.json').read_text())
        ev=current.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();candidate_coords=[tuple(current.matrix_world@v.co)for v in posed.vertices];ev.to_mesh_clear()
        candidate_tree=BVHTree.FromPolygons(candidate_coords,[tuple(f.vertices)for f in current.data.polygons])
        previous=len(locked)
        for view,pixels in enumerate(faulty):
            angle=view*math.pi/4;target_point=Vector((0,.15,.9));eye=target_point+Vector((math.sin(angle),-math.cos(angle),0))*distances[LEVEL]
            forward=(target_point-eye).normalized();right=forward.cross(Vector((0,0,1)))
            for x,y in pixels:
                ray=(forward+right*((x+.5-480)/focal)+Vector((0,0,1))*((480-y-.5)/focal)).normalized()
                loc,norm,index,dist=original_tree.ray_cast(eye,ray)
                if loc is None:
                    loc,norm,index,dist=candidate_tree.ray_cast(eye,ray)
                    if loc is not None:loc,norm,index,dist=original_tree.find_nearest(loc)
                if index is not None:
                    hit_vertices=set(faces[index])
                    locked.update(hit_vertices)
                for ox,oy in [(-.4,-.4),(.4,-.4),(-.4,.4),(.4,.4),(-.7,0),(.7,0),(0,-.7),(0,.7)]:
                    subray=(forward+right*((x+.5+ox-480)/focal)+Vector((0,0,1))*((480-y-.5-oy)/focal)).normalized()
                    loc,norm,index,dist=original_tree.ray_cast(eye,subray)
                    if loc is None:
                        loc,norm,index,dist=candidate_tree.ray_cast(eye,subray)
                        if loc is not None:loc,norm,index,dist=original_tree.find_nearest(loc)
                    if loc is not None and index is not None:locked.update(faces[index])
        loss=max(0,.995-metric['min_iou'])+max(0,.98-metric['min_ssim'])
        stagnant=stagnant+1 if best_loss is not None and loss>=best_loss else 0
        best_loss=loss if best_loss is None else min(loss,best_loss)
        bpy.data.objects.remove(current,do_unlink=True)
        if len(locked)==previous:break
    if not accepted:break
assert chosen is not None
print('ADAPTIVE_SELECTED',LEVEL,chosen['triangles'],chosen['blend'],flush=True)
