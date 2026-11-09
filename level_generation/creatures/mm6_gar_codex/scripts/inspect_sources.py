import bpy, json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
report=[]
for fn in ['characters/warrok_w_kurniawan.fbx','Floating.fbx','Mutant Swiping.fbx','Hit Reaction.fbx','Hit Reaction (2).fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo',fn).resolve()))
    arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    assert len(arm.data.bones)>20
    report.append({'file':fn,'fps':bpy.context.scene.render.fps,'objects':[(o.name,o.type,len(o.data.vertices) if o.type=='MESH' else 0) for o in bpy.data.objects], 'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions], 'matrix':list(map(list,arm.matrix_world)), 'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in arm.data.bones}})
(P/'work/source_inspection.json').write_text(json.dumps(report,indent=2))
print('SOURCE_SUMMARY',[(r['file'],r['fps'],r['objects'],r['actions']) for r in report])
