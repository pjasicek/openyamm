"""Record the selected review revision and distinguish measured passes from remaining review gaps."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,image_of,slot,TEXTURE_SLOTS
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads((P/f).read_text())
main=read('review/runtime_gates/gates.json');neck=read('review/round3_neck_floor_gates/gates.json')
assert main['status']==neck['status']=='PASS'
for report in [main,neck]:
    for asset in report['assets']:assert sha(Path(asset['path']))==asset['sha256']
viewer=read('review/viewer_check.json');assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD' not in (P/'review/bindings_check.txt').read_text()
info=read('export/export_info.json');counts=read('export/lods.json');skin=read('review/round3_skin.json')
inventory={};textures={}
for name in ['mm6_natm.glb','mm6_natm_spear.glb','mm6_natm_buckler.glb','mm6_natm.blend']:
    f=P/'export'/name;inventory[name]={'bytes':f.stat().st_size,'sha256':sha(f)}
for kind,file,node in [('body','mm6_natm.glb','Natm'),('spear','mm6_natm_spear.glb','Spear'),('buckler','mm6_natm_buckler.glb','Buckler')]:
    d,b=read_glb(P/'export'/file);assert len(d['images'])==4
    index=next(n['mesh']for n in d['nodes']if n.get('name')==node);chain=[index]+d['meshes'][index]['extras']['openyamm_lods'];sets=[]
    for mi in chain:
        pr=d['meshes'][mi]['primitives'][0];sets.append([slot(d['materials'][pr['material']],key)['index']for key in TEXTURE_SLOTS])
    assert all(v==sets[0]for v in sets)
    for mesh in d['meshes']:
        if mesh.get('name','').endswith('_Shadow'):
            for pr in mesh['primitives']:assert d['materials'][pr['material']].get('alphaMode','OPAQUE')=='OPAQUE'
    textures[kind]={'images':4,'texture_indices_by_lod':sets,'sizes':[image_of(d,b,i)[0].size for i in sets[0]]}
images={str(f.relative_to(P)):{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted((P/'export/textures_shared').rglob('*.png'))}
manifest={'review_round':3,'files':inventory,'triangles':counts,'animations':info['clips'],'bones':78,
          'textures':textures,'image_files':images,'bindings_sha256':sha(P/'integration/actors.yml')}
(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'review/round3_texture_audit.json').write_text(json.dumps(textures,indent=2)+'\n')
for role,row in info['clips'].items():
    page=Image.new('RGB',(2100,1228),(32,32,32));draw=ImageDraw.Draw(page)
    draw.text((12,10),f'Review round 3 | {role} | {row["duration"]:.6f}s | final runtime GLBs',fill='white')
    for j,view in enumerate(['front','left','three_quarter']):
        for i,t in enumerate(np.linspace(0,row['duration'],7)):
            image=Image.open(P/f'review/final/{role}_{i:02}_{view}.png').convert('RGB');image.thumbnail((300,370))
            x=i*300+(300-image.width)//2;y=42+j*390;page.paste(image,(x,y));draw.text((i*300+8,y+370),f'{view}: {t:.3f}s',fill='white')
    page.save(P/f'review/sheets/{role}.jpg',quality=93)
lod_metrics={}
for level,size in [(1,550),(2,220),(3,88)]:
    intersections=unions=0;rows=[]
    for i in range(8):
        a=np.array(Image.open(P/f'review/reduction/round3_lod0_{size}/natm_b_{i}.png'))[:,:,3]>127
        b=np.array(Image.open(P/f'review/reduction/round3_lod{level}_{size}/natm_b_{i}.png'))[:,:,3]>127
        ii=int((a&b).sum());uu=int((a|b).sum());intersections+=ii;unions+=uu;rows.append(ii/uu)
    lod_metrics[str(level)]={'actor_pixels':size,'views_iou':rows,'pooled_iou':intersections/unions}
    assert intersections/unions>=.97,(level,intersections/unions)
(P/'review/reduction/round3_metrics.json').write_text(json.dumps(lod_metrics,indent=2)+'\n')
def maximum(report,name,clip=None):
    return max(r['worst']for r in report['gates']if r['gate']==name and (clip is None or r['clip']==clip))
table='\n'.join(f'| {name} | {v["bytes"]:,} | `{v["sha256"]}` |'for name,v in inventory.items())
triangles='\n'.join(f'| {i} | {counts["body"][i]} | {counts["spear"][i]} | {counts["buckler"][i]} |'for i in range(4))
gate_rows='\n'.join(f'| {name} | {maximum(main,name):.6g} |'for name in ['arm_stretch_p99','hand_stretch_max','elbow_plane_deg','wrist_flexion_deg','angular_acceleration_deg_s2','prop_body_penetration_mm','cloth_penetration_mm','grip_gap_mm'])
import shutil
from PIL import ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
page=Image.new('RGB',(1800,2160),(32,32,32));draw=ImageDraw.Draw(page)
for col,revision in enumerate([1,2,3]):
 x=col*600;draw.text((x+16,15),f'Round {revision}',font=font,fill='white')
 for row,(view,label,h) in enumerate([('body_front','Front',760),('chest_front','Chest and arms — front',590),('chest_three_quarter','Chest and arms — angled',590)]):
  y=[80,900,1535][row];pic=Image.open(P/f'review/final/round3_compare_r{revision}_{view}.png').convert('RGB');pic.thumbnail((600,h));page.paste(pic,(x+(600-pic.width)//2,y));draw.text((x+10,y-28),label,font=font,fill='white')
page.save(P/'review/round3_skin_comparison.jpg',quality=95)
refs=Path('/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/5707d78c-82f0-4aec-b463-6fc01c03b6f9/images')
page=Image.new('RGB',(1800,1440),(32,32,32));draw=ImageDraw.Draw(page)
for row,(native,frame,title) in enumerate([(88,21,'Wind-up'),(89,44,'Forward drive')]):
 shutil.copy2(refs/f'{native}.png',P/f'review/round3_native_{native}.png')
 for col,(path,label) in enumerate([(P/f'review/round3_native_{native}.png','User-selected native'),(P/f'review/final/round3_attack_{frame:02}_three_quarter.png',f'Final frame {frame} / 48 Hz'),(P/f'review/final/round3_attack_{frame:02}_left.png','Final side')]):
  pic=Image.open(path).convert('RGBA')
  if col:
   pic=pic.crop(pic.getchannel('A').getbbox());bg=Image.new('RGBA',pic.size,(87,87,87,255));bg.alpha_composite(pic);pic=bg
  pic=pic.convert('RGB');scale=min(580/pic.width,620/pic.height);pic=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.LANCZOS);x=col*600;y=row*720;page.paste(pic,(x+(600-pic.width)//2,y+50));draw.text((x+12,y+12),f'{title}: {label}',font=font,fill='white')
page.save(P/'review/round3_attack_targets.jpg',quality=95)
review_files=[P/'review/round3_skin_comparison.jpg',P/'review/round3_attack_targets.jpg',P/'review/viewer/manifest.json']
manifest['review_artifacts']={str(f.relative_to(P)):sha(f)for f in review_files};manifest['gate_reports']={str(f):sha(P/f)for f in ['review/runtime_gates/gates.json','review/round3_neck_floor_gates/gates.json']};(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
diag=read('review/round3_final_diagnostics.json');fit=read('review/round3_coarse_grip_fit.json')
text=f'''# MM6 PeasantM4 / natm — staged review handoff

Latest: **Review round 3**. Re-exported; implemented shared gates, bindings and viewer pass.
Artistic changes are staged for review. Outstanding qualifications are listed below; this is not an unqualified
completion of every current batch requirement. **50/100 Meshy credits spent; zero this round.**
No installation, shared registry edit, build, game launch or commit. Original ../mm6_natm remains read-only.

## Review round 3

- Rebuilt Attack around the user's native poses: frames 0–21 shift back, lift the front knee, lean/twist the torso
  back and raise the spear/shield. The creature steps into a low forward lunge, drives the level shaft with both hands,
  then opens the off hand and recovers. Left hand sits ahead of the dominant right hand on the shaft.
  Attack is **108 frames / 2.25 s**. Cached `2HandSpearAttack10` supplies residual body motion;
  native key poses and anatomical IK fill the pose gap. This is a substantial authored adaptation, not an unaltered library clip.
- Shared blow measurement: **43.5/48 = 0.906250000 s**, tip **8.355556 m/s**, pointing error **0.000197°**,
  fastest aimed-tip timing error **0 s**. Off hand has a fixed shaft grip through frames 42–52, including the blow.
  [Native/final pose comparison](review/round3_attack_targets.jpg), [clip sheets](review/sheets/).
- Head stays forward: authoring diagnostic maximum deviation **{diag['head']['Attack']['max_forward_angle_deg']:.3f}°**
  in Attack, **{diag['head']['Cast']['max_forward_angle_deg']:.3f}°** in Cast. Neck/head have no translation/scale channels.
  Neck deformation passes the shared stretch probe; the diagnostic is not a replacement head-facing gate.
- Restored original Meshy anatomical luminance variation and full normal-map detail using round 2's warm-brown chroma.
  Exposure is balanced continuously through chest/neck/head; neck contrast is compressed to prevent a dark ring.
  Pink upper-arm components are brown and assigned to the skin palette on every tier.
  [Round 1 / 2 / 3 skin comparison](review/round3_skin_comparison.jpg) shows body and chest/arms under identical lighting.
  [Skin measurements](review/round3_skin.json). Head retains its 1K source map before shared atlas merging.
- Fixed stale atlas reuse: full packing refreshes `work/shared_atlas_cache/`. Selected runtime atlases contain round 3 skin.
  Four shared images per GLB, accepted texel density, >=16 px island dilation, opaque shadows. No per-LOD texture sets.
  No claim of reduced decoded atlas memory.
- Death is **80 frames / 1.666667 s**, exactly half its former 160-frame duration. Exported Death endpoint and Dead bone
  matrices are unchanged (maximum endpoint delta **0**); Dead remains **0.041667 s**.
  [Final diagnostics](review/round3_final_diagnostics.json).
- Refined coarse left-hand weights and seated palm/finger surfaces against the shaft without adding triangles.
  Near LOD changes three vertices by at most **{fit[0]['maximum_bind_move_mm']:.3f} mm**; coarse corrections are in
  [the fit receipt](review/round3_coarse_grip_fit.json). Three LOD3 belt-feather corners move 23 mm;
  right calf feathers compress by at most 22.64% only during Attack for floor clearance. Death/Dead feather keys stay unchanged.
- **integration/actors.yml changed:** all six melee/ranged impacts across three tiers move from 0.489583333 to
  **0.906250000**. Cast stays **0.479166667**, socket `Socket_LeftPalm`; scale, yaw and look limits unchanged.
  Bindings SHA256: `{sha(P/'integration/actors.yml')}`.

### Files, hashes and triangle counts

Only these three runtime GLBs are integration inputs. `mm6_natm.blend` is the editable near source;
`work/runtime_lod0.blend` through `runtime_lod3.blend` are final editable LODs.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
{table}

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
{triangles}

Counts are unchanged. [Manifest](export/manifest.json) records image hashes, animations and report hashes.
Switch-size pooled silhouette IoU: {', '.join(f'LOD{k} {v["pooled_iou"]:.6f}'for k,v in lod_metrics.items())}.
Original reduction curve retained; no new reduction search this round. Texture appearance deliberately differs from
rejected earlier skin; SSIM against that skin is not acceptance evidence.

### Validation on these files

- [Main shared runner](review/runtime_gates/gates.md): **PASS**, {main['counts']}, all nine clips and colour/shadow LODs.
- [Neck and whole-solid-body floor probe](review/round3_neck_floor_gates/gates.md): **PASS**, {neck['counts']}.
  Neck p99 **{maximum(neck,'arm_stretch_p99'):.6f}×**, maximum edge **{maximum(neck,'arm_stretch_max'):.6f}×**, limits 1.5×/2×.
  Worst floor penetration **{maximum(neck,'floor_penetration_mm'):.6f} mm**;
  Dead **{maximum(neck,'floor_penetration_mm','Dead'):.6f} mm**.
- [Bindings](review/bindings_check.txt): exit 0, **no BAD line**, including weights and shadow opacity.
- [Viewer](review/viewer_check.json): **27 switches**, zero failures or console errors. Owned Chrome processes stopped.
- [Skin comparison](review/round3_skin_comparison.jpg), [attack targets](review/round3_attack_targets.jpg),
  [clip sheets](review/sheets/), [corpse/close-ups](review/final/), [LOD metrics](review/reduction/round3_metrics.json).

| Main measurement | Worst value |
|---|---:|
{gate_rows}

Death smoothness limits scale with the requested 2× compression: rotation step 50° (2×), angular acceleration
80000°/s² (4×). Other clip limits are unchanged. Attack posture allows the low lunge: pelvis minimum 0.70 m,
lean maximum 50°. Inherited LOD3 ratio allowance remains 0.102. Shared runner source is unchanged;
[config](gates.json) records the allowances.

### Open qualifications and integration ownership

1. Shared runner lacks head-forward and Cast-palm-to-target checks and rejects unknown config fields.
   [Requested extension](integration/shared_gate_request.json) records intent. Authoring diagnostics are evidence,
   **not shared-gate PASS**. Orchestrator owns shared checks and runtime head-look verification.
2. Strict native per-region luminance/percentile matching remains unmet. Native head/neck/chest means are
   55.54/33.38/43.76, p95 105.02/60.06/97.31; native lighting is baked into these pixels. Current head/chest means are
   about 64.82/62.93, neck 59.62–61.86, with anatomical variation. This follows the latest consistent-hue/detail request;
   user artistic review remains required.
3. Running retains historical `RelaxRunForward`. This review did not replace it, so it does **not** meet the later
   Standard Run batch rule. Passing its existing gait gates does not waive that requirement.
4. Native installation, captures, runtime head-look layering and regression belong to the orchestrator.
   Nothing was copied to assets_dev. Existing reduction counts remain; no new 5–8k near-body search was made.

### Reproduction / selected sources

`review3_selected_build.py` loads `work/round3_key_baseline/`, applies staged motion, hand corrections and feather fixes,
reloads round 3 maps and exports. Then `runtime_pack.py --reuse-atlas` and `review3_finalize.py` produce runtime files.
`review1_preview_source.py`, `make_viewer.py`, `review3_comparison_models.py`, `review3_final_render.py` build review assets.
`review3_records.py` writes these records after shared gates, bindings and viewer checks.
Other round-3 trial scripts/numbered gate folders are provenance, not selected final validation.

## Review round 2

Head/neck skinning, forward Cast palm, socket and warm-brown chroma repairs remain.
[Full round-2 handoff and hashes](work/review_round3_before/HANDOFF.md). Its flat skin is superseded above.

## Review round 1

Opaque shadows, shared padded textures and corpse back-feather repairs remain.
[Full round-1 handoff](work/review_round2_before/HANDOFF.md).
'''
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text('''# MM6 PeasantM4 / natm — review round 3

Cannibal / Head Hunter / Witch Doctor, male. Three tiers, nine clips, 78 bones, four LODs.
**50/100 Meshy credits spent; zero this round.**

[HANDOFF.md](HANDOFF.md) records files, hashes, checks and outstanding qualifications.
[Viewer](review/viewer/index.html), [skin comparison](review/round3_skin_comparison.jpg),
[native/final attack poses](review/round3_attack_targets.jpg), [clip sheets](review/sheets/).

Attack raises the front knee during a backward wind-up, then drives into a two-handed low lunge.
Impact is 0.90625 s. Skin restores muscle detail with one warm-brown hue and removes pink upper-arm patches.
Death is 2× faster; endpoint and Dead bone pose unchanged. Implemented shared gates, bindings and viewer pass.

## Recorded decisions

- Work only here; ../mm6_natm read-only. No commits, installs, builds or game launches.
- Native poses need substantial authoring over cached 2HandSpearAttack10 residual motion, not an unmodified library clip.
- Left hand ahead of dominant right hand; fixed two-hand grip spans the blow.
- Original normal detail and balanced luminance restore anatomy; shared chroma prevents earlier colour patches.
- Atlas cache rebuilt after texture changes so repacks cannot restore flat skin.
- Shared head-forward/Cast-palm checks remain unsupported; diagnostics are separate evidence.
- Strict native pixel percentiles remain open; prioritize latest consistent-hue/detail request.
- Existing RelaxRunForward and reduction counts retained; later requirements are not claimed as fulfilled.
- Death smoothness allowances scale only for explicit 2× retiming.
- Final editable LODs: work/runtime_lod*.blend. Selected pipeline is recorded in HANDOFF.md.
- Orchestrator owns native integration, captures, missing shared checks and user artistic review.
''')
progress=read('creature_3d_progress.json');progress.update(stage='Review round 3: re-exported and checked; qualifications documented',status='handoff_with_review_gaps')
progress['review_round_3']={'credits_spent':0,'files':inventory,'bindings_changed':True,'shared_gates':main['counts'],'neck_floor_gates':neck['counts'],'viewer_switches':27,'attack_impact_s':.90625,'death_duration_s':80/48,'open_qualifications':['Shared runner lacks head-forward/Cast-palm target gates','Strict native luminance percentiles not matched','Historical Running source does not meet later Standard Run rule','Existing reduction counts retained'],'next_action':'Orchestrator: review round-3 sheets and qualifications, integrate approved files and capture native runtime.'}
progress['next_action']=progress['review_round_3']['next_action'];progress['handoff']={'file':'HANDOFF.md','review_round':3,**progress['review_round_3']};(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('ROUND3_RECORDS_WRITTEN',inventory,flush=True)
