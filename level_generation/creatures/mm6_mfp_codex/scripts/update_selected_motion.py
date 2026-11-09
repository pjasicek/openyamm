import bpy,json,sys,os,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from gates_summary import summarize
R=P/'review/reduction_soft';selection=json.loads((R/'selection.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'));rest={b.name:np.array(b.matrix_local)for b in bpy.data.objects['Rig'].data.bones};roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];curve=json.loads((R/'lod0_curve.json').read_text());accepted=None
for row in curve['steps']:
 if not row['pass']:continue
 source=P/row['blend'];bpy.ops.wm.open_mainfile(filepath=str(source));r=bpy.data.objects['Rig'];assert max(abs(rest[b.name]-np.array(b.matrix_local)).max()for b in r.data.bones)<1e-5;r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/rig_textured.blend'),link=False)as(src,dst):dst.actions=list(roles)
 for a in dst.actions:a.use_fake_user=True
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);path=source.with_name(source.stem+'_finalmotion.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path));report=R/f'lod0_step{row["step"]}_gates.json';os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(report),GATE_RENDER='0');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');gate=summarize(json.loads(report.read_text()));row['rig_gate']=gate;row['final_blend']=str(path.relative_to(P));row['pass']=bool(row['pass']and gate['pass']);print('SELECTED_GATE',row['step'],gate,flush=True)
 if row['pass']:accepted=dict(row,blend=row['final_blend'])
 else:break
assert accepted, 'No reduced LOD0 passes the rig gates';selection['0']=accepted;(R/'selection.json').write_text(json.dumps(selection,indent=2));(R/'lod0_curve.json').write_text(json.dumps(curve,indent=2));(P/'work/reduction_soft/config.json').write_text('{"levels":[1,2,3],"steps":20}')
