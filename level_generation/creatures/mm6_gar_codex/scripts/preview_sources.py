"""Preview stored source motion on its own library mannequin and record joint extremes."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
out=P/'review/source_motion'; out.mkdir(exist_ok=True)
rows=[]; reports=[]
for role,fn in [('Flight','Floating.fbx'),('Attack','Mutant Swiping.fbx'),('Hit','Hit Reaction.fbx')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo/characters/warrok_w_kurniawan.fbx').resolve()))
    target=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    target.animation_data_clear()
    meshes=[o for o in bpy.data.objects if o.type=='MESH']
    for o in meshes: o.color=(0.54,0.57,0.59,1)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo',fn).resolve()))
    source=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE')
    act=source.animation_data.action
    f0,f1=map(int,act.frame_range); scene=bpy.context.scene; scene.render.fps=30
    names=[b.name for b in target.data.bones if b.name in source.data.bones]
    S=source.matrix_world.copy(); T=target.matrix_world.copy(); TI=T.inverted()
    offsets={n:(S@source.data.bones[n].matrix_local).to_3x3().normalized().inverted()@(T@target.data.bones[n].matrix_local).to_3x3().normalized() for n in names}
    scene.frame_set(f0)
    s0=(S@source.pose.bones['mixamorig:Hips'].matrix).translation.copy()
    tr=(T@target.data.bones['mixamorig:Hips'].matrix_local).translation.copy()
    swings={n:[] for n in names if any(k in n for k in ['Arm','Hand','Spine','Neck','Head']) and not any(k in n for k in ['Thumb','Index','Middle','Ring','Pinky','End'])}
    for f in range(f0,f1+1):
        scene.frame_set(f)
        for n in swings:
            q=source.pose.bones[n].matrix_basis.to_quaternion()
            swings[n].append(math.degrees(q.angle))
    extremes={n:{'max_local_rotation_deg':round(max(v),2),'frame':f0+v.index(max(v))} for n,v in swings.items()}
    reports.append({'role':role,'file':'anim_library/mixamo/'+fn,'fps':30,'frames':[f0,f1],'duration':(f1-f0)/30,'extremes':extremes})
    common.workbench_clay(scene)
    scene.display.shading.color_type='OBJECT'
    scene.world=bpy.data.worlds.new('PreviewWorld')
    scene.world.color=(0.8,0.8,0.8)
    scene.render.image_settings.file_format='PNG'
    for view in ['front','left','three_quarter']:
        row=[]
        for i in range(7):
            f=f0+(f1-f0)*i/6; scene.frame_set(int(f),subframe=f-int(f))
            for n in names:
                pb=target.pose.bones[n]
                m=((S@source.pose.bones[n].matrix).to_3x3().normalized()@offsets[n]).to_4x4()@Matrix.Diagonal((*T.to_scale(),1.0))
                m.translation=tr+((S@source.pose.bones[n].matrix).translation-s0) if n=='mixamorig:Hips' else T@pb.head
                pb.matrix=TI@m; bpy.context.view_layer.update()
            lo,hi=common.world_bounds(meshes)
            assert all(math.isfinite(v) for v in lo) and hi.z-lo.z<5, ('Invalid preview pose',tuple(lo),tuple(hi))
            targetxy=((lo.x+hi.x)/2,(lo.y+hi.y)/2)
            path=common.render_views(str(out/f'{role}_{view}_{i}'),(lo.z+hi.z)/2,max(2.8,hi.z-lo.z+0.3),views=(view,),resolution=(240,330),target=targetxy)[0]
            row.append([path,f'{role} {view} {(f-f0)/30:.2f}s'])
        rows.append(row)
(out/'frames.json').write_text(json.dumps(rows))
(P/'work/source_rom.json').write_text(json.dumps(reports,indent=2))
print('SOURCE_PREVIEW_COMPLETE',[(r['role'],r['duration']) for r in reports])
