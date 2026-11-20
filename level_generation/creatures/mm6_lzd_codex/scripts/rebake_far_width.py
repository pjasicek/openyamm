import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
from rebake_textures import bake
from round3_candidate_gates import check
selected=None
for factor in [.999,.998,1.001]:
 tag='far_width_'+str(factor).replace('.','_');bpy.ops.wm.open_mainfile(filepath=str(P/'work/rebake/lod3_selected.blend'));body=bpy.data.objects['Body'];pv=[v.value for v in body.data.attributes['piece'].data]
 for v in body.data.vertices:
  if pv[v.index]<201:v.co.x*=factor;v.co.y*=factor
 path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,tag,3,parts=['actor']);r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,'3','8','actor'],text=True));(P/f'review/rebake/{tag}_actor_metrics.json').write_text(json.dumps(r,indent=2));print('FAR_WIDTH',factor,r['actor']['pooled_iou'],flush=True)
 if r['actor']['passed']:
  gates=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(gates,indent=2));print('FAR_WIDTH_GATES',factor,gates['passed'],gates['motion']['issues'],flush=True)
  if gates['passed']:selected=(tag,path);break
assert selected,'No final distance-width candidate passed'
tag,path=selected;bake(path,tag,3)
(P/'review/rebake/final_selection.json').write_text(json.dumps({'0':{'tag':'near70final'},'1':{'tag':'lod1_selected'},'2':{'tag':'lod2_selected'},'3':{'tag':tag}},indent=2))
