"""Final animation contact, loop and skin audit from the retained textured master."""
import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/('work/uv_master.blend' if '--uv' in sys.argv else 'work/m552_textured_master.blend')))
rig=bpy.data.objects['Thunderbird_Rig'];mesh=bpy.data.objects['Thunderbird'];sc=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
labels=mesh.data.attributes['anatomy_part'].data;body=np.array([v.value==0 for v in labels]);report={};death=None
for n,spec in json.loads((P/'work/clip_manifest.json').read_text()).items():
 rig.animation_data.action=bpy.data.actions[n];samples=[]
 for f in np.arange(0,spec['frames']+.01,.125):
  sc.frame_set(int(f),subframe=float(f%1));co=np.array([tuple(v.co) for v in mesh.evaluated_get(dg).data.vertices]);assert np.isfinite(co).all();samples.append(co)
 a=np.array(samples);gap=float(np.linalg.norm(a[0]-a[-1],axis=1).max())
 if spec['loop']:assert gap<1e-5
 if n in ('Death','Dead'):assert a[:,:,2].min()>-.002
 if n=='Death':death=a[-1]
 if n=='Dead':assert np.max(abs(a[0]-death))<.001 and gap<1e-5 and a[0,body,2].min()<.02
 report[n]=dict(sample_count=len(a),minimum=a.min((0,1)).tolist(),maximum=a.max((0,1)).tolist(),endpoint_delta=gap,body_floor_final=float(a[-1,body,2].min()))
scale=json.loads((P/'work/scale.json').read_text())['scale'];report['flight_top_units']=report['Fly']['maximum'][2]*scale
assert report['flight_top_units']<200
(P/'review/final_deformation_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL DEFORMATION',report)
