import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
bpy.ops.import_scene.fbx(filepath=str(R/'anim_library/mixamo/Standard Run.fbx'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
a=rig.animation_data.action;start,end=a.frame_range;fps=sc.render.fps/sc.render.fps_base
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(R/'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
char=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE')
assert set(b.name for b in rig.data.bones)==set(b.name for b in char.data.bones)
char.animation_data_create();char.animation_data.action=a
if a.slots:char.animation_data.action_slot=a.slots[0]
out=P/'motion/standard_run';out.mkdir(exist_ok=True)
common.workbench_clay(sc)
sc.frame_set(int(start));bpy.context.view_layer.update()
lo,hi=common.world_bounds([o for o in bpy.data.objects if o.type=='MESH'])
height=max(hi.z-lo.z,(hi.x-lo.x)*300/220,(hi.y-lo.y)*300/220)*1.4
for i in range(5):
 f=start+(end-start)*i/4;sc.frame_set(int(f),subframe=f-int(f))
 common.render_views(str(out/f'run_{i}'),(lo.z+hi.z)/2,height,target=((lo.x+hi.x)/2,(lo.y+hi.y)/2),views=('front','left','three_quarter'),resolution=(220,300))
(P/'motion/standard_run.json').write_text(json.dumps({'source':'anim_library/mixamo/Standard Run.fbx','fps':fps,'frame_range':[start,end],'duration':(end-start)/fps},indent=2))
