"""Replace only Attack in the retained editable/export checkpoints."""
from pathlib import Path
import bpy,runpy,sys,json,shutil,hashlib
P=Path(__file__).resolve().parents[1];W=P/'work/attack_revision_1'
def signature(a):
 return [(fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]) for l in a.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
s=P/'scripts/export_glb.py';sys.argv=[str(s),'--',str(W/'candidate.blend'),str(W/'attack_source.glb')]
runpy.run_path(str(s),run_name='__main__')
records=[]
for path in [P/'work/textured_uv.blend',P/'work/rig_final.blend',P/'work/runtime_textured.blend',P/'export/raven_master.blend',*[P/f'work/portable_{t}.blend' for t in 'abc']]:
 backup=W/'checkpoints'/path.name;backup.parent.mkdir(exist_ok=True)
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));rig=bpy.data.objects['Rig']
 before={a.name:signature(a) for a in bpy.data.actions if a.name!='Attack'}
 with bpy.data.libraries.load(str(W/'candidate.blend'),link=False) as (src,dst):dst.actions=['Attack']
 new=dst.actions[0];old=bpy.data.actions['Attack'];was_active=rig.animation_data.action==old
 bpy.data.actions.remove(old);new.name='Attack';new.use_fake_user=True
 if was_active:
  rig.animation_data.action=new;rig.animation_data.action_slot=new.slots[0]
 assert {a.name:signature(a) for a in bpy.data.actions if a.name!='Attack'}==before
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 records.append({'path':str(path.relative_to(P)),'other_actions_unchanged':True})
(W/'checkpoint_preservation.json').write_text(json.dumps(records,indent=2)+'\n')
