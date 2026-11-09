"""Measure the complete equipped actor at the prescribed pixel heights and native tier materials."""
import bpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import reduce_natf as red
R=P/'review/equipped_reduction';W=P/'work/equipped_reduction';R.mkdir(exist_ok=True);W.mkdir(exist_ok=True);red.R=R
allrows=[]
for folder in ['reduction_v9','reduction_fit','reduction_props']:
 for row in json.loads((P/f'review/{folder}/curve.json').read_text()):row['method']=folder;allrows.append(row)
def choose(part,level,ratio,folder='reduction_props'):
 return next(r for r in reversed(allrows)if r['part']==part and r['lod']==level and r['ratio']==ratio and r['method']==folder)
def setup(rows):
 if rows is None:
  body,rig=red.reset('Body');maps={n:[{'name':m.name,'maps':{'basecolor':f'textures/{red.TAGS[m.name]}_basecolor_1k.png','region_mask':f'textures/{red.TAGS[m.name]}_region_mask.png'}}for m in bpy.data.objects[n].data.materials]for n in ['Body','ForearmBlade','LeafShield']}
 else:
  bpy.ops.wm.open_mainfile(filepath=str(P/rows['Body']['blend']));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];maps={n:row['maps']for n,row in rows.items()}
  for n in ['ForearmBlade','LeafShield']:
   with bpy.data.libraries.load(str(P/rows[n]['blend']))as(src,dst):dst.meshes=[n]
   assert len(dst.meshes)==1 and dst.meshes[0]is not None,n
   ob=bpy.data.objects[n];ob.data=dst.meshes[0];ob.vertex_groups.clear();ob.vertex_groups.new(name=n).add(list(range(len(ob.data.vertices))),1,'REPLACE')
 rig.animation_data.action=None
 if rows is not None:
  for a in list(bpy.data.actions):bpy.data.actions.remove(a)
  roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
  with bpy.data.libraries.load(str(P/'work/accepted_master.blend'))as(src,dst):dst.actions=roles
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();return body,rig,maps
def trial(level,label,rows):
 body,rig,maps=setup(rows);tag=f'lod{level}_{label}';blend=W/f'{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));red.render(body,rig,level,tag,maps,whole=True)
 code="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from reduction_metrics import compare;root=Path(sys.argv[2]);a,b=sys.argv[3:5];v=[compare(root/f'{a}_{t}_{i}.png',root/f'{b}_{t}_{i}.png')for t in ['natf_a','natf_b','natf_c']for i in range(8)];print(json.dumps({'views':v,'min_iou':min(r['iou']for r in v),'pooled_iou':sum(r['intersection_pixels']for r in v)/sum(r['union_pixels']for r in v),'min_ssim':min(r['ssim']for r in v)}))"
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3','-c',code,str(P/'scripts'),str(R),f'lod{level}_source',tag],text=True));passed=(metrics['min_iou']>=.99 and metrics['min_ssim']>=.95)if level==0 else metrics['pooled_iou']>=.97
 row={'level':level,'label':label,'parts':rows,'blend':str(blend.relative_to(P)),'triangles':{n:red.count(bpy.data.objects[n])for n in maps},'actor_height_px':[700,550,220,88][level],**metrics,'pass':passed};file=R/'curve.json';curve=json.loads(file.read_text())if file.exists()else[];curve.append(row);file.write_text(json.dumps(curve,indent=2));print('EQUIPPED',level,label,row['triangles'],metrics['min_iou'],metrics['pooled_iou'],metrics['min_ssim'],passed,flush=True);return row
if __name__=='__main__':
 for level in range(4):trial(level,'source',None)
 for ratio in [.78,.75,.7,.55]:
  rows={'Body':choose('Body',0,ratio,'reduction_v9'),'ForearmBlade':choose('ForearmBlade',0,.75),'LeafShield':choose('LeafShield',0,.6)};trial(0,f'body{ratio}',rows)
 for ratio in [.4,.32]:
  rows={'Body':choose('Body',1,ratio,'reduction_v9'),'ForearmBlade':choose('ForearmBlade',1,.25),'LeafShield':choose('LeafShield',1,.25)};trial(1,f'body{ratio}',rows)
 for ratio,folder in [(.21,'reduction_props'),(.18,'reduction_fit'),(.14,'reduction_v9')]:
  rows={'Body':choose('Body',2,ratio,folder),'ForearmBlade':choose('ForearmBlade',2,.18),'LeafShield':choose('LeafShield',2,.18)};trial(2,f'body{ratio}',rows)
 for ratio,folder in [(.1,'reduction_props'),(.075,'reduction_fit'),(.06,'reduction_fit')]:
  rows={'Body':choose('Body',3,ratio,folder),'ForearmBlade':choose('ForearmBlade',3,.08),'LeafShield':choose('LeafShield',2,.12)};trial(3,f'body{ratio}',rows)
