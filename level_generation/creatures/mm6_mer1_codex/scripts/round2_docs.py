# Publish current, hash-bound handoff from finished review evidence.
import json,hashlib,shutil,datetime
from pathlib import Path
P=Path(__file__).resolve().parents[1];O=P/'review/round2'
def read(p):return json.loads((P/p).read_text())
def dump(p,d):(P/p).write_text(json.dumps(d,indent=2)+'\n')
def ref(p):
 f=P/p;return {'path':p,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}
s=read('review/round2/summary.json');gates=read('review/gates/gates.json');artifacts=read('review/round2/artifacts.json')
state=read('creature_3d_progress.json');skin=read('review/round2/final_skin_luminance.json')['regions']
identity=read('review/runtime_geometry_identity.json');curves=read('review/round2/reduction_curve.json')['body']
filetable=['| File | Bytes | SHA-256 |','|---|---:|---|']+[f'| [{a["path"]}]({a["path"]}) | {a["bytes"]} | {a["sha256"]} |'for a in artifacts]
jobtable=['| Job | Id | Credits |','|---|---|---:|']
for k in ['body_round2_smart','body_round2_rig','body_round2_texture_v2','head_round2_texture_v2']:
 j=state['meshy']['jobs'][k];jobtable.append(f'| {k} | {j["task_id"]} | {j["consumed_credits"]} |')
skinrows=['| Region | Baked mean / p90 / p95 | Native mean / p90 / p95 |','|---|---|---|']
for n,d in skin.items():skinrows.append('| '+n+' | '+' / '.join(f'{d["baked"][k]:.6f}'for k in ['mean','p90','p95'])+' | '+' / '.join(f'{d["native"][k]:.6f}'for k in ['mean','p90','p95'])+' |')
curve=['| LOD | Body triangles | Actor px | Min IoU | Pooled IoU | Min SSIM |','|---|---:|---:|---:|---:|---:|']
for r in curves:curve.append(f'| {r["level"]} | {r["triangles"]} | {r["target_height_px"]} | {r["min_iou"]:.6f} | {r["pooled_iou"]:.6f} | {r["min_ssim"]:.6f} |')
url='http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html'
text=f"""# MM6 Merchant mer1 — handoff

## Review round 2 (regenerated body)

**QA HOLD — regenerated body staged; technical completion NOT achieved.**
Final shared verdict: **{gates['status']} — {gates['counts']['PASS']} PASS, {gates['counts']['FAIL']} FAIL,
{gates['counts']['UNVERIFIED']} UNVERIFIED**, {gates['counts']['INFO']} INFO and {gates['counts']['N/A']} N/A rows.
Counts include colour/shadow LOD rows and shared skeleton evidence, not distinct physical defects.
This revision is for review and further repair, not an accepted replacement. No artistic acceptance is recorded.

### Changes

- Five new body HD masters and five new head views were generated from native mer1, with prompts and receipts in
  [references_hd/round2](references_hd/round2/). The A-pose keeps open hands clear of the body, ordinary continuous
  set-in sleeves, green/gold tunic, blue collar, cap, belt/pouch, boots and stocky build. Shoulder caps and gold
  armhole strips were omitted so the new design is one garment.
- One fresh Meshy Smart Topology body, fresh auto-rig estimate, five-view body retexture and separate head retexture.
  The raw garment has **zero open shoulder/armpit boundary edges**, with a single torso/sleeve surface and no added
  arm-root wedges. [Topology](review/round2/raw_topology.json), [raw front/side/back](review/round2/raw_body_turnaround.jpg).
  Raw inspection shows no internal arm-root walls; this does not certify the remaining animated deformation faults.
- Fresh body geometry and weights were fitted to the retained source-frame rig, with new finger fitting and garment
  weights. No old torso/sleeve geometry was reused. Selected weights are the fresh Meshy transfer plus graph
  smoothing. Later weight, normal-transfer and surface-projection experiments were reverted after worsening checks
  or failing to resolve artifacts; [selection record](review/round2/continuous_shirt_weights.json).
- The accepted club GLB is byte-identical, and the **Club** node is preserved. A modeled belt loop supports it in
  Standing/Walking/Running/Fidget/Hit/Death/Dead. Attack draws it to the right hand and returns it.
  Draw/body and Death/body contact still fail, so this attachment animation is not certified.
- Running remains local Mixamo **Jogging**, 0.8 seconds and 1.302 m stride. **RelaxRunForward is not used.**
  The other owned-library choices remain: Standard Idle, ArmedWalk, Sword And Shield Slash, UnarmedGetHitF1,
  Standing Idle 03 Examine and Standing Death Forward 02. Dead holds the terminal fall; Cast aliases Attack.
- Hands were rebuilt with clean low-contrast skin, and the face uses a dedicated 1K texture input. All covered-texel
  mean/p90/p95 values meet native luminance floors. Artistic matching of the pale hands remains part of review.
- Death retains smoothed cloth rotation/location channels. Its configured cloth rotation-step rows pass, with worst
  step **{s['death_cloth_rotation_step_max_deg']:.3f} degrees/sample**. The shared runner has **no dedicated
  hem-vertex acceleration or shoulder-volume test**. These requested checks remain unverified; rotation-step passes
  do not establish hem-jitter clearance.

### Files and geometry

"""+'\n'.join(filetable)+f"""

| Component | Before round 2 LOD0/1/2/3 | Current LOD0/1/2/3 |
|---|---|---|
| Body | 9546 / 2420 / 2384 / 951 | **6989 / 2400 / 1730 / 685** |
| Club | 1122 / 290 / 252 / 200 | **1122 / 290 / 252 / 200**, byte-identical |

The unreduced new production body is 15,942 triangles; the candidate removes 56.16%.
Body ratios: 1 / 0.3434 / 0.2475 / 0.0980. The retained club's LOD3 ratio is 0.1783; the shared configuration keeps
its inherited 0.18 allowance, while [export identity](review/runtime_geometry_identity.json) separately asserts
body LOD3 <= 0.10. Combined LOD3 ratio is 0.1091. All counts are below the previous installed body counts.
Final primitive weight sums differ from one by at most **{identity['max_weight_sum_error']:.3g}**.
Selected/runtime geometry and skin identity pass; this is not a deformation-quality pass.

One usable rebake at 6,989 triangles supplies all body LODs. Body 2048² and head 1024² inputs combine to one
**3104×2048 atlas, four image/texture resources**, shared across all LODs and three tiers. Island gaps are
34.816 px (body) and 33.792 px (head), with >=16 px dilated margins. The first zero-coverage UV bake was rejected
and preserved in work/round2/invalid_blank_bake; it is not a usable bake. No per-LOD texture sets.
[Atlas receipt](review/round2/shared_atlas.json), [coverage](work/round2/shared_textures/projection_coverage.json).

Eight views in all three palettes were compared at the stated projected sizes:

"""+'\n'.join(curve)+"""

These are fixed candidates, **not an accepted passing reduction curve**. Visible cap/torso faceting or projection
artifacts and failed near textured SSIM remain open; no perceptual exception is claimed.
[Reduction evidence](review/round2/reduction/README.md), [all measurements](review/round2/reduction_curve.json),
[LOD0 side-by-side](review/round2/reduction/body_lod0_comparison.jpg), [candidate plot](review/round2/reduction/curve.png).

Covered UV texels only; dilated padding is excluded from skin measurements:

"""+'\n'.join(skinrows)+f"""

[Skin report](review/round2/final_skin_luminance.json). One shared map serves every LOD.

### Verification and unresolved faults

- check_bindings.py: **exit 0, no BAD line**; [receipt](review/bindings_check.txt).
- Shared viewer checker: **24/24 tier/clip switches**, no console errors or failed switches; checker closed its browser.
  [Current-hash receipt](review/round2/viewer_check.json), [viewer]({url}).
- Shared runner covers all eight clips and colour/shadow LODs at 48 Hz. Its final input hashes are in
  [gates.json](review/gates/gates.json), with [readable report](review/gates/gates.md) and
  [open rows](review/round2/open_findings.json). No new gate implementation was added.
- Kinematic/source-angle or rotation-step passes do not override surface, grip or reduction failures.
  [Locomotion measurements](review/round2/locomotion_measurements.json) record lowest soles, walking lift and
  running contact/flight across clips and LODs.

"""+(O/'fault_table.md').read_text()+"""

Final visual inspection confirms large folds/self-intersections at the armpits and waist in Attack/Death, plus
cap/neck artifacts. The zero-boundary raw mesh did not by itself produce a correct bound/exported garment.
Recheck fitting of the fresh A-pose to the retained rest joints before further weight smoothing or reduction.

Priorities before acceptance: continuous-sleeve deformation with raised/bent arms; reduced-surface shading and
texture projection; robe/boot containment through Death; actual-mesh club draw and belt contact; grip fitting
and finger preservation at far LODs; LOD3 sole geometry. Keep complete closed leg geometry; do not delete hidden
faces or loosen thresholds to conceal these faults. Shared tooling also needs shoulder-volume and hem-vertex
jitter coverage before those requested checks can be certified.

### Review sheets

[Final front/side/back](review/round2/body_turnaround.jpg),
[rest/Attack/Death shoulders](review/round2/shoulder_closeups.jpg),
[hands](review/round2/hands_closeups.jpg).
Eight sheets live in review/round2/clip_Standing.jpg, clip_Walking.jpg, clip_Running.jpg, clip_Attack.jpg,
clip_Hit.jpg, clip_Fidget.jpg, clip_Death.jpg and clip_Dead.jpg. Each contains front, side and three-quarter rows.
Individual frames and full-resolution close-ups remain beside them. Root review/clip_*.jpg sheets are refreshed.

### Integration and reproduction

**integration/actors.yml changed:** scale 103.841591817 -> **103.944653064**, z_offset -> **-0.103944653**,
calibrated to native height 177.099241 game units. Stride 0.84 m, running multiplier 1.55, impact 0.8125 s,
yaw -1.570796327, ids 577/578/579, Cast alias, skins and Club node remain compatible.
[Staged YAML](integration/actors.yml), [integration case](integration/regression.md).

The sprite-restore project stayed read-only. No assets_dev/assets_source installation, game launch, build or commit.
The orchestrator owns eventual installation and game verification after this hold is resolved.

Authoritative source: work/round2/master.blend.
Selected geometry: work/round2/body_lod0..3.blend and review/reduction/selection.json.
Maps: work/round2/shared_textures/.
Assembly order: export_selected.py (Blender), round2_package.py, round2_viewer.py, export_identity.py;
then round2_review_and_gates.py (Blender), round2_records.py and round2_docs.py.
Use the workspace wrapper and Blender --threads 4.
round2_refresh.py, round2_shirt_weights.py, round2_normals.py, round2_transfer_normals.py and
round2_project_shape.py are rejected experiments, not the selected assembly path.
Export files outside the six listed above are intermediate assembly outputs.

### Credits

**Round 2 spent: 30. Project total: 60 / 100. Remaining: 40.**

"""+'\n'.join(jobtable)+"""

Two meshy-7.1 retexture submissions were rejected with HTTP 400 and zero credits; corrected meshy-7 jobs succeeded.
No paid animation jobs were submitted. Payloads, download hashes and receipts are in creature_3d_progress.json
and meshy/. No paid jobs are pending.

### Review round 1 history

The rejected shoulder patches were replaced by complete body regeneration. The old handoff is preserved as
[HANDOFF_round1.md](work/round2/HANDOFF_round1.md); its hashes/counts are historical.
Lease release follows final record verification as the last batch operation.
"""
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text(f"""# MM6 Merchant (mer1)

**Review round 2: regenerated body staged; QA HOLD.** Technical completion is false.
Shared gates: {gates['counts']['FAIL']} FAIL and {gates['counts']['UNVERIFIED']} UNVERIFIED rows.
[HANDOFF.md](HANDOFF.md) lists current hashes, changes, evidence and unresolved defects.

Five fresh body masters and five head views are in [references_hd/round2](references_hd/round2/).
A new Smart Topology body replaces all patched torso/sleeve geometry. Raw shoulders have zero boundary edges;
torso and set-in sleeves are one surface. Gold trim remains at collar/cuffs/hem. Armhole trim was omitted to
avoid the rejected separate-tube construction. The original club and Club node remain, with belt carry and
Attack draw. Running uses Jogging; RelaxRunForward is rejected. Clean hand maps and a 1K head set were rebuilt.
Death/Dead use smoothed library cloth motion, but the available shared runner cannot certify hem-vertex jitter.

Body LODs: **6989 / 2400 / 1730 / 685**. Club: **1122 / 290 / 252 / 200**, byte-identical.
One usable shared rebake with >=16 px margins; the first collapsed-UV bake was rejected.
Later weight/shading experiments were reverted. Fresh Meshy transfer plus graph smoothing is selected.
The animated export still has visibly broken cloth at the armpits and waist.
Cloth, stretch, grip and reduced-image-quality faults prevent acceptance; the 7k candidate is not a pass.

[Turnaround](review/round2/body_turnaround.jpg), [shoulders](review/round2/shoulder_closeups.jpg),
[clip sheets](review/round2/), [reduction evidence](review/round2/reduction/README.md),
[shared gates](review/gates/gates.md), [viewer]({url}).
Viewer: 24/24 switches; bindings: no BAD line. These checks do not clear deformation failures.

Authoritative source: work/round2/master.blend and work/round2/body_lod0..3.blend.
Selection/maps: review/reduction/selection.json and work/round2/shared_textures/.
Deliverables: export/mm6_mer1.glb, mm6_mer1_club.glb, mm6_mer1.blend and mm6_mer1_portable_a/b/c.glb.
Use HANDOFF.md's assembly path; rejected experimental scripts are excluded.
The staged actors.yml changes scale/z_offset; stride, impact and attachment scheme remain compatible.

**Budget: 30 credits this round; 60/100 total; 40 remaining.** No pending paid jobs.
Unattended choices and failed checks are recorded without claiming acceptance.
Native mm6_mer1 remained read-only. No installation, game launches, builds or commits.
The orchestrator handles integration after repairs.
""")
(P/'integration/regression.md').write_text("""# Proposed integration case — QA HOLD

Resolve HANDOFF.md's failures before installing this revision as accepted.
The orchestrator installs final project GLBs using tools/install_model.py and merges the staged descriptors.

- Case: mm6-mer1-codex; MM6 oute3.odm, then a normal MM6 BLV.
- Summon 577 / 578 / 579. Native visible height 177.099241 game units; broad size bounds 140–220.
- Proposed scale 103.944653064, z_offset -0.103944653, yaw -1.570796327.
- Exercise all eight clips; Cast aliases Attack. Inspect both shoulders, raised Attack arms and Death.
- Club stays hung from its belt loop in Standing/Walking/Running/Fidget/Hit/Death/Dead; draws/returns in Attack.
- Inspect loop contact and clipping during draw/fall; these contacts currently have shared failures.
- Check Jogging at .8 seconds / 1.302 m stride, walking .84 m, and LOD switches at 550/220/88 projected bound pixels.
- Check hand skin against face/native, three palettes, reduced head/cloth texture quality and frame-by-frame hem motion.
- Verify impact .8125 s, look controls, shadows, save/load and attachments; run shared MM6 regression and indoor/outdoor tour.

This batch session performed no runtime install, build, game launch, scenario or game capture.
""")
notes=P/'integration/playbook_notes.md'
notes.write_text("""# Production notes — current round 2 supersedes earlier repair guidance

- Native mer1 carries a club at its belt and draws for Attack. Keep the original modeled/textured club and Club node.
- Generate one continuous set-in-sleeve A-pose. Caps and gold armhole rings encouraged the rejected tube construction.
- Raw shoulder boundary count zero cannot certify deformation; inspect actual exported Attack and Death.
- Fresh Meshy weights need a careful fit to the retained source-frame skeleton. Graph smoothing alone did not clear stretch gates.
- Broad coordinate weight fields pulled the belly with the arms or left forearms influenced by the torso. These trials were reverted.
- The authoritative fresh body remains in work/round2/master.blend; no previous torso or sleeve geometry was retained.
- Preserve the anatomical source-frame hinge and distribute forearm roll. Jogging replaces RelaxRunForward permanently.
- The running multiplier is 1.55: walking .84 m requires a planted run stride of 1.302 m.
- Keep complete closed legs under the tunic; Death still needs actual robe/boot containment work.
- Validate UV area and bake coverage. The first Smart UV margin pack collapsed and produced empty maps; it was rejected.
- The usable bake has body 2K / head 1K, >33 px island gaps and >=16 px dilated borders, shared by every LOD.
- Combining unequal head/body sizes needs an explicit head region mask. Final atlas: 3104x2048, four shared textures.
- Exclude padding when comparing skin luminance to native sprites.
- Silhouette alone missed cap/torso faceting or projection defects at ~7k; textured SSIM failed. No perceptual exception is justified.
- Actual-mesh club/hand contacts still fail. Cylindrical proxies are insufficient, especially after far-LOD finger reduction.
- Shared cloth aliases cover rotation steps, not hem-vertex acceleration or shoulder volume. Those requested checks remain unverified.
- Current shared reports and hashes in review/round2 supersede historical custom reports and reduction curves.
- No integration was performed. The orchestrator must resolve the QA hold before accepting/installing this revision.
""")
shutil.copyfile(P/'creature_3d_progress.json',P/'work/round2/progress_before_handoff.json')
state.update(stage='handoff',status='qa_hold',current_stage='review_round_2',current_substep='regenerated body staged; shared and visual gates fail',substep='qa_hold',technical_completion=False,last_updated=s['generated_at'],selected_artifacts=artifacts,handoff='HANDOFF.md',next_action='Orchestrator: inspect round-2 evidence and repair exact deformation/contact/LOD faults before acceptance or installation.',user_acceptance='round-1 shoulder patches rejected; regenerated round-2 body not accepted')
state.setdefault('references_hd_historical',state['references_hd']);state.setdefault('references_head_historical',state['references_head'])
state['references_hd']=[ref(f'references_hd/round2/{n}.png')for n in ['00_three_quarter','01_front','02_back','03_left','04_right']]
state['references_head']=[ref(f'references_hd/round2/head/{n}.png')for n in ['00_three_quarter','01_front','02_back','03_left','04_right']]
state['review_round_2'].update(s,finished_at=s['generated_at'],handoff='HANDOFF.md',artifacts=artifacts,review_sheets='review/round2/',integration_actors_changed=True)
state['rig_gate_checkpoint']={'blend':'work/round2/master.blend','shared_gate_report':'review/gates/gates.json','shared_gate_status':gates['status'],'open_findings':'review/round2/open_findings.json','runtime_geometry_identity':'review/runtime_geometry_identity.json','note':'All clips/LODs sampled; deformation/contact fails. Shared runner has no shoulder-volume or hem-vertex acceleration check.'}
state['texture_checkpoint']={'skin_report':'review/round2/final_skin_luminance.json','all_skin_mean_p90_p95_not_darker':all(x['not_darker']for x in skin.values()),'shared_atlases':'review/round2/shared_atlas.json','meshy_credits':60,'numeric_visual_curve':'review/round2/reduction_curve.json','note':'One usable shared rebake; textured reduction quality remains on hold.'}
dump('creature_3d_progress.json',state)
print('HANDOFF, README, integration notes and progress updated; QA HOLD remains.')
