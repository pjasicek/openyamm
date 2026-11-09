"""Publish the measured reduction boundary and paired review sheets."""
import json,csv,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'work/python'));import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=P/'review/rebake';out=P/'review/reduction'
def read(n):return json.loads((R/(n+'.json')).read_text())
rows=[]
for part,base,selected,failed in [('body',12987,'near70final','near65final'),('bow',2236,'bow80_baked','bow70_boundary_geometry')]:
 rows.append(dict(part=part,step='unreduced',triangles=base,min_iou=1.,min_ssim=1.,passed=True))
 for tag,status in [(selected,'selected'),(failed,'next lower rejected')]:
  m=read(tag+'_metrics')[part];count=read('near70final_counts')['body']if tag=='near70final'else read('near65final_counts')['body']if tag=='near65final'else 1788 if tag=='bow80_baked'else 1564
  rows.append(dict(part=part,step=status,triangles=count,**{k:m[k]for k in ['min_iou','min_ssim','passed']}))
m=read('near65final_metrics')['bow'];rows.append(dict(part='bow',step='earlier passing step',triangles=2012,**{k:m[k]for k in ['min_iou','min_ssim','passed']}))
for row in rows:
 row['rig_gates']='PASS: selected runtime, all nine clips' if row['step']=='selected' else 'not rerun for this image comparison'
(out/'curve.json').write_text(json.dumps(rows,indent=2))
with (out/'curve.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
for a,part in zip(ax,['body','bow']):
 vals=sorted([v for v in rows if v['part']==part],key=lambda r:r['triangles'])
 for metric,color in [('min_iou','tab:blue'),('min_ssim','tab:orange')]:a.plot([v['triangles']for v in vals],[v[metric]for v in vals],'o-',label=metric,color=color)
 a.axhline(.99,linestyle=':',color='tab:blue');a.axhline(.95,linestyle=':',color='tab:orange');a.set(title=part.title()+' — eight views at 700 px',xlabel='Triangles',ylabel='Minimum score',ylim=(.91,1.006));a.grid(alpha=.2);a.legend()
fig.tight_layout();fig.savefig(out/'curve.png',dpi=160);plt.close(fig)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
def sheet(name,pairs,size=(440,440)):
 w,h=size;im=Image.new('RGB',(w*2,50+len(pairs)*(h+35)),(35,38,41));d=ImageDraw.Draw(im);d.text((12,12),'Unreduced reference / selected rebake',font=font,fill='white')
 for row,(label,a,b)in enumerate(pairs):
  y=50+row*(h+35);d.text((12,y),label,font=font,fill='white')
  for col,path in enumerate([a,b]):
   src=Image.open(path).convert('RGBA');src.thumbnail((w,h));bg=Image.new('RGB',(w,h),(60,62,65));bg.paste(src,((w-src.width)//2,(h-src.height)//2),src);im.paste(bg,(col*w,y+30))
 im.save(out/name,quality=93)
sheet('near_tiers.jpg',[(f'Tier {tier.upper()} — source height 700 px',R/f'reference_lzd_{tier}_body_l0_0.png',R/f'near70final_lzd_{tier}_body_l0_0.png')for tier in'abc'])
sheet('bow_comparison.jpg',[('Bow — source actor height 700 px',R/'reference_pbr_bow_l0_0.png',R/'bow80_baked_bow_l0_0.png')],(768,768))
sheet('lod_comparison.jpg',[(f'LOD {level} — actor {px} px; assembled body + bow',R/f"{'reference64'if level==3 else'reference_pbr'}_actor_l{level}_0.png",R/f'runtime_lod{level}_actor_l{level}_0.png')for level,px in [(1,550),(2,220),(3,88)]],(768,768))
tiers=read('actual_tiers');lods={str(i):read(f'runtime_lod{i}_metrics')['actor']for i in [1,2,3]}
(out/'README.md').write_text("""# Round 3 reduction evidence

Current selection: body 9,858 and bow 1,788 triangles at LOD0. Counts are separate from the skinned string/arrow, which remain in the body.
[Curve](curve.png), [CSV](curve.csv), [all tier pairs](near_tiers.jpg), [bow pair](bow_comparison.jpg), [distance pairs](lod_comparison.jpg).

Body protected face, fingers, collar, deformation loops, boundaries and contact. The next 9,545-triangle authored candidate fails textured SSIM (0.92868); the selected 9,858 passes all three actual tier palettes (minimum SSIM 0.96079, minimum IoU 0.994625). A smaller earlier trial passed scalar metrics but damaged the collar and was rejected visually.
Bow 2,012 passed, 1,788 passes (minimum IoU 0.996461, SSIM 0.992048); 1,564 fails silhouette (0.986866). Final body geometry/UV/named weights were preserved while substituting only the smaller bow.

This already-running round retains per-LOD rebakes under Batch Cost controls item 4 (no retroactive rules). The later shared-map/16-pixel-margin migration is not claimed. Each selected level rebakes base colour, region mask, ORM and +Y tangent normals. Near body/head/bow maps are 2048/1024/1024; source normal strength 0.65 is included in the bake and exported scale is 1.0. Head/body merge uses existing atlas tooling. Only cloth is recoloured; skin and metal keep their source colours.

Near comparisons use eight 700-pixel actor views and score body and bow separately. Distance comparisons score the **assembled body + bow actor**, at 550/220/88 pixels, with pooled silhouette IoU >= 0.97. Isolated far bow overlap is about 0.916 because it is mostly subpixel; that diagnostic is retained rather than described as a standalone pass. The initial 16-sample far assembled trial scored 0.969931; paired reference/candidate at 64 samples scored 0.970581 before export. The final runtime-import comparisons below supersede those authored-mesh scores.

Export triangulation removes 7/21/30 triangles from the authored lower body counts (5238/2206/750 -> 5231/2185/720). Runtime imports, all-clip rig checks and silhouette renders validate the exact written topology; the selected receipt retains both counts. The GLB chain strictly decreases and stays below the previously installed chain. Lower levels use the same base animation bytes and matching bind matrices.

All exploratory trials remain under ../rebake/; they are not runtime inputs. The final input list is ../rebake/final_selection.json. Recovery timing was subsequently slowed over frames 23–25; Standing and these visual comparisons are unchanged.
"""+'\nFinal runtime pooled IoU:\n\n'+'\n'.join(f"- LOD {i}: {x['pooled_iou']:.9f}"for i,x in lods.items())+'\n')
print('REDUCTION_REVIEW_PUBLISHED')
