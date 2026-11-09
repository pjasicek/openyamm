"""Assemble final clip and reduction evidence without changing the assets."""
import json,csv,io,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
info=json.loads((P/'export/export_info.json').read_text())['0'];S=R/'sheets';S.mkdir(exist_ok=True)
def paste(canvas,path,box):
 image=Image.open(path).convert('RGBA')
 if image.width==image.height and box[2]<box[3]:
  width=round(image.height*box[2]/box[3]);bbox=image.getbbox();x=max(0,min(image.width-width,round((bbox[0]+bbox[2]-width)/2)));image=image.crop((x,0,x+width,image.height))
 image.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS);canvas.paste(image,(box[0]+(box[2]-image.width)//2,box[1]+(box[3]-image.height)//2),image)
for role,duration in info['durations'].items():
 frames=[(f'{i:02}',float(t))for i,t in enumerate(np.linspace(0,duration,6))]
 if role=='Attack':frames.insert(2,('impact',.416666666667))
 cellw,cellh=240,380;out=Image.new('RGB',(len(frames)*cellw,3*cellh+50),(32,36,42));draw=ImageDraw.Draw(out);draw.text((12,10),f'{role} — front / left / three-quarter; seconds',font=font,fill='white')
 for row,view in enumerate(['front','left','three_quarter']):
  for col,(key,t)in enumerate(frames):
   path=R/'final_clips'/role/f'{key}_{view}.png'if key!='impact'else R/'final_comparison/lod0/selected'/f'mfp_a_Attack_{[0,2,1][row]}.png';assert path.exists();paste(out,path,(col*cellw,50+row*cellh,cellw,350));draw.text((col*cellw+8,50+row*cellh+350),f'{t:.3f}s'+('  impact'if key=='impact'else''),font=small,fill='white')
 out.save(S/f'{role}.png')
# Full-size paired images preserve the actual 700/550/220/88-pixel projection used in the metrics.
C=R/'comparisons';C.mkdir(exist_ok=True)
for level in range(4):
 out=Image.new('RGB',(1640,1684),(25,29,34));draw=ImageDraw.Draw(out);draw.text((10,8),f'LOD{level}: reference (left), selected (right)',font=font,fill='white')
 for row,role in enumerate(['Standing','Attack']):
  for col,kind in enumerate(['reference','selected']):paste(out,R/f'final_comparison/lod{level}/{kind}/mfp_a_{role}_1.png',(820*col,44+820*row,820,820))
 out.save(C/f'lod{level}_pairs.png')
html="""<!doctype html><meta charset="utf-8"><title>PeasantF3 reduction comparisons</title><style>body{background:#191d22;color:#eee;font:16px system-ui;margin:20px}select{font:inherit;margin:8px;padding:8px}main{display:flex;gap:12px}figure{margin:0;flex:1}img{width:100%;background:#191d22}a{color:#9bd0ff}</style><h1>PeasantF3 matched reduction renders</h1><p>Original render size is 820 × 820. LOD0 reference is the unreduced mesh; other references are LOD0. Both use the final materials and pose.</p><label>LOD<select id="lod"><option>0</option><option>1</option><option>2</option><option>3</option></select></label><label>Tier<select id="tier"><option value="mfp_a">Cutpurse</option><option value="mfp_b">Bounty Hunter</option><option value="mfp_c">Assassin</option></select></label><label>Pose<select id="pose"><option>Standing</option><option>Attack</option></select></label><label>View<select id="view"><option>0</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option><option>6</option><option>7</option></select></label><main><figure><figcaption>Reference</figcaption><a id="refLink"><img id="ref" alt="Reference"></a></figure><figure><figcaption>Selected</figcaption><a id="selLink"><img id="sel" alt="Selected LOD"></a></figure></main><script>const get=id=>document.getElementById(id);function update(){const root='../final_comparison/lod'+get('lod').value+'/',name=get('tier').value+'_'+get('pose').value+'_'+get('view').value+'.png';for(const [id,kind]of [['ref','reference'],['sel','selected']]){get(id).src=root+kind+'/'+name;get(id+'Link').href=get(id).src;}}for(const s of document.querySelectorAll('select'))s.onchange=update;update();</script>"""
(C/'index.html').write_text(html)
rows=[]
for f in sorted(R.glob('**/*curve.json')):
 if 'workbench'in str(f):continue
 d=json.loads(f.read_text());steps=d if isinstance(d,list)else d.get('steps',[]);level=int(f.name[3]);
 for step in steps:
  v=step.get('visual',{});g=step.get('rig_gate')or{};passed=(v.get('min_iou',0)>=.99 and v.get('min_ssim',0)>=.95)if level==0 else v.get('pooled_iou',0)>=.97
  rows.append({'curve':str(f.relative_to(R)),'step':step.get('step'),'triangles':step.get('triangles'),'min_iou':v.get('min_iou'),'min_ssim':v.get('min_ssim'),'pooled_iou':v.get('pooled_iou'),'visual_pass':passed,'rig_pass':g.get('pass'),'rig_failures':', '.join(g.get('failures',[]))})
with (R/'reduction_curve.csv').open('w')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
lines=['# Reduction curve','', 'Historical trials retain their original motion/material revision. Final measurements are in `final_comparison/scores.json`. Lower LODs use pooled IoU ≥ 0.97; SSIM is recorded, with its 0.95 threshold applied only at LOD0. Counts here are Blender triangles before the exporter removes zero-area faces.', '', '| Curve / step | Triangles | Min IoU | Min SSIM | Pooled IoU | Visual | Rig |', '|---|---:|---:|---:|---:|---|---|']
for x in rows:lines.append(f"| {x['curve']} / {x['step']} | {x['triangles']} | {x['min_iou']:.6f} | {x['min_ssim']:.6f} | {x['pooled_iou']:.6f} | {'pass'if x['visual_pass']else'fail'} | {x['rig_failures']or('pass'if x['rig_pass']else'not run')} |")
lines+=['','LOD0 retains step 3 of the soft protection curve. Step 4 failed the Hit cloth gate (2.707 mm); step 5 failed SSIM (0.935024). The final LOD3 uses the 0.13 contour-protected candidate: the smaller 0.125 trial scored 0.969902 pooled IoU and was rejected without rounding. The final LOD3 is 12.27% of LOD0 total triangles; silhouette requirements take precedence over the approximate 10% guidance. No previous installed PeasantF3 3D counts existed.','', '[Interactive matched pairs](comparisons/index.html) · [LOD0 full-size pairs](comparisons/lod0_pairs.png) · [LOD1](comparisons/lod1_pairs.png) · [LOD2](comparisons/lod2_pairs.png) · [LOD3](comparisons/lod3_pairs.png)']
(R/'REDUCTION.md').write_text('\n'.join(lines)+'\n')
print('ASSEMBLED',len(info['durations']),'clip sheets;',len(rows),'reduction trials')
