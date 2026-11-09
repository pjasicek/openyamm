import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_rebake as red
row=json.loads((red.R/'selection.json').read_text());high,rig=red.reset();red.component_labels(high)
with bpy.data.libraries.load(str(P/row['blend']),link=False)as(src,dst):dst.objects=['Jackalman']
low=dst.objects[0];bpy.context.collection.objects.link(low)
for mod in low.modifiers:
 if mod.type=='ARMATURE':mod.object=rig
for obj in list(bpy.data.objects):
 if obj not in [high,low,rig]:bpy.data.objects.remove(obj,do_unlink=True)
body=red.rebake(high,low,rig,P/row['maps']);red.render(body,rig,'step03',P/row['maps'])
metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(red.R),'reference','step03'],text=True));assert metrics['min_iou']>=.99 and metrics['min_ssim']>=.95,metrics
for mat,tag in zip(body.data.materials,red.TAGS):mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node.image=bpy.data.images.load(str(P/row['maps']/f'{tag}_basecolor.png'),check_existing=True)
red.rest(rig);row['blend']='work/round2/reduction/step03_padded.blend';bpy.ops.wm.save_as_mainfile(filepath=str(P/row['blend']));row.update(metrics);row['bake_margin_px']=16;(red.R/'selection.json').write_text(json.dumps(row,indent=2));curve=json.loads((red.R/'curve.json').read_text());curve=[row if r['step']==3 else r for r in curve];(red.R/'curve.json').write_text(json.dumps(curve,indent=2));print('PADDED REBAKE PASS',metrics['min_ssim'],flush=True)
