"""Record the selected assets and measurements without turning an open visual gate into a pass."""
import csv,hashlib,io,json,struct,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review/round3';E=P/'export';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
J=lambda p:json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
selected=J(R/'final_selection.json');before=[15427,7712,2771,903];after=[selected[str(i)]['triangles'] for i in range(4)]
assert all(a>b for a,b in zip(after,after[1:]));assert all(a<=b for a,b in zip(after,before));assert all(after[i]<=after[0]*r for i,r in [(1,.55),(2,.25),(3,.10)])
files=['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb','mm6_figc_portable.glb','mm6_figc_authoring.blend'];art=J(E/'artifacts.json');art.update(revision='review_round_3',files={n:{'bytes':(E/n).stat().st_size,'sha256':sha(E/n)} for n in files},combined_lod_triangles=after,lod_triangles={n:[selected[str(i)]['parts'][part] for i in range(4)] for n,part in [('mm6_figc.glb','Body'),('mm6_figc_axe.glb','Axe'),('mm6_figc_shield.glb','Shield')]},technical_completion=False);save(E/'artifacts.json',art)
# Exact animation accessor comparison is independent of indices, material order, and PNG packing.
def animation_data(path):
 d,b=read_glb(path);curves={}
 for a in d['animations']:
  for c in a['channels']:
   t=c['target'];s=a['samplers'][c['sampler']];curves[(a['name'],d['nodes'][t['node']]['name'],t['path'])]=tuple(accessor_array(d,b,s[k]) for k in ['input','output'])
 return curves
base=animation_data(R/'before/export/mm6_figc_lod0.glb');invariance={}
for i in range(4):
 path=E/'mm6_figc_lod0.glb' if i==0 else R/f'export_lod{i}/mm6_figc_lod0.glb';actual=animation_data(path);assert actual.keys()==base.keys();identical=all(np.array_equal(a,b) for k in base for a,b in zip(base[k],actual[k]));assert identical;invariance[str(i)]={'channels':len(actual),'bit_identical':identical,'raw_glb_sha256':sha(path)}
assert (P/'integration/actors.yml').read_bytes()==(R/'before/integration/actors.yml').read_bytes();save(R/'animation_invariance.json',{'lods':invariance,'actors_sha256':sha(P/'integration/actors.yml'),'actors_changed':False})
for old in (R/'before/textures').iterdir():
 if old.is_file():assert old.read_bytes()==(P/'textures'/old.name).read_bytes(),old.name
ramps=J(P/'textures/figc_ramps.json');new=J(P/'textures/figc_round3_ramps.json')
for i,m in enumerate(new['materials']):assert m['ramps']==ramps['materials'][i%3]['ramps']
textures={}
for f in sorted((P/'textures').glob('round3_lod*/*.png')):
 im=Image.open(f);textures[str(f.relative_to(P))]={'size':list(im.size),'bytes':f.stat().st_size,'sha256':sha(f)}
save(R/'texture_manifest.json',textures)
def storage(folder):
 unique={};total=0;size=0
 for name in files[:3]:
  d,b=read_glb(folder/name);size+=(folder/name).stat().st_size
  for image in d.get('images',[]):
   v=d['bufferViews'][image['bufferView']];start=v.get('byteOffset',0);png=b[start:start+v['byteLength']];im=Image.open(io.BytesIO(png));n=im.width*im.height*4;unique[hashlib.sha256(png).hexdigest()]=n;total+=n
 return {'runtime_glb_bytes':size,'distinct_rgba8_bytes_without_mips':sum(unique.values()),'rgba8_bytes_counting_files_separately':total}
storage_report={'before':storage(R/'before/export'),'after':storage(E),'method':'Embedded PNG dimensions at four bytes/texel; distinct hashes deduplicated. Excludes mips, driver formats and actual engine residency.'};save(R/'storage.json',storage_report)
rows=[]
for i in range(4):
 row=selected[str(i)];gates=J(P/row['gates']);assert len(gates)==8 and sum(v['frames'] for v in gates.values())==682
 for name,g in gates.items():
  assert g['arm_p99']<1.5 and g['finger_max']<4.5 and g['head_mm']<10 and g['minimum_z']>=0,(i,name,g)
  assert max(g[k] for k in ['L_contact_mm','R_contact_mm','Axe_mm','Shield_mm'])<=2
 m=row['metrics'];rows.append({'lod':i,'before':before[i],'after':after[i],'body':row['parts']['Body'],'axe':row['parts']['Axe'],'shield':row['parts']['Shield'],'minimum_iou':m['minimum_iou'],'pooled_iou':m['pooled_iou'],'minimum_ssim':m['minimum_ssim'],'visual_gate_pass':row['visual_gate_pass'],'rig_gate_pass':True,'arm_p99':max(g['arm_p99'] for g in gates.values()),'finger_max':max(g['finger_max'] for g in gates.values()),'head_mm':max(g['head_mm'] for g in gates.values()),'minimum_z_mm':min(g['minimum_z'] for g in gates.values())*1000,'raw_glb_sha256':invariance[str(i)]['raw_glb_sha256']})
save(R/'reduction_results.json',{'lods':rows,'original_close_thresholds':{'iou':.995,'ssim':.98},'revised_far_pooled_iou_threshold':.97,'all_colour_lod_rig_gates_pass':True,'all_visual_gates_pass':all(r['visual_gate_pass'] for r in rows),'technical_completion':False,'installed_lod3':J(R/'installed_lod3_metrics.json')})
with (R/'reduction_curve.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
curve=[{'name':'Accepted round 2','triangles':15427,'iou':1.,'ssim':1.,'decision':'baseline'}]
for name,folder,tris,decision in [('Initial rebake','rebake_soft_seams',9873,'rejected: prop close-up'),('Next body step','rebake_soft6',9192,'rejected: image thresholds'),('Reduced props','rebake_props_next',9565,'rejected: inner bevel/UV transfer'),('Further props','rebake_props_limit',8814,'rejected: SSIM')]:
 m=J(R/folder/'physical/metrics.json');curve.append({'name':name,'triangles':tris,'iou':m['minimum_iou'],'ssim':m['minimum_ssim'],'decision':decision})
curve.append({'name':'Selected protected axe','triangles':after[0],'iou':rows[0]['minimum_iou'],'ssim':rows[0]['minimum_ssim'],'decision':'selected; all legacy rig gates pass'})
save(R/'close_reduction_curve.json',curve)
try:
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
 for ax,key,threshold in zip(axes,['iou','ssim'],[.995,.98]):
  for index,r in enumerate(curve):ax.scatter(r['triangles'],r[key],c='green' if index==len(curve)-1 else 'steelblue');ax.annotate(str(index),(r['triangles'],r[key]),xytext=(4,3),textcoords='offset points')
  ax.axhline(threshold,c='red',ls='--',label=f'target {threshold}');ax.set(xlabel='Combined LOD0 triangles',ylabel='Minimum '+key.upper());ax.invert_xaxis();ax.grid(alpha=.2);ax.legend()
 fig.suptitle('FighterChain round 3: measured candidates (labels in close_reduction_curve.json)');fig.savefig(R/'reduction_curve.png',dpi=150);plt.close(fig)
except ModuleNotFoundError:pass
# Same-camera pairs retain the full-resolution inputs alongside the readable sheets.
def pairs(left,right,out,size):
 canvas=Image.new('RGB',(size*2,(size+24)*8),(48,48,48));draw=ImageDraw.Draw(canvas)
 for i in range(8):
  for col,folder in enumerate([left,right]):
   im=Image.open(folder/f'{i}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(46,46,46,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB').resize((size,size)),(col*size,i*(size+24)+24));draw.text((col*size+8,i*(size+24)+6),f'{i*45} deg | '+('accepted' if col==0 else 'selected'),fill='white')
 canvas.save(out)
pairs(R/'rebake/physical/reference_lod0',R/'head_1k/physical/rebaked_lod0',R/'eight_view_comparison.png',512)
for i in range(1,4):pairs(R/f'final_lower/physical/reference_lod{i}',R/f'final_lower/physical/selected_lod{i}',R/f'lod{i}_comparison.png',384 if i==1 else 256)
for prop in ['axe','shield']:
 a=Image.open(P/f'review/round2/details/{prop}_standalone_quarter.png').convert('RGB');b=Image.open(R/f'details/{prop}_standalone_quarter.png').convert('RGB');im=Image.new('RGB',(a.width+b.width,a.height+28),(48,48,48));im.paste(a,(0,28));im.paste(b,(a.width,28));draw=ImageDraw.Draw(im);draw.text((10,8),'Accepted round 2',fill='white');draw.text((a.width+10,8),'Selected round 3',fill='white');im.save(R/f'{prop}_comparison.png')
for view in ['front','left','three_quarter']:shutil.copy2(P/f'review/clips_{view}.png',R/f'clips_{view}.png')
progress=J(P/'creature_3d_progress.json');progress.update(status='handoff_with_open_faults',stage='review_round_3_handoff',technical_completion=False,user_acceptance='round_2_accepted; round_3_triangle_reduction_review_pending',review_round_3={'counts_before':before,'counts_after':after,'credits_used_this_round':0,'open_faults':['LOD3 pooled silhouette IoU 0.95904 < 0.97 at 88 pixels'],'actors_changed':False,'evidence':'review/round3/reduction_results.json'});save(P/'creature_3d_progress.json',progress)
# Hash every final runtime asset, texture, selected lower authoring file and review sheet.
changed=[E/n for n in files]+list((P/'textures').glob('round3_lod*/*.png'))+[P/'textures/figc_round3_ramps.json']+[R/f'export_lod{i}/mm6_figc_authoring.blend' for i in range(1,4)]+[P/f'review/clips_{v}.png' for v in ['front','left','three_quarter']]
save(R/'changed_files.json',{str(f.relative_to(P)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in changed})
table='| LOD | Before | After (body + axe + shield) | Min IoU | Pooled IoU | Min SSIM | Rig gates |\n|---|---:|---:|---:|---:|---:|---|\n'+''.join(f"| {r['lod']} | {r['before']:,} | {r['after']:,} ({r['body']} + {r['axe']} + {r['shield']}) | {r['minimum_iou']:.6f} | {r['pooled_iou']:.6f} | {r['minimum_ssim']:.6f} | pass |\n" for r in rows)
hashes='| File | SHA-256 |\n|---|---|\n'+''.join(f"| export/{name} | `{art['files'][name]['sha256']}` |\n" for name in files)
main=rows[0];blow=J(P/'work/blade_gate.json');grip=J(R/'gates/grip_envelopes.json');budget='30/100 credits used overall; 0 credits used in round 3.'
text=f"""# FighterChain handoff — review round 3

**Re-exported and reviewed; the LOD3 visual gate remains open.** The round-2 appearance was accepted by the user. No clips, tier ramps, grip frames or binding values were redesigned. {budget}

## Triangle reduction

LOD0 is **{after[0]:,} triangles, down {(1-after[0]/before[0])*100:.2f}%**. The body is 6,797, the axe 2,122 and the shield 1,328 triangles. Geometry was reduced in approximately 10% component steps with weighted protection for the face, hands, joints, silhouettes and contacts. Body/head maps were rebaked with their seam connectivity retained; rigid props received separate UV charts and isolated source baking. Base colour, masks, ORM and tangent normals were transferred. The accepted axe head, socket and wooden shaft remain exact source geometry; the 318 axe-triangle saving comes from the wrap/fittings. More aggressive head reduction produced a visible inner-bevel defect and was rejected even when whole-character SSIM passed.

{table}

LOD0 uses the user's original strict thresholds (every view IoU >= 0.995 and SSIM >= 0.98), at about 690–700 pixels body height. LOD1–3 use the subsequently revised batch criterion: pooled IoU >= 0.97 at actor heights 550/220/88 pixels. Minimum per-view SSIM is reported for the distant levels without pretending those levels meet 0.98. Metrics use eight azimuths, Standing at frame 0, fixed cameras, the actual tier-A material equation, CPU Cycles and a tight foreground bounding window for SSIM. All three tiers share the same geometry and unchanged ramp values.

The next body trial (9,192 combined triangles with its trial props) failed at 0.994412 IoU / 0.978499 SSIM. The more aggressive prop trial (8,814 combined) failed SSIM at 0.974644. The 9,565-triangle trial passed whole-body metrics but failed the manual prop close-up. This is a measured, conservative stop, not a claim of globally optimal topology. The complete historical trials and selected results are in [review/round3/](review/round3/), especially [reduction_curve.csv](review/round3/reduction_curve.csv), [close_reduction_curve.json](review/round3/close_reduction_curve.json), [reduction_results.json](review/round3/reduction_results.json), [eight-view pairs](review/round3/eight_view_comparison.png) and the three LOD comparison sheets.

**Open fault:** LOD3's pooled IoU is {rows[3]['pooled_iou']:.6f}, below 0.97. It improves on the installed 903-triangle LOD3's {J(R/'installed_lod3_metrics.json')['pooled_iou']:.6f} under the same 88-pixel comparison, and its 898 triangles remain below the installed cap. Contour fitting, extra silhouette edges and contact projection improved it but did not meet the target. Technical completion is therefore recorded as false. No failing trial has been labelled a pass.

## Review round 3

The three runtime GLBs below are the integration candidates; the portable GLB is combined tier-A LOD0 for review, and the Blender file is the canonical packed authoring source. [All changed delivery-file hashes](review/round3/changed_files.json), [artifact sizes](export/artifacts.json), [texture hashes/dimensions](review/round3/texture_manifest.json) and lower-LOD authoring files are retained. Re-export the packed source with `scripts/export_baked.py`; `scripts/export_runtime.py` is only for explicitly supplied original-UV trial sources. `scripts/lods.py` and `scripts/runtime_finish.py` package the selected lower meshes, colour regions, head atlases, attachments and viewer.

{hashes}

**integration/actors.yml did not change.** SHA-256: `{sha(P/'integration/actors.yml')}`. Descriptors 535–537, tiers figc_a/b/c, scale 126.027899, z offset -1.512415, yaw -1.570796327 and melee impact 0.715 seconds remain unchanged. The 1,392 animation channels in each raw LOD export are byte-identical to the accepted export; all eight clips and the 58-bone skeleton remain. [Animation/binding proof](review/round3/animation_invariance.json).

Existing G4/G5/G6 checks pass on all four colour LODs, all eight clips, 682 samples per LOD at 48 Hz. LOD0 maximum pooled arm p99 is {main['arm_p99']:.6f}, finger stretch {main['finger_max']:.6f}, head contact {main['head_mm']:.3f} mm; arm/prop-body contacts are zero and floors stay nonnegative. The blade gate passes at {blow['time']:.6f} s, speed {blow['tip_speed_m_s']:.3f} m/s and edge share {blow['edge_share']:.6f}. Motion trace has no flags. Dense grip-envelope clearance changed by at most {grip['maximum_clearance_loss_mm']:.4f} mm. This is an envelope comparison, not a new per-digit surface-contact certificate. Export parity and UV checks pass.

Bindings/weights are checked by `check_bindings.py` with no BAD line. The viewer check covers 24 tier/clip switches; all eight clips are played at 1x and 0.5x. Fresh front, side and three-quarter sheets contain 168 frames. [Viewer](review/viewer/index.html), [round-3 close-ups](review/round3/details/), [axe comparison](review/round3/axe_comparison.png), [shield comparison](review/round3/shield_comparison.png), [playback record](review/round3/viewer_c/playback_review.json).

Coverage limit: unchanged bone channels preserve the accepted elbow/roll/palm motion, but this round does not claim a new absolute closed-volume sleeve/hem containment certificate for the layered, open garment surfaces. Exploratory nearest-face cloth probes are not acceptance evidence. Colour-mesh rig gates and final weight checks are distinct from a new full shared-suite audit of every shadow mesh.

Body/gear LOD0 maps are 2048 pixels; the head is 1024. The body/head atlas is 3104x2048, followed by 2080x1024, 1056x512 and 544x256. A 1K body colour trial failed SSIM (0.977633). Per-LOD rebakes increase texture storage: the three runtime GLBs total {storage_report['after']['runtime_glb_bytes']/1048576:.2f} MiB versus {storage_report['before']['runtime_glb_bytes']/1048576:.2f} MiB before. [Storage estimates](review/round3/storage.json) report the separate uncompressed pixel cost; triangle savings are not a claim of lower total GPU memory.

No assets_dev installation, game launch, build, regression run or commit was performed. Integration and game checks remain with the orchestrator. The workspace lease is released at handoff.

## Historical handoffs

The following sections record earlier deliveries. Their counts, hashes and completion statements are superseded by the round-3 record above.

"""
handoff=P/'HANDOFF.md';old=handoff.read_text();marker='# FighterChain handoff — review round 3'
if old.startswith(marker):old=old.split('## Historical handoffs\n',1)[1].split('\n\n',2)[-1]
handoff.write_text(text+old)
readme=P/'README.md';old=readme.read_text();prefix=f"""# Current delivery: review round 3

LOD colour counts: **{' / '.join(f'{n:,}' for n in after)}**, from 15,427 / 7,712 / 2,771 / 903. Main body/axe/shield: 6,797 / 2,122 / 1,328. Clips, palette ramps and actors.yml are unchanged. {budget}

**LOD3's 0.95904 pooled IoU remains below 0.97; this is a handoff with an open visual gate.** Existing colour-LOD rig gates, bindings and viewer checks pass. See [HANDOFF.md](HANDOFF.md) for exact hashes, metrics, coverage limits and the texture-memory tradeoff. [Round-3 evidence](review/round3/reduction_results.json).

Reproduction uses the packed `export/mm6_figc_authoring.blend` with `scripts/export_baked.py`, then copies the PNG/+Y-normal raw GLB to `export/mm6_figc_runtime_lod0.glb` and runs `scripts/lods.py` / `scripts/runtime_finish.py`. Lower sources are `review/round3/export_lod1..3/`. Run under a reclaimed workspace lease. The legacy `export_runtime.py` replaces materials and is intentionally restricted to explicit original-UV trial inputs.

Batch decisions: preserve the accepted animation and bindings; retain the stronger original close-up thresholds despite the later relaxed batch text; use the revised pooled silhouette criterion at 550/220/88 pixels; retain the original axe head after close-up rejection of its decimation; keep original source textures untouched and rebake into `textures/round3_lod*`; report the unresolved distant silhouette gate instead of relaxing it. UV charts on the body preserve seam connectivity; props need fresh charts because their original projected UVs overlap.

## Earlier project record

"""
if old.startswith('# Current delivery: review round 3'):old=old.split('## Earlier project record\n\n',1)[1]
readme.write_text(prefix+old)
print('RECORDED_ROUND3',after,'OPEN_LOD3',rows[3]['pooled_iou'])
