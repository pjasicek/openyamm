"""Review skeletal-only Mixamo run on a simple joint-head mannequin; no runtime asset."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import common
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo/Standard Run.fbx').resolve()))
scene=bpy.context.scene
src=next(o for o in bpy.data.objects if o.type=='ARMATURE')
act=src.animation_data.action
assert scene.render.fps==30
pre=next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
pairs=[('Hips','Spine',.07),('Spine','Spine1',.08),('Spine1','Spine2',.10),('Spine2','Neck',.12),('Neck','Head',.05)]
for s in ('Left','Right'):
    pairs += [(s+'Shoulder',s+'Arm',.05),(s+'Arm',s+'ForeArm',.05),(s+'ForeArm',s+'Hand',.04),('Hips',s+'UpLeg',.07),(s+'UpLeg',s+'Leg',.07),(s+'Leg',s+'Foot',.05),(s+'Foot',s+'ToeBase',.05)]
parts=[]
for a,b,r in pairs:
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=1)
    parts.append(bpy.context.object)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.12)
head=bpy.context.object
common.workbench_clay(scene)
out=P/'review/source_selected'
rows=[];numbers=[]
for view in ('front','left','three_quarter'):
    row=[]
    for i in range(6):
        f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/5
        scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
        def point(n):return src.matrix_world@src.pose.bones[pre+n].head
        for (a,b,r),o in zip(pairs,parts):
            va,vb=point(a),point(b)
            o.location=(va+vb)/2;o.scale.z=(vb-va).length
            o.rotation_euler=(vb-va).to_track_quat('Z','Y').to_euler()
        head.location=point('Head')+Vector((0,0,.06))
        pth=common.render_views(str(out/f'StandardRun_{i}'),1.0,2.5,views=(view,),resolution=(240,320),target=(point('Hips').x,point('Hips').y))[0]
        row.append([pth,f'Standard Run {f:.1f} {view}'])
        if view=='front':numbers.append({'frame':f,'hips':list(point('Hips')),'feet':[list(point(s+'Foot')) for s in ('Left','Right')]})
    rows.append(row)
(out/'mixamo_frames.json').write_text(json.dumps(rows,indent=2))
(P/'work/mixamo_source_review.json').write_text(json.dumps({'source':'anim_library/mixamo/Standard Run.fbx','fps':30,'range':list(act.frame_range),'representation':'joint-head mannequin; source FBX has no mesh','samples':numbers},indent=2))
