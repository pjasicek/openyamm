"""Publish current receipts and the review-round-2 handoff."""
from pathlib import Path
import json,hashlib,datetime,shutil,numpy as np,yaml
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/'review/round2'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=lambda p:{'sha256':sha(p),'bytes':p.stat().st_size}
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
g=json.loads((R/'shared_gates/gates.json').read_text());assert g['status']=='PASS'and not g['error']
for asset in g['assets']:assert sha(Path(asset['path']))==asset['sha256']
v=json.loads((R/'viewer_check.json').read_text());assert v['switched']==24 and not v['failed']and not v['consoleErrors']
assert 'BAD'not in(R/'bindings.txt').read_text()
manifest=json.loads((P/'review/viewer/manifest.json').read_text());assert len(manifest['models'])==3
for m in manifest['models']:assert sha(P/'review/viewer'/m['url'].split('?')[0])==m['sha256']
motion=json.loads((R/'motion_preservation.json').read_text());assert motion['after_sha256']==sha(P/'export/mm6_mfp.glb')
receipts=json.loads((P/'source/native_inputs.json').read_text());old=json.loads((P/'review/round1/source_verification.json').read_text())
for e in receipts+old['restored_references']:assert sha(ROOT/e['path'])==e['sha256']
write(R/'source_verification.json',{'verified_utc':now,'original_receipts':len(receipts),'all_match':True,'native_manifest':'source/native_inputs.json','restored_references':old['restored_references']})
# Spatial cheek ROI excludes eyes, mouth and forehead jewelry.
s=np.load(P/'work/round1/textures/lod0/mfp_head_surface.npz')
a=np.array(Image.open(P/'work/round2/textures/mfp_head_basecolor.png').convert('RGB'))/255
lin=lambda a:np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
light=lin(a)@np.array([.2126,.7152,.0722]);x,y,z=np.moveaxis(s['pos'],2,0)
cheek=s['cov']&s['front']&(np.abs(x)>.018)&(np.abs(x)<.04)&(z>1.50)&(z<1.52)&(y<-.065)
neck=s['cov']&s['front']&(z>1.40)&(z<1.445)&(np.abs(x)<.035)&s['skin']
stats=lambda mask:{'pixels':int(mask.sum()),'mean':float(light[mask].mean()),'p90':float(np.percentile(light[mask],90)),'p95':float(np.percentile(light[mask],95))}
skin={'native':json.loads((P/'review/round1/skin_luminance.json').read_text())['native'],'cheek_roi_m':{'abs_x':[.018,.04],'z':[1.50,1.52],'y_max':-.065},'cheeks':stats(cheek),'head_neck':stats(neck),'body':json.loads((R/'texture_production.json').read_text())['regions']['mfp'],'interpretation':'Pigment means match native warm brown; cheeks exclude eyes/lips/jewelry. Flat body albedo does not reproduce already-lit native highlight percentiles. Highlights belong to scene lighting; historical round-1 percentile equality is superseded.'}
write(R/'skin_pigment.json',skin)
summary={}
for gate in sorted({r['gate']for r in g['gates']}):
 rows=[r for r in g['gates']if r['gate']==gate and isinstance(r.get('worst'),(int,float))]
 if rows:summary[gate]={'min':min(r['worst']for r in rows),'max':max(r['worst']for r in rows),'unit':rows[0].get('unit','')}
soles={}
for r in g['gates']:
 if r['gate']=='lowest_sole_m':
  entry=soles.setdefault(r['clip'],{});entry[r['region']]=min(entry.get(r['region'],1e9),1000*r['worst'])
tri={asset:[int(next(r['worst']for r in g['gates']if r['gate']=='triangles'and r['asset']==asset and r['lod']==f'colour{i}'))for i in range(4)]for asset in ['body','knife']}
assert tri=={'body':[10183,5513,2278,1235],'knife':[2344,1289,543,303]}
files=['export/mm6_mfp.glb','export/mm6_mfp_knife.glb','export/mm6_mfp.blend','integration/actors.yml'];delivery={f:record(P/f)for f in files}
beforeactors=P/'work/round2/before/actors.yml'
if not beforeactors.exists():beforeactors=P/'work/round2/before/integration/actors.yml'
assert beforeactors.exists()
assert yaml.safe_load(beforeactors.read_text())==yaml.safe_load((P/'integration/actors.yml').read_text())
metrics={'revision':'review_round_2','generated_utc':now,'authority':'Unchanged claude_shared/gates/run_gates.py','status':g['status'],'counts':g['counts'],'assets':g['assets'],'triangles':tri,'summary':summary,'lowest_soles_mm_all_lods':soles,'sampling':g['sampling'],'skin':'round2/skin_pigment.json','viewer':'round2/viewer_check.json','bindings':'round2/bindings.txt'}
write(P/'review/final_metrics.json',metrics)
write(P/'review/runtime_audit.json',{'revision':'review_round_2','assets':g['assets'],'authority':'round2/shared_gates/gates.json','bindings':'round2/bindings.txt','viewer':'round2/viewer_check.json','runtime_game':'Not run; orchestrator owns installation and game checks.'})
shutil.copy2(R/'viewer_check.json',P/'review/viewer_check.json');shutil.copy2(R/'bindings.txt',P/'review/check_bindings.txt')
(P/'review/GATES.md').write_text('# Current verification\n\nReview round 2: **PASS** — 6,288 PASS, 136 INFO, 72 N/A; no failing rows.\n\n[Shared report](round2/shared_gates/gates.md), [JSON and bound hashes](round2/shared_gates/gates.json), [metrics](final_metrics.json), [bindings](round2/bindings.txt), [viewer](round2/viewer_check.json).\n\nBones: 48 Hz. Meshes: 24 Hz with adaptive refinement to 48 Hz. No new gate implementation or threshold relaxation this round. UV/skin files are production measurements, not additional rig gates.\n')
captures=[R/(row[0]+'.png')for row in json.loads((R/'capture_after.json').read_text())]
write(R/'capture_receipt.json',{'generated_utc':now,'runtime':delivery,'viewer_models':manifest['models']+json.loads((R/'lod_viewer_models.json').read_text()),'poses':len(captures),'captures':{str(p.relative_to(P)):record(p)for p in captures},'visual_review':'Agent inspected final face/blouse/arm/midriff, recovery, Hit, Running and LOD sheets. Software WebGL evidence; not game GPU evidence.'})
texgen=json.loads((R/'texture_generation.json').read_text());texgen['reference_sha256']=sha(P/texgen['reference'])
texgen['prompt']="Create a production texture tile for this exact character's sari fabric, using the attached reference only for its sari pattern. Output a 1024x1024 square flat albedo textile swatch, completely front-on, no perspective, no folds, no cloth edges, no shadows, no background, no text. The entire square is raspberry pink woven silk. One large circular antique-gold medallion is centered at (50%,50%), diameter about 72% of canvas width, using the same small floral/rosette details and pale tiny bead dots inside the golden circle as the reference sari, with clean fine embroidered outlines. Two slim vertical ornamental stripe bands at x=4% and x=96%, gold-edged with small ivory diamond/flower motifs like the sari stripe borders. The tile must repeat seamlessly both horizontally and vertically; leave matching plain pink space at top/bottom, no horizontal border. Crisp clean embroidery, restrained fine fabric weave, flat even albedo lighting, no fuzzy painting and no coarse grain. This is only the fabric texture, not a person, not an illustration of clothing. Preserve the reference's berry-pink, ochre-gold, and ivory palette and motif identity. Save the generated texture as an image asset."
texgen['actual_dimensions']=list(Image.open(P/texgen['output']).size);write(R/'texture_generation.json',texgen)
hash_table='\n'.join(f'| [{f}]({f}) | {d["sha256"]} |'for f,d in delivery.items())
triangle_table='\n'.join(f'| {i} | {tri["body"][i]:,} | {tri["knife"][i]:,} | {tri["body"][i]+tri["knife"][i]:,} |'for i in range(4))
sole_table='\n'.join(f'| {clip} | {d["L"]:.3f} | {d["R"]:.3f} |'for clip,d in sorted(soles.items()))
durations='\n'.join(f'| {clip} | {d["duration"]:.6f} |'for clip,d in manifest['clips'].items())
selected_gates=['cloth_penetration_mm','grip_gap_mm','grip_penetration_mm','arm_body_penetration_mm','head_penetration_mm','prop_body_penetration_mm','elbow_plane_deg','upper_arm_roll_deg','forearm_roll_deg','wrist_roll_deg','wrist_flexion_deg','rotation_step_deg','angular_acceleration_deg_s2','weight_sum_error','floor_penetration_mm','rest_sole_height_mm','rest_sole_tilt_deg','foot_yaw_deg','blow_time_error_s','blow_speed_fraction','blade_edge_share','blade_signed_lead']
gate_table='\n'.join(f'| {key} | {summary[key]["min"]:.6g} | {summary[key]["max"]:.6g} |'for key in selected_gates)
handoff=f"""# MM6 PeasantF3 / mfp — batch handoff

## Review round 2

**Repairs and project checks complete; artistic acceptance and game integration belong to the orchestrator.**
Updated {now}. Round-1 state is preserved in [work/round2/before/HANDOFF.md](work/round2/before/HANDOFF.md).

### Changes

- **Attack:** preserved wind-up/cut through frame 32 at 48 fps (0.666667 s). The hand then recovers directly to the side; the clip ends at **frame 54 / 1.125 s**, replacing 2.420833 s / 116 frames. The endpoint matches the requested previous frame-48 pose. Blow stays **0.656250 s**. The shared pose sampler measures at most {motion['attack_frames_0_32_max_matrix_delta']:.3g} matrix-component difference before frame 32 and {motion['old_frame48_vs_new_frame54_max_matrix_delta']:.3g} at the requested endpoint. [Receipt](review/round2/motion_preservation.json).
- **Body textures:** re-unwrapped/equalized the existing body islands, continuously transferred UVs to every LOD and rebuilt maps. Area-weighted body density rises **4.754 → 14.659 texels/cm**; triangle-density P10/P50/P90 is **13.364 / 14.659 / 15.728**. Head remains **20.326 texels/cm**. [Every island versus torso/head density](review/round2/uv_islands.csv), [summary](review/round2/uv_density.json).
- **Appearance:** removed baked vertical skin illumination, refreshed smooth skin normals, rebuilt quiet blouse weave and crisp physical-scale sari medallions. One textile tile was generated from the existing HD sari reference. [Prompt/source/hash](review/round2/texture_generation.json).
- **Head:** cleaned the HD-reference-derived 1K texture in surface space across UV seams, preserving eyes, lips, brows and gold details. Clean pigment blends into the body tone at the neck. Cheek mean linear luminance **{skin['cheeks']['mean']:.6f}**, body **0.128308**, native **{skin['native']['mean']:.6f}**. [Measurements](review/round2/skin_pigment.json).
- **Running:** verified the round-1 replacement, **UnarmedRunForward2** arms over the planted native-size gait. No RelaxRunForward. Forty shared-sampler comparisons give **zero pose difference** from the already-correct round-1 Running clip.

**No triangle reduction. No new Meshy jobs: spending remains 55 / 100 credits, six successful jobs.** The built-in imagegen textile tile is not a Meshy charge. No game launch, build, installation or commit. Native/restored sources and shared gate code remain unchanged.

### Delivery and integration

The orchestrator installs accepted exports with **tools/install_model.py**, then merges the staged descriptors. Do not copy exports directly into assets_dev.

| File | SHA-256 |
|---|---|
{hash_table}

**integration/actors.yml changed: yes, revision/timing/install header only.** Numerical descriptor blocks remain unchanged from round 1: all three melee/ranged/cast impacts **0.656250 s**, scale **107.495710585**, IDs **601–603**, skins **mfp_a/b/c**, yaw −π/2, walk stride **0.9 m**, runtime run stride **1.395 m**. Shorter Attack duration is embedded in the GLB; these descriptors have no duration field. Noncasters retain cast alias to Attack.

[Complete manifest](export/manifest.json) hashes delivery/evidence. Editable checkpoints: **work/round2/lod0.blend … lod3.blend**; [packed authoring file](export/mm6_mfp.blend). Canonical maps: **work/round2/textures/**. Production: scripts/round2_geometry.py, round2_surface_finish.py, round2_textures.py and round2_export.py.

| LOD | Body | Knife | Total |
|---|---:|---:|---:|
{triangle_table}

Counts are unchanged from round 1; colour/shadow chains match. Retained LOD3 total is 12.28% of LOD0, above approximate 10% guidance; the existing 13% cap and silhouette remain unchanged in this no-reduction round. Historical reduction IoU/SSIM numbers are not new texture scores.

Runtime body: **one shared 5152×4096 atlas set** (4096² body, 32 px gutter, 1024² head), four maps including region mask, three tiers. Islands receive 16 px margins; nearest-surface padding fills remaining body-atlas voids for coarse faces and filtering. Knife: unchanged shared 1024² set. Increased body resolution is a deliberate memory cost; native game performance is not verified.

### Checks

Unchanged [shared runner](review/round2/shared_gates/gates.md): **PASS — 6,288 PASS, 136 INFO, 72 N/A; no failing or missing rows**. JSON binds both current runtime hashes. Bones: **48 Hz**. Meshes: **24 Hz with adaptive 48 Hz refinement**, not uniform 48 Hz.

| Shared measurement | Minimum across rows | Maximum across rows |
|---|---:|---:|
{gate_table}

Walking swing **83.242–86.439 mm**, knee peaks **59.206–59.330°**. Running contact **100%**, maximum lowest-foot height **4.296 mm**. Limits and per-sample details are in the shared report; [current metrics](review/final_metrics.json) retain all ranges.

| Clip | Lowest left sole, mm | Lowest right sole, mm |
|---|---:|---:|
{sole_table}

Prone Dead has deliberately raised bent-leg soles. Eight clips, 121 joints:

| Clip | Duration, s |
|---|---:|
{durations}

[Bindings](review/round2/bindings.txt): **no BAD line**. [Shared viewer check](review/round2/viewer_check.json): **24/24 switches**, no failed loads or console errors. **240/240** original receipts and three restored attack references match. Browser/server processes are closed after checks.

### Evidence and limitations

[Round-2 index](review/round2/README.md): full-size before/after face, blouse, midriff and arm; [Attack recovery](review/round2/attack_recovery.png); [all LODs/tiers](review/round2/lod_tiers.png); grip/native comparisons; eight refreshed clip sheets. The project viewer zoom limit is extended to 30 m so the LOD3 evidence reaches its actual 88 px switch size (review/viewer/review.js and scripts/prepare_review.py). **206 final direct-viewer poses** are [hash-bound](review/round2/capture_receipt.json).

Pigment means and neck transition are matched. **Flatter skin albedo intentionally does not reproduce already-lit native P90/P95 values.** The round-1 percentile-matched baked lighting caused the reported vertical bands. Scene lighting now supplies highlights; the old percentile table is historical, not a current texture pass. The whole-head mask includes dark makeup/eyes/lips and is darker than clean cheek pigment.

Game rendering, memory/performance, runtime head look, save/load and indoor/outdoor regression remain with the orchestrator under [integration/regression.md](integration/regression.md). User artistic acceptance is pending. No reduction or game check was performed. Release the workspace lease after final manifest verification; no commit is authorized.

## Review round 1 — historical

[Complete preserved handoff](work/round2/before/HANDOFF.md), [round-1 evidence](review/round1/).
"""
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text("""# MM6 PeasantF3 — Cutpurse / Bounty Hunter / Assassin

Review round 2 repairs and project checks complete; game integration and artistic acceptance remain with the orchestrator. [HANDOFF.md](HANDOFF.md) has current hashes, counts, limitations and integration changes. Meshy: **55/100 credits**.

## Delivery

- [Body](export/mm6_mfp.glb), [knife](export/mm6_mfp_knife.glb), [packed authoring](export/mm6_mfp.blend).
- [Staged descriptors](integration/actors.yml), [regression](integration/regression.md).
- [Comparisons](review/round2/README.md), [shared gates](review/round2/shared_gates/gates.md), [manifest](export/manifest.json).
- Editable checkpoints: work/round2/lod0.blend through lod3.blend. Canonical maps: work/round2/textures/.

## Unattended decisions

Preserve the cut through frame 32; remove the slow tail and reach the requested hand-at-side pose by frame 54 (1.125 s). Keep blow .65625 s. Keep the already-replaced UnarmedRunForward2 arms and planted native-size gait; no RelaxRunForward.

Re-unwrap body islands, equalize scale, transfer UVs continuously across unchanged LODs and bake a 4K body set beside the retained 1K head. Shared atlas: 5152×4096, 32 px body/head gutter, 16 px island dilation. Increased resolution is deliberate: body density rises from 4.754 to 14.659 texels/cm versus head 20.326. All LODs share maps; knife stays 1K.

Clean skin uses native warm-brown pigment; smooth mesh lighting supplies highlights. Cheek/body means remain near native; the old albedo P90/P95 match is intentionally not retained because it encoded the reported directional bands. Preserve facial features/gold while cleaning across UV seams on the surface. Generate one sharp sari tile from the selected HD reference and map physical-size repeats; rebuild quiet unstretched blouse weave.

No reduction or geometry-position edits this round. Body counts 10183 / 5513 / 2278 / 1235; knife 2344 / 1289 / 543 / 303. Retain the selected distant silhouette and existing 13% LOD3 cap. Normals/UVs change, not topology.

## Reproduction and ownership

Claim a fresh lease before writes. One background Blender process, four threads, through tools/run_creature_blender.sh. Authoring order: round2_geometry.py, round2_surface_finish.py, round2_textures.py (ordinary Python), round2_export.py. Export reloads canonical disk images.

Use unchanged claude_shared/gates/run_gates.sh with export/mm6_mfp.glb, project gates.json and output review/round2/shared_gates. Bones 48 Hz, mesh adaptive 24→48 Hz. round2_evidence.py refreshes review LODs, per-island measurements and shared-sampler comparisons; round2_capture.py after captures the existing viewer; round2_sheets.py assembles sheets; round2_validate.py invokes existing checks; round2_finalize.py publishes records.

Sibling mm6_mfp/, shared scripts, runtime assets and engine remain read-only. No game/build/install/commit. Orchestrator installs accepted GLBs with tools/install_model.py, merges descriptors and runs game checks. Round-1 records: work/round2/before/. Earlier reduction scores remain historical.
""")
(R/'README.md').write_text("""# Review round 2

Final exported GLB viewer captures, identical cameras/lighting for each before/after pair. Software WebGL evidence, not game GPU/performance captures.

- [Face before/after](before_after_face.png)
- [Blouse before/after](before_after_blouse.png)
- [Midriff before/after](before_after_midriff.png)
- [Arm before/after](before_after_arm.png)
- [Attack recovery, frames 24–54](attack_recovery.png)
- [Reverse grip](grip.png)
- [Restored native attack comparison](attack_native_comparison.png)
- [All LODs/tiers at switch sizes](lod_tiers.png)
- [Every UV island](uv_islands.csv), [density summary](uv_density.json)
- [Motion preservation and Running source](motion_preservation.json)
- [Pigment measurements](skin_pigment.json), [texture production](texture_production.json)
- [Shared gates](shared_gates/gates.md), [bindings](bindings.txt), [viewer](viewer_check.json)
- [Capture/model hashes](capture_receipt.json)

Clips (front/side/quarter): [Standing](../sheets/Standing.png), [Walking](../sheets/Walking.png), [Running](../sheets/Running.png), [Attack](../sheets/Attack.png), [Hit](../sheets/Hit.png), [Death](../sheets/Death.png), [Dead](../sheets/Dead.png), [Fidget](../sheets/Fidget.png).

Cut through frame 32 retained, recovery finished frame 54 / 1.125 s; blow .65625 s. Running uses UnarmedRunForward2. Counts unchanged. Flatter skin pigment intentionally does not reproduce already-lit native highlight percentiles; see the handoff. Artistic acceptance pending.
""")
(P/'review/README.md').write_text('# PeasantF3 review\n\nCurrent: [Round 2](round2/README.md), [viewer](viewer/index.html), [shared gates](round2/shared_gates/gates.md), [metrics](final_metrics.json).\n\nHistorical: [round 1](round1/), [reduction study](REDUCTION.md). Historical IoU/SSIM and pigment-percentile numbers are not new round-2 texture scores.\n')
(P/'integration/regression.md').write_text("""# Orchestrator integration and regression — review round 2

Install export/mm6_mfp.glb and export/mm6_mfp_knife.glb with tools/install_model.py --world mm6. The installer writes accepted assets_source models and runtime copies; never copy exports directly into assets_dev. Merge the three staged descriptors.

Test mm6_mfp_peasantf3_codex_review2 on oute3.odm and 6d19.blv; summon 601/602/603. Standing height 177.099241 world units ±5%; tiers agree within .1. Scale 107.495710585, yaw −π/2, walk stride .9 m, Running stride 1.395 m. Ordinary speeds 200/220/240 and boosted running.

Attack retains the cut through .666667 s, ends 1.125 s; impact remains .65625 s for melee/ranged/cast. Check edge-leading contact, direct hand-at-side recovery and return to Standing, no slow tail. Noncasters alias cast to Attack. Knife visible during Attack only.

Inspect clean face, neck seam, midriff/arms, crisp sari and green/red/blue blouse tiers. Check larger shared atlas support, memory and performance on desktop/Android. Inspect four LOD/shadow switches at 700/550/220/88 px for seams, specular noise, mip bleeding.

All eight clips: Hit waist/skirt clearance, seated Attack grip, UnarmedRunForward2 arm swing with planted stride (no RelaxRunForward), upright rest, flat soles, visible walk lift, hands, braid/skirt, fall and held corpse. Check head look and disabled look during Death/Dead.

Run ordinary actor-registry, save/load, indoor/outdoor and unaffected-descriptor regressions. This session did not build/launch/install the game.
""")
notes=P/'integration/playbook_notes.md';text=notes.read_text().split('\n## Review round 2')[0]
notes.write_text(text+"""
## Review round 2

- Lit-sprite luminance pasted around cylinders encodes directional skin bands. Keep native pigment/mean and let mesh lighting supply highlights; explicitly distinguish this from historical albedo P90/P95 equality.
- Measure every UV island against surface area. Re-unwrapping at real 4K density fixes stretch; enlarging the old bitmap does not.
- Project each lower-LOD face to its matching source surface piece; keep all corners within one continuous UV island. Old lower-LOD UV layouts were not reliable correspondence.
- Denoise face pigment across UV seams in surface space. Exclude gold and preserve dark features; packed-UV blur mixes unrelated islands and creates patches.
- Derive repeat cloth from the selected HD costume reference and map it in physical units.
- Refresh skin normals after hole repairs; reload authoritative maps at export.
- Preserve the accepted cut/blow, shorten only recovery and verify the requested endpoint with the shared sampler.
""")
progress_path=P/'creature_3d_progress.json';progress=json.loads(progress_path.read_text())
progress.update(stage='review_round_2',status='complete',completed_utc=now,handoff='HANDOFF.md',deliverables=delivery,user_acceptance='pending',next_action={'owner':'orchestrator','action':'Install accepted exports via tools/install_model.py, merge unchanged numeric descriptors with revised timing header, run game checks and obtain artistic acceptance.'})
progress['checks']={'shared_gates':g['counts'],'bindings':'no BAD','viewer':'24/24, no errors','source_sha256':'240/240 plus 3 restored references','runtime_game':'Delegated to orchestrator'}
progress['known_tradeoffs']=['No reduction; retained LOD3 uses existing 13% cap.','Adaptive mesh sampling 24→48 Hz.','Larger 5152×4096 merged atlas; game memory/performance unverified.','Flat skin pigment does not reproduce lit native P90/P95; clean cheek/body means remain native-matched.','Game regression and artistic acceptance pending.']
progress['review_round_2']={'status':'complete','completed_utc':now,'attack_duration_s':1.125,'impact_s':.65625,'frames_at_48fps':54,'running':'UnarmedRunForward2 arms, planted gait','meshy_spend':0,'meshy_total':55,'credit_limit':100,'triangle_reduction':False,'actors_changed':'Header only; numeric events and bindings unchanged','gate_report':'review/round2/shared_gates/gates.json','review':'review/round2/README.md'}
write(progress_path,progress)
selected=set()
patterns=['scripts/prepare_review.py','scripts/export_levels.py','scripts/pack_runtime.py','scripts/merge_head_lods.py','scripts/bake_tiers.py','scripts/round1_running.py','textures/mfp_ramps.json','textures/runtime_ramps.json','review/reduction_soft/selection.json','references_hd/01_front.png','export/*.glb','export/*.blend','export/export_info.json','integration/*','scripts/round2*','review/round2/**/*.json','review/round2/**/*.md','review/round2/**/*.txt','review/round2/**/*.csv','review/round2/**/*.png','review/round2/lod_models/*.glb','review/sheets/*.png','review/viewer/*.glb','review/viewer/*.json','review/viewer/*.js','review/viewer/*.html','review/viewer/feedback/*.json','work/round2/textures/*.png','work/round2/lod?.blend','references_hd/round2_sari_tile.png']
for pattern in patterns:
 for f in P.glob(pattern):
  if f.is_file():selected.add(f)
for f in ['HANDOFF.md','README.md','creature_3d_progress.json','gates.json','review/README.md','review/GATES.md','review/final_metrics.json','review/runtime_audit.json','review/viewer_check.json','review/check_bindings.txt','source/native_inputs.json','source/clip_candidates.json','source/ANIMATION_STUDY.md']:selected.add(P/f)
write(P/'export/manifest.json',{'identity':'mm6:mfp','revision':'review_round_2','generated_utc':now,'runtime_files':delivery,'files':{str(f.relative_to(P)):record(f)for f in sorted(selected)}})
print('Round-2 handoff, records and hash manifest published')
